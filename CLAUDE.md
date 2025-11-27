# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Scout is an AI-powered job posting extraction tool that parses job URLs and logs structured data to Google Sheets. It uses LlamaIndex for agent orchestration and structured output extraction.

The system follows a three-stage pipeline:
1. `fetch_job_page(url)` - Retrieves and cleans HTML from job posting URLs
2. `extract_job_info(text)` - Uses LlamaIndex structured output program to extract JobInfo from cleaned text
3. `log_job_to_sheet(job, worksheet)` - Appends extracted data to Google Sheets

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment, install dependencies
./scripts/install.sh

# Manual activation
source .venv/bin/activate
```

### Testing
```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_extractor.py

# Run tests locally matching CI environment
./scripts/run_ci_locally.sh
```

### Running the Application
```bash
# Basic usage (as designed)
python main.py "https://careers.company.com/job/12345"
```

## Project Structure

```
src/scout/
├── agent/
│   └── job_agent.py          # Main agent orchestration
├── tools/
│   ├── fetcher.py            # HTTP fetching and HTML cleaning
│   ├── extractor.py          # LlamaIndex structured extraction
│   └── tracker.py            # Google Sheets integration
├── utils/
│   └── text_cleaning.py      # Text preprocessing utilities
├── models.py                 # Pydantic JobInfo model + enums
├── config.py                 # Configuration (currently minimal)
└── cli.py                    # CLI entry point

tests/
├── test_extractor.py         # Tests LlamaIndex program integration
├── test_fetcher.py           # Tests HTTP and HTML parsing
├── test_models.py            # Tests Pydantic model validation
└── test_tracker.py           # Tests Google Sheets row formatting
```

## Architecture Notes

### Data Model (JobInfo)
The `JobInfo` Pydantic model in `models.py` represents the schema for extracted job data. All fields must match the column order expected by the Google Sheet tracker. The test in `test_tracker.py:33` validates this column ordering is maintained.

Fields include: company, contact_person, title, location, salary, url, date_applied, date_confirmation, date_latest_reply, status, reason_outcome, plus enum fields (level, remote_type, ats).

### Extraction Pipeline
`extractor.py` uses LlamaIndex's structured output program to convert raw job posting text into a `JobInfo` instance. The `get_job_info_program()` function builds the extraction program, which is then called with cleaned text.

### Google Sheets Integration
`tracker.py` handles appending rows to Google Sheets. The column order in `log_job_to_sheet()` must exactly match the sheet's column structure. Empty/None optional fields are converted to empty strings.

### Environment Variables
`.env` contains `OLLAMA_API_KEY` for LlamaIndex/Ollama integration. This is referenced in commented code in `src/scout/__init__.py` but the active implementation may use OpenAI or another provider.

## Dependencies

Core dependencies (from `requirements.txt`):
- `llama-index==0.14.8` - Agent orchestration and structured extraction
- `ollama==0.6.1` - LLM provider interface
- `python-dotenv==1.2.1` - Environment variable management
- `pytest==9.0.1` - Testing framework

Additional implicit dependencies (installed as part of llama-index):
- Google Sheets API client (gspread or similar)
- BeautifulSoup/lxml for HTML parsing
- httpx/requests for HTTP fetching

## CI/CD

GitHub Actions runs on all pushes and PRs to main:
1. Python 3.12 environment
2. Installs dependencies from requirements.txt + pytest
3. Runs `pytest`

Use `./scripts/run_ci_locally.sh` to replicate CI behavior locally.

## Testing Patterns

Tests use monkeypatching to mock external dependencies:
- `test_extractor.py` patches `get_job_info_program()` to avoid LlamaIndex API calls
- `test_tracker.py` uses `FakeWorksheet` class to verify row append calls without touching Google Sheets API
- Tests verify both data transformation logic and integration contracts

## Important Constraints

1. **Column Order**: The order of fields written to Google Sheets in `log_job_to_sheet()` must exactly match the tracker spreadsheet's columns. Any changes require updating both code and sheet.

2. **Enum Values**: JobLevel, RemoteType, and AtsType enums must align with Google Sheet dropdown validation options.

3. **No Auto-Submit**: Scout only extracts and logs job data; it never submits applications automatically (per README philosophy).