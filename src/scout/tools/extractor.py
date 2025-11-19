from scout.models import JobInfo

def get_job_info_program():
    """
    Build and return the LlamaIndex structured program that produces JobInfo.
    (Called once per extraction; returns a callable)
    """

def extract_job_info(text: str) -> JobInfo:
    """
    Convert cleaned job description text into a JobInfo model.
    """
