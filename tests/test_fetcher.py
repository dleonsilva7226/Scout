# tests/test_fetcher.py

from src.scout.tools.fetcher import fetch_job_page

class DummyResponse:
    status_code = 200
    text = """
        <html>
          <head>
            <title>Job</title>
            <script>console.log("ignore me")</script>
          </head>
          <body>
            <h1>Software Engineer</h1>
            <p>Build cool stuff.</p>
          </body>
        </html>
    """

    def raise_for_status(self) -> None:  # mimic httpx.Response
        return None


def test_fetch_job_page_calls_httpx_and_returns_clean_text(monkeypatch):
    calls = {}

    def fake_get(url, *args, **kwargs):
        calls["url"] = url
        return DummyResponse()

    # adjust to how you import httpx inside fetcher.py
    monkeypatch.setattr("scout.tools.fetcher.httpx.get", fake_get)

    text = fetch_job_page("https://example.com/job/123")

    assert calls["url"] == "https://example.com/job/123"
    # you decide what “cleaned” means, but make these true:
    assert "Software Engineer" in text
    assert "Build cool stuff." in text
    assert "console.log" not in text
    assert "<script" not in text
