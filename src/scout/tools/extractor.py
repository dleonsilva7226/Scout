from scout.models import JobInfo
from bs4 import BeautifulSoup

HEADINGS = {
    "what_youll_do": ["what you'll do", "what you will do"],
    "responsibilities": ["responsibilities", "your responsibilities"],
    "who_you_are": ["who you are", "about you"],
    "qualifications": ["qualifications", "requirements"],
}

def get_job_info_program():
    """
    Build and return the LlamaIndex structured program that produces JobInfo.
    (Called once per extraction; returns a callable)
    """
    pass

def extract_job_info(text: str) -> JobInfo:
    """
    Convert cleaned job description text into a JobInfo model.
    """
    pass

def normalize_html_text(html: str):
    soup = BeautifulSoup(html, "html.parser")
    text_raw = "\n".join(line.strip() for line in soup.get_text(separator="\n")
                         .splitlines() if line.strip())
    text_norm = (
        text_raw
        .replace("\u2019", "'")
        .replace("’", "'")
        .lower()
    )
    return text_norm

def find_heading_positions(text_norm):
    pass

def slice_by_positions(text_raw, text_norm, positions):
    pass