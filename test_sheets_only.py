#!/usr/bin/env python3
"""
Test script for Google Sheets integration only.
Creates a test job and logs it to Google Sheets.

Usage:
    python test_sheets_only.py
"""
import sys
import logging
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scout.models import JobInfo, JobLevel, RemoteType, AtsType
from scout.tools.tracker import get_worksheet, log_job_to_sheet
from scout.config import GOOGLE_SPREADSHEET_ID

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    try:
        print("🔐 Authenticating with Google Sheets...")
        worksheet = get_worksheet()
        print("✅ Successfully authenticated\n")
        
        # Create a test job
        test_job = JobInfo(
            company="Test Company Inc",
            contact_person="Jane Doe",
            title="Senior Software Engineer",
            location="San Francisco, CA",
            salary="$150,000 - $200,000",
            url="https://example.com/job/test-123",
            date_applied=None,  # Will be auto-populated to today
            date_confirmation=None,
            date_latest_reply=None,
            status=None,  # Will be auto-populated to "to_apply"
            reason_outcome=None,
            level=JobLevel.SENIOR,
            remote_type=RemoteType.HYBRID,
            ats=AtsType.GREENHOUSE,
        )
        
        print("📝 Test Job Information:")
        print("-" * 60)
        print(f"Company:      {test_job.company}")
        print(f"Title:        {test_job.title}")
        print(f"Location:     {test_job.location}")
        print(f"Salary:       {test_job.salary}")
        print(f"Level:        {test_job.level.value}")
        print(f"Remote Type:  {test_job.remote_type.value}")
        print(f"ATS:          {test_job.ats.value}")
        print("-" * 60)
        
        print("\n📤 Logging to Google Sheets...")
        log_job_to_sheet(test_job, worksheet)
        
        print("\n✅ Successfully logged test job to Google Sheets!")
        print(f"   Check your spreadsheet: https://docs.google.com/spreadsheets/d/{GOOGLE_SPREADSHEET_ID}")
        print("\n💡 You can delete this test row from your spreadsheet if needed.")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

