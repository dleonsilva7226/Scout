"""Google Sheets integration for logging job applications"""
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from scout.config import GOOGLE_SPREADSHEET_ID, GOOGLE_SHEET_ID
from scout.models import JobInfo

logger = logging.getLogger(__name__)

# Google Sheets API scopes
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# Rate limiting constants
MAX_RETRIES = 3
INITIAL_RETRY_DELAY = 1  # seconds
MAX_RETRY_DELAY = 60  # seconds
RATE_LIMIT_DELAY = 2  # seconds between requests to avoid hitting quotas


def get_authenticated_service() -> Any:
    """
    Get authenticated Google Sheets API service using OAuth token.
    
    Returns:
        Google Sheets API service object
        
    Raises:
        FileNotFoundError: If token file doesn't exist
        ValueError: If authentication fails
    """
    token_path = Path("secrets/google_token.json")
    creds_path = Path("secrets/google_oauth_client.json")
    
    if not token_path.exists():
        raise FileNotFoundError(
            f"OAuth token not found at {token_path}. "
            "Run scripts/sheets_oauth_bootstrap.py to authenticate."
        )
    
    creds = None
    try:
        # Load existing token
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
        
        # Refresh token if expired
        if creds and creds.expired and creds.refresh_token:
            logger.info("Refreshing expired OAuth token...")
            creds.refresh(Request())
            # Save refreshed token
            token_path.write_text(creds.to_json())
            logger.info("Token refreshed and saved")
    except Exception as e:
        logger.error(f"Error loading credentials: {e}")
        # If token is invalid, try to re-authenticate
        if creds_path.exists():
            logger.info("Attempting to re-authenticate...")
            flow = InstalledAppFlow.from_client_secrets_file(str(creds_path), SCOPES)
            creds = flow.run_local_server(port=0)
            token_path.write_text(creds.to_json())
            logger.info("Re-authentication successful")
        else:
            raise ValueError(
                f"Authentication failed and client secrets not found at {creds_path}. "
                "Please ensure OAuth setup is complete."
            ) from e
    
    if not creds or not creds.valid:
        raise ValueError("Failed to obtain valid credentials")
    
    # Build and return the service
    try:
        service = build("sheets", "v4", credentials=creds)
        return service
    except Exception as e:
        raise ValueError(f"Failed to build Google Sheets service: {e}") from e


def get_worksheet(
    service: Any | None = None,
    spreadsheet_id: str | None = None,
    sheet_id: int | str | None = None
) -> Any:
    """
    Get a worksheet object for the specified spreadsheet and sheet.
    
    Args:
        service: Authenticated Google Sheets API service. If None, creates one.
        spreadsheet_id: The ID of the Google Spreadsheet. If None, uses config default.
        sheet_id: Optional sheet ID (gid). If None, uses config default or first sheet.
        
    Returns:
        Worksheet object with append_row method
    """
    # Use defaults from config if not provided
    if service is None:
        service = get_authenticated_service()
    if spreadsheet_id is None:
        if not GOOGLE_SPREADSHEET_ID:
            raise ValueError(
                "GOOGLE_SPREADSHEET_ID not set. "
                "Set it in your .env file or pass spreadsheet_id parameter."
            )
        spreadsheet_id = GOOGLE_SPREADSHEET_ID
    if sheet_id is None:
        sheet_id = int(GOOGLE_SHEET_ID) if GOOGLE_SHEET_ID else None
    elif isinstance(sheet_id, str):
        sheet_id = int(sheet_id)
    class Worksheet:
        def __init__(self, service: Any, spreadsheet_id: str, sheet_id: int | None):
            self.service = service
            self.spreadsheet_id = spreadsheet_id
            self.sheet_id = sheet_id
            self._sheet_name: str | None = None  # Cache sheet name
            
        def _get_sheet_name(self) -> str:
            """Get the sheet name, caching it to avoid repeated API calls."""
            if self._sheet_name is not None:
                return self._sheet_name
                
            try:
                spreadsheet = self.service.spreadsheets().get(
                    spreadsheetId=self.spreadsheet_id
                ).execute()
                
                if self.sheet_id is not None:
                    # Find sheet by ID
                    for sheet in spreadsheet.get("sheets", []):
                        if sheet["properties"]["sheetId"] == self.sheet_id:
                            self._sheet_name = sheet["properties"]["title"]
                            break
                    if not self._sheet_name:
                        raise ValueError(f"Sheet with ID {self.sheet_id} not found")
                else:
                    # Use first sheet
                    first_sheet = spreadsheet.get("sheets", [{}])[0]
                    self._sheet_name = first_sheet.get("properties", {}).get("title", "Sheet1")
                
                return self._sheet_name
            except HttpError as e:
                raise ValueError(f"Failed to get sheet name: {e}") from e
            
        def append_row(self, values: list[Any], value_input_option: str = "RAW") -> None:
            """
            Append a row to the worksheet.
            
            Args:
                values: List of values to append
                value_input_option: How to interpret values ("RAW" or "USER_ENTERED")
            """
            # Get sheet name (cached after first call)
            try:
                sheet_name = self._get_sheet_name()
                # Use column A to identify the sheet - API will append to next available row
                range_name = f"{sheet_name}!A:A"
            except Exception as e:
                # Fallback to generic range if we can't get sheet name
                logger.warning(f"Could not get sheet name, using default: {e}")
                range_name = "A:A"
            
            # Append the row with rate limiting and retry logic
            _append_with_retry(
                self.service,
                self.spreadsheet_id,
                range_name,
                values,
                value_input_option
            )
    
    return Worksheet(service, spreadsheet_id, sheet_id)


