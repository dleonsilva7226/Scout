"""
Method for scraping webpages to get text
"""
import logging
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


def _sanitize_error_message(error_msg: str) -> str:
    """
    Sanitize error messages to prevent leaking API keys or secrets.
    
    Args:
        error_msg: The error message to sanitize
        
    Returns:
        Sanitized error message with potential secrets redacted
    """
    if not error_msg:
        return error_msg
    
    # Redact potential API keys (long alphanumeric strings)
    error_msg = re.sub(
        r'(api[_-]?key|apikey|token|secret|password)\s*[:=]\s*["\']?([a-zA-Z0-9._-]{20,})["\']?',
        r'\1=***REDACTED***',
        error_msg,
        flags=re.IGNORECASE
    )
    
    # Redact Bearer tokens
    error_msg = re.sub(
        r'Bearer\s+[a-zA-Z0-9._-]{20,}',
        'Bearer ***REDACTED***',
        error_msg,
        flags=re.IGNORECASE
    )
    
    # Redact API keys in format "API key: sk-..." or "key: ..."
    error_msg = re.sub(
        r'(api\s+key|key)\s*:\s*([a-zA-Z0-9._-]{20,})',
        r'\1: ***REDACTED***',
        error_msg,
        flags=re.IGNORECASE
    )
    
    # Redact any long alphanumeric strings that look like keys (50+ chars)
    error_msg = re.sub(
        r'\b(sk-[a-zA-Z0-9._-]{30,}|[a-zA-Z0-9._-]{50,})\b',
        '***REDACTED***',
        error_msg
    )
    
    return error_msg

def fetch_job_page(url: str, timeout: int = 60000) -> str:
    """
    Fetch raw job page HTML and return it.
    
    Args:
        url: URL of the job posting page
        timeout: Timeout in milliseconds (default: 60000 = 60 seconds)
        
    Returns:
        HTML content of the page
        
    Raises:
        PlaywrightTimeoutError: If page fails to load within timeout
        Exception: For other errors during page fetch
    """
    browser = None
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/119.0.0.0 Safari/537.36"
                )
            )
            
            # Try networkidle first, but many modern sites never reach networkidle
            # So we'll use a shorter timeout and fallback to domcontentloaded
            try:
                page.goto(url, wait_until="networkidle", timeout=20000)  # 20s for networkidle
            except PlaywrightTimeoutError:
                logger.warning(f"networkidle timeout for {url}, using domcontentloaded instead...")
                # Use domcontentloaded - faster and works for most pages
                # The page is likely already loaded, just not idle
                page.goto(url, wait_until="domcontentloaded", timeout=timeout)
            
            # Wait for JavaScript to render dynamic content
            page.wait_for_timeout(3000)  # Wait 3 seconds for JS to render
            
            content = page.content()
            return content
            
    except PlaywrightTimeoutError as e:
        logger.error(f"Timeout fetching {url} after trying multiple strategies: {_sanitize_error_message(str(e))}")
        raise
    except Exception as e:
        logger.error(f"Error fetching {url}: {_sanitize_error_message(str(e))}")
        raise
    finally:
        if browser:
            try:
                browser.close()
            except:
                pass