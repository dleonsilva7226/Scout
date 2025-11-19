from scout.models import JobInfo

def run_scout_agent(url: str, worksheet) -> JobInfo:
    """
    Full pipeline:
      - fetch_job_page(url)
      - extract_job_info(text)
      - log_job_to_sheet(job, worksheet)
      - return JobInfo
    """
