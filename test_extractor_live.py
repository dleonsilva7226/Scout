#!/usr/bin/env python3
"""
Simple script to test the job extractor with real data.
Usage:
    python test_extractor_live.py "https://example.com/job/123"  # From URL
    python test_extractor_live.py --text "Job posting text here"  # From text
"""
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from scout.tools.extractor import extract_job_info
from scout.tools.fetcher import fetch_job_page


def print_job_info(job_info):
    """Pretty print job information"""
    print("\n" + "="*60)
    print("EXTRACTED JOB INFORMATION")
    print("="*60)
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
    
    print("\n" + "-"*60)
    print("Full JSON Output:")
    print("-"*60)
    print(json.dumps(job_info.model_dump(), indent=2, default=str))
    print("="*60 + "\n")


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python test_extractor_live.py <url>")
        print("  python test_extractor_live.py --text \"Job posting text here\"")
        print("\nExample:")
        print("  python test_extractor_live.py https://example.com/job/123")
        sys.exit(1)
    
    try:
        if sys.argv[1] == "--text" or sys.argv[1] == "-t":
            # Extract from text
            if len(sys.argv) < 3:
                print("Error: --text requires job posting text")
                sys.exit(1)
            
            text = sys.argv[2]
            print(f"Extracting from text ({len(text)} characters)...")
            job_info = extract_job_info(text, url="test-url")
            
        elif sys.argv[1].startswith("http"):
            # Extract from URL
            url = sys.argv[1]
            print(f"Fetching job page from: {url}")
            html = fetch_job_page(url)
            print(f"Fetched {len(html)} characters of HTML")
            print("Extracting job information...")
            job_info = extract_job_info(html, url=url)
            
        else:
            # Treat as text
            text = sys.argv[1]
            print(f"Extracting from text ({len(text)} characters)...")
            job_info = extract_job_info(text, url="test-url")
        
        print_job_info(job_info)
        
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

