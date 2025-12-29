"""Comprehensive tests for job page fetching functionality"""
import pytest

# Skip entire test file if Playwright is not installed
pytest.importorskip("playwright")

from unittest.mock import Mock, patch, MagicMock
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, Error as PlaywrightError

# Mark all tests in this module as E2E tests
pytestmark = pytest.mark.e2e


class TestFetchJobPage:
    """Tests for fetch_job_page function"""
    
    @patch('scout.tools.fetcher.sync_playwright')
    def test_fetch_job_page_success(self, mock_playwright):
        """Test successful page fetch"""
        # Setup mocks
        mock_page = MagicMock()
        mock_page.content.return_value = "<html><body><h1>Job Title</h1></body></html>"
        
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright_instance = MagicMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
        mock_playwright.return_value.__exit__.return_value = None
        
        from scout.tools.fetcher import fetch_job_page
        
        result = fetch_job_page("https://example.com/job/123")
        
        assert result == "<html><body><h1>Job Title</h1></body></html>"
        mock_page.goto.assert_called_once_with("https://example.com/job/123", wait_until="networkidle", timeout=20000)
        mock_browser.new_page.assert_called_once()
        mock_playwright_instance.chromium.launch.assert_called_once_with(headless=True)
    
    @patch('scout.tools.fetcher.sync_playwright')
    def test_fetch_job_page_sets_user_agent(self, mock_playwright):
        """Test that user agent is set correctly"""
        mock_page = MagicMock()
        mock_page.content.return_value = "<html></html>"
        
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright_instance = MagicMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
        mock_playwright.return_value.__exit__.return_value = None
        
        from scout.tools.fetcher import fetch_job_page
        
        fetch_job_page("https://example.com/job/123")
        
        # Check that new_page was called with user_agent
        call_kwargs = mock_browser.new_page.call_args[1]
        assert "user_agent" in call_kwargs
        assert "Mozilla" in call_kwargs["user_agent"]
        assert "Chrome" in call_kwargs["user_agent"]
    
    @patch('scout.tools.fetcher.sync_playwright')
    def test_fetch_job_page_waits_for_networkidle(self, mock_playwright):
        """Test that page waits for networkidle"""
        mock_page = MagicMock()
        mock_page.content.return_value = "<html></html>"
        
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright_instance = MagicMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
        mock_playwright.return_value.__exit__.return_value = None
        
        from scout.tools.fetcher import fetch_job_page
        
        fetch_job_page("https://example.com/job/123")
        
        # Check that goto was called with wait_until="networkidle"
        mock_page.goto.assert_called_once()
        args, kwargs = mock_page.goto.call_args
        assert kwargs.get("wait_until") == "networkidle"
    
    @patch('scout.tools.fetcher.sync_playwright')
    def test_fetch_job_page_handles_timeout(self, mock_playwright):
        """Test handling of timeout errors"""
        mock_page = MagicMock()
        mock_page.goto.side_effect = PlaywrightTimeoutError("Timeout")
        
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright_instance = MagicMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
        mock_playwright.return_value.__exit__.return_value = None
        
        from scout.tools.fetcher import fetch_job_page
        
        with pytest.raises(PlaywrightTimeoutError):
            fetch_job_page("https://example.com/job/123")
    
    @patch('scout.tools.fetcher.sync_playwright')
    def test_fetch_job_page_handles_playwright_error(self, mock_playwright):
        """Test handling of general Playwright errors"""
        mock_playwright_instance = MagicMock()
        mock_playwright_instance.chromium.launch.side_effect = PlaywrightError("Browser launch failed")
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
        mock_playwright.return_value.__exit__.return_value = None
        
        from scout.tools.fetcher import fetch_job_page
        
        with pytest.raises(PlaywrightError):
            fetch_job_page("https://example.com/job/123")
    
    @patch('scout.tools.fetcher.sync_playwright')
    def test_fetch_job_page_different_urls(self, mock_playwright):
        """Test fetching different URL formats"""
        mock_page = MagicMock()
        mock_page.content.return_value = "<html></html>"
        
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright_instance = MagicMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
        mock_playwright.return_value.__exit__.return_value = None
        
        from scout.tools.fetcher import fetch_job_page
        
        urls = [
            "https://example.com/job/123",
            "http://example.com/job/456",
            "https://careers.company.com/position/789",
        ]
        
        for url in urls:
            fetch_job_page(url)
            mock_page.goto.assert_called_with(url, wait_until="networkidle", timeout=20000)
        
        assert mock_page.goto.call_count == len(urls)
    
    @patch('scout.tools.fetcher.sync_playwright')
    def test_fetch_job_page_returns_full_html(self, mock_playwright):
        """Test that full HTML content is returned"""
        expected_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Software Engineer</title>
            <script>console.log('test');</script>
        </head>
        <body>
            <h1>Software Engineer</h1>
            <p>Build amazing products</p>
            <div class="requirements">
                <ul>
                    <li>Python</li>
                    <li>JavaScript</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        mock_page = MagicMock()
        mock_page.content.return_value = expected_html
        
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright_instance = MagicMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
        mock_playwright.return_value.__exit__.return_value = None
        
        from scout.tools.fetcher import fetch_job_page
        
        result = fetch_job_page("https://example.com/job/123")
        
        assert result == expected_html
        assert "<html>" in result
        assert "Software Engineer" in result
        assert "<script>" in result  # Should include all HTML
    
    @patch('scout.tools.fetcher.sync_playwright')
    def test_fetch_job_page_cleans_up_browser(self, mock_playwright):
        """Test that browser is properly closed after use"""
        mock_page = MagicMock()
        mock_page.content.return_value = "<html></html>"
        
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright_instance = MagicMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        context_manager = MagicMock()
        context_manager.__enter__.return_value = mock_playwright_instance
        context_manager.__exit__.return_value = None
        mock_playwright.return_value = context_manager
        
        from scout.tools.fetcher import fetch_job_page
        
        fetch_job_page("https://example.com/job/123")
        
        # Verify context manager was used (cleanup happens in __exit__)
        context_manager.__enter__.assert_called_once()
        context_manager.__exit__.assert_called_once()
    
    @patch('scout.tools.fetcher.sync_playwright')
    def test_fetch_job_page_empty_response(self, mock_playwright):
        """Test handling of empty page content"""
        mock_page = MagicMock()
        mock_page.content.return_value = ""
        
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright_instance = MagicMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
        mock_playwright.return_value.__exit__.return_value = None
        
        from scout.tools.fetcher import fetch_job_page
        
        result = fetch_job_page("https://example.com/job/123")
        assert result == ""
    
    @patch('scout.tools.fetcher.sync_playwright')
    def test_fetch_job_page_handles_network_error(self, mock_playwright):
        """Test handling of network errors during page load"""
        mock_page = MagicMock()
        mock_page.goto.side_effect = PlaywrightError("Network error: Failed to load")
        
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright_instance = MagicMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
        mock_playwright.return_value.__exit__.return_value = None
        
        from scout.tools.fetcher import fetch_job_page
        
        with pytest.raises(PlaywrightError, match="Network error"):
            fetch_job_page("https://example.com/job/123")
    
    @patch('scout.tools.fetcher.sync_playwright')
    def test_fetch_job_page_handles_invalid_url(self, mock_playwright):
        """Test handling of invalid URLs"""
        mock_page = MagicMock()
        mock_page.goto.side_effect = PlaywrightError("Invalid URL")
        
        mock_browser = MagicMock()
        mock_browser.new_page.return_value = mock_page
        
        mock_playwright_instance = MagicMock()
        mock_playwright_instance.chromium.launch.return_value = mock_browser
        mock_playwright.return_value.__enter__.return_value = mock_playwright_instance
        mock_playwright.return_value.__exit__.return_value = None
        
        from scout.tools.fetcher import fetch_job_page
        
        with pytest.raises(PlaywrightError):
            fetch_job_page("not-a-valid-url")
