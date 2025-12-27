"""Main agent orchestration for job extraction pipeline"""
import logging
from scout.models import JobInfo
from scout.tools.fetcher import fetch_job_page
from scout.tools.extractor import extract_job_info
from scout.tools.tracker import log_job_to_sheet

logger = logging.getLogger(__name__)


def run_scout_agent(url: str, worksheet) -> JobInfo:
    """
    Full pipeline:
      - fetch_job_page(url)
      - extract_job_info(text)
      - log_job_to_sheet(job, worksheet)
      - return JobInfo
    
    Args:
        url: Job posting URL
        worksheet: Google Sheets worksheet object
        
    Returns:
        JobInfo model instance
        
    Raises:
        RuntimeError: If any step in the pipeline fails
    """
    try:
        # Step 1: Fetch the job page
        logger.info(f"Fetching job page: {url}")
        html_content = fetch_job_page(url)
        
        # Step 2: Extract job information
        logger.info("Extracting job information...")
        job_info = extract_job_info(html_content, url=url)
        
        # Step 3: Log to Google Sheets (if worksheet provided)
        if worksheet is not None:
            logger.info("Logging job to Google Sheets...")
            log_job_to_sheet(job_info, worksheet)
        else:
            logger.warning("No worksheet provided, skipping Google Sheets logging")
        
        logger.info(f"Successfully processed job: {job_info.company} - {job_info.title}")
        return job_info
        
    except Exception as e:
        logger.error(f"Pipeline failed for URL {url}: {e}")
        raise RuntimeError(f"Job extraction pipeline failed: {e}") from e
