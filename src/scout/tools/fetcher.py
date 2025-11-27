"""
Method for scraping webpages to get text
"""
from playwright.sync_api import sync_playwright

def fetch_job_page(url: str) -> str:
    """
    Fetch raw job page HTML and return it.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(user_agent=(
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        ))
        page.goto(url, wait_until="networkidle")
        return page.content()