def _append_with_retry(
    service: Any,
    spreadsheet_id: str,
    range_name: str,
    values: list[Any],
    value_input_option: str,
    retry_count: int = 0
) -> None:
    """
    Append a row with exponential backoff retry logic for rate limiting and errors.
    
    Args:
        service: Google Sheets API service
        spreadsheet_id: Spreadsheet ID
        range_name: Range to append to (e.g., "Sheet1!A:A")
        values: Values to append
        value_input_option: How to interpret values
        retry_count: Current retry attempt
        
    Raises:
        HttpError: If all retries fail
    """
    try:
        # Add rate limiting delay
        if retry_count > 0:
            delay = min(INITIAL_RETRY_DELAY * (2 ** (retry_count - 1)), MAX_RETRY_DELAY)
            logger.warning(f"Rate limit hit, waiting {delay}s before retry {retry_count}/{MAX_RETRIES}")
            time.sleep(delay)
        else:
            time.sleep(RATE_LIMIT_DELAY)  # Small delay to avoid hitting quotas
        
        body = {"values": [values]}
        result = service.spreadsheets().values().append(
            spreadsheetId=spreadsheet_id,
            range=range_name,
            valueInputOption=value_input_option,
            insertDataOption="INSERT_ROWS",
            body=body
        ).execute()
        
        logger.debug(f"Successfully appended row to {range_name}")
        return result
        
    except HttpError as error:
        error_code = error.resp.status if hasattr(error, 'resp') else None
        
        # Handle rate limiting (429) and quota errors (403)
        if error_code in [429, 403]:
            if retry_count < MAX_RETRIES:
                logger.warning(f"Rate limit/quota error ({error_code}), retrying...")
                return _append_with_retry(
                    service, spreadsheet_id, range_name, values,
                    value_input_option, retry_count + 1
                )
            else:
                logger.error(f"Max retries reached for rate limit error: {error}")
                raise RuntimeError(
                    f"Google Sheets API rate limit exceeded after {MAX_RETRIES} retries. "
                    "Please wait and try again later."
                ) from error
        
        # Handle other HTTP errors
        elif error_code == 401:
            raise ValueError(
                "Authentication failed. Please re-run scripts/sheets_oauth_bootstrap.py"
            ) from error
        elif error_code == 404:
            raise ValueError(
                f"Spreadsheet or sheet not found. Check spreadsheet_id and sheet_id."
            ) from error
        else:
            logger.error(f"Google Sheets API error ({error_code}): {error}")
            raise RuntimeError(f"Failed to append row to Google Sheets: {error}") from error
    
    except Exception as e:
        logger.error(f"Unexpected error appending to Google Sheets: {e}")
        if retry_count < MAX_RETRIES:
            return _append_with_retry(
                service, spreadsheet_id, range_name, values,
                value_input_option, retry_count + 1
            )
        raise RuntimeError(f"Failed to append row after {MAX_RETRIES} retries: {e}") from e


def log_job_to_sheet(job: JobInfo, worksheet) -> None:
    """
    Append a row to Google Sheets based on the JobInfo fields,
    matching the column order in the Tracker sheet.
    
    Auto-populates application tracking fields with sensible defaults:
    - date_applied: Set to today's date (YYYY-MM-DD) if not already set
    - status: Set to "To Apply" if not already set
    - Other tracking fields (date_confirmation, date_latest_reply, reason_outcome) 
      remain empty for manual update later
    
    Column order (matching spreadsheet):
    1. company
    2. contact_person
    3. title
    4. location
    5. salary
    6. url
    7. date_applied
    8. date_confirmation
    9. date_latest_reply
    10. status
    11. reason_outcome
    12. level
    13. remote_type
    14. ats
    
    Args:
        job: JobInfo model instance
        worksheet: Google Sheets worksheet object with append_row method
        
    Raises:
        RuntimeError: If appending to sheet fails
    """
    try:
        # Auto-populate application tracking fields with defaults if not set
        today = datetime.now().strftime("%Y-%m-%d")
        date_applied = job.date_applied or today
        # Status must match spreadsheet dropdown: "to_apply" (lowercase with underscore)
        status = job.status or "to_apply"
        # ATS defaults to "unknown" if not detected
        ats_value = job.ats.value if job.ats else "unknown"
        
        # Convert JobInfo to row values in exact column order
        # Note: level, remote_type, and ats use enum values which should match spreadsheet
        row_values = [
            job.company or "",
            job.contact_person or "",
            job.title or "",
            job.location or "",
            job.salary or "",
            job.url or "",
            date_applied,  # Auto-populated if not set
            job.date_confirmation or "",  # Empty - to be filled when confirmed
            job.date_latest_reply or "",  # Empty - to be filled when reply received
            status,  # Auto-populated if not set (must be "to_apply" format)
            job.reason_outcome or "",  # Empty - to be filled when outcome known
            job.level.value if job.level else "",  # Enum value (intern, entry, mid, etc.)
            job.remote_type.value if job.remote_type else "",  # Enum value (on_site, remote, etc.)
            ats_value,  # Enum value (greenhouse, lever, etc.) or "unknown" as default
        ]
        
        # Append the row
        worksheet.append_row(row_values, value_input_option="USER_ENTERED")
        logger.info(f"Successfully logged job to sheet: {job.company} - {job.title}")
        
    except Exception as e:
        logger.error(f"Failed to log job to sheet: {e}")
        raise RuntimeError(f"Failed to log job to Google Sheets: {e}") from e
