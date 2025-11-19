from scout.models import JobInfo

def log_job_to_sheet(job: JobInfo, worksheet) -> None:
    """
    Append a row to Google Sheets based on the JobInfo fields,
    matching the column order in the Tracker sheet.
    """
