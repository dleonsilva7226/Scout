#!/usr/bin/env python3
"""
End-to-end test script for Google Sheets integration.
Tests the full pipeline: fetch → extract → log to Google Sheets

Usage:
    python test_sheets_e2e.py "https://example.com/job/123"
    python test_sheets_e2e.py "https://example.com/job/123" --dry-run  # Skip actual sheet write
"""
import sys
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scout.agent.job_agent import run_scout_agent
from scout.tools.tracker import get_worksheet
from scout.config import validate_config

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_sheets_e2e.py <job_url>")
        print("  python test_sheets_e2e.py <job_url> --dry-run  # Skip Google Sheets write")
        print("\nExample:")
        print("  python test_sheets_e2e.py https://example.com/job/123")
        sys.exit(1)
    
    url = sys.argv[1]
    dry_run = "--dry-run" in sys.argv or "-d" in sys.argv
    
    try:
        # Validate configuration
        print("🔍 Validating configuration...")
        validate_config()
        print("✅ Configuration valid\n")
        
        # Get worksheet (this will authenticate with Google Sheets)
        worksheet = None
        if not dry_run:
            print("🔐 Authenticating with Google Sheets...")
            try:
                worksheet = get_worksheet()
                print("✅ Successfully authenticated with Google Sheets\n")
            except Exception as e:
                print(f"❌ Failed to authenticate with Google Sheets: {e}")
                print("\n💡 Make sure you've run: python scripts/sheets_oauth_bootstrap.py")
                sys.exit(1)
        else:
            print("🧪 DRY RUN MODE: Skipping Google Sheets authentication\n")
        
        # Run the full pipeline
        print(f"🚀 Starting end-to-end pipeline for: {url}\n")
        print("-" * 60)
        
        job_info = run_scout_agent(url, worksheet)
        
        print("-" * 60)
        print("\n✅ Pipeline completed successfully!\n")
        
        # Print summary
        print("=" * 60)
        print("EXTRACTED JOB INFORMATION")
        print("=" * 60)
        print(f"Company:      {job_info.company}")
        print(f"Title:        {job_info.title}")
        print(f"Location:     {job_info.location}")
        print(f"URL:          {job_info.url}")
        
        if job_info.salary:
            print(f"Salary:       {job_info.salary}")
        if job_info.contact_person:
            print(f"Contact:      {job_info.contact_person}")
        if job_info.level:
            print(f"Level:        {job_info.level.value}")
        if job_info.remote_type:
            print(f"Remote Type:  {job_info.remote_type.value}")
        if job_info.ats:
            print(f"ATS:          {job_info.ats.value}")
        
        if job_info.date_applied:
            print(f"Date Applied: {job_info.date_applied}")
        if job_info.status:
            print(f"Status:       {job_info.status}")
        
        print("=" * 60)
        
        if dry_run:
            print("\n🧪 DRY RUN: Job was NOT written to Google Sheets")
        else:
            from scout.config import GOOGLE_SPREADSHEET_ID
            print("\n✅ Job successfully logged to Google Sheets!")
            print(f"   Check your spreadsheet: https://docs.google.com/spreadsheets/d/{GOOGLE_SPREADSHEET_ID}")
        
        print()
        
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

