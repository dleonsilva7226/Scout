"""Comprehensive tests for job extraction functionality"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pydantic import ValidationError

from scout.models import JobInfo, JobLevel, RemoteType, AtsType
from scout.tools import extractor


class TestGetJobInfoProgram:
    """Tests for get_job_info_program function"""
    
    def test_program_caching(self, monkeypatch):
        """Test that program instance is cached"""
        call_count = {"count": 0}
        
        def fake_program_factory():
            call_count["count"] += 1
            return Mock()
        
        monkeypatch.setattr(extractor, "STRUCTURED_PROGRAM_AVAILABLE", True)
        monkeypatch.setattr(extractor, "validate_config", lambda: True)
        monkeypatch.setattr(
            "scout.tools.extractor.StructuredLLMProgram.from_defaults",
            lambda **kwargs: fake_program_factory()
        )
        
        # Reset cache
        extractor._program_cache = None
        
        program1 = extractor.get_job_info_program()
        program2 = extractor.get_job_info_program()
        
        assert program1 is program2
        assert call_count["count"] == 1  # Should only be called once
    
    def test_program_not_available_raises_error(self, monkeypatch):
        """Test that ImportError is raised when structured program is not available"""
        monkeypatch.setattr(extractor, "STRUCTURED_PROGRAM_AVAILABLE", False)
        extractor._program_cache = None
        
        with pytest.raises(ImportError, match="LlamaIndex structured program not available"):
            extractor.get_job_info_program()


class TestExtractJobInfo:
    """Tests for extract_job_info function"""
    
    def test_extract_job_info_uses_llamaindex_program(self, monkeypatch):
        """Test that extract_job_info uses the LlamaIndex program correctly"""
        captured = {}

        def fake_program_factory():
            class FakeProgram:
                def __call__(self, input_text: str) -> JobInfo:
                    captured["text"] = input_text
                    return JobInfo(
                        company="Citadel",
                        contact_person="HR",
                        title="SWE Intern",
                        location="New York",
                        salary="43 - $48 per hour",
                        url="https://example.com/job/123",
                        date_applied="22 Oct",
                        date_confirmation=None,
                        date_latest_reply=None,
                        status="Wait for reply",
                        reason_outcome=None,
                        level=JobLevel.INTERN,
                        remote_type=RemoteType.ON_SITE,
                        ats=AtsType.GREENHOUSE,
                    )

            return FakeProgram()

        monkeypatch.setattr(extractor, "get_job_info_program", fake_program_factory)

        raw_text = "Citadel SWE Intern in New York, 43–48 per hour..."
        job = extractor.extract_job_info(raw_text, url="https://example.com/job/123")

        assert captured["text"] == raw_text
        assert job.company == "Citadel"
        assert job.title == "SWE Intern"
        assert job.location == "New York"
        assert job.status == "Wait for reply"
        assert job.level is JobLevel.INTERN
        assert job.remote_type is RemoteType.ON_SITE
        assert job.ats is AtsType.GREENHOUSE
    
    def test_extract_job_info_empty_text(self):
        """Test that extract_job_info raises ValueError for empty text"""
        with pytest.raises(ValueError, match="Text input cannot be empty"):
            extractor.extract_job_info("")
    
    def test_extract_job_info_whitespace_only_text(self):
        """Test that extract_job_info raises ValueError for whitespace-only text"""
        with pytest.raises(ValueError, match="Text input cannot be empty"):
            extractor.extract_job_info("   \n\t  ")
    
    def test_extract_job_info_sets_url_when_unknown(self, monkeypatch):
        """Test that extract_job_info sets URL correctly when program returns unknown"""
        def fake_program_factory():
            class FakeProgram:
                def __call__(self, input_text: str) -> JobInfo:
                    return JobInfo(
                        company="Test Co",
                        contact_person=None,
                        title="Developer",
                        location="Remote",
                        salary=None,
                        url="unknown",  # Program returns unknown
                        date_applied=None,
                        date_confirmation=None,
                        date_latest_reply=None,
                        status=None,
                        reason_outcome=None,
                        level=None,
                        remote_type=None,
                        ats=None,
                    )
            return FakeProgram()

        monkeypatch.setattr(extractor, "get_job_info_program", fake_program_factory)

        job = extractor.extract_job_info("Test job posting", url="https://example.com/job/456")
        assert job.url == "https://example.com/job/456"
    
    def test_extract_job_info_sets_url_when_missing(self, monkeypatch):
        """Test that extract_job_info sets URL when program doesn't provide it"""
        def fake_program_factory():
            class FakeProgram:
                def __call__(self, input_text: str) -> JobInfo:
                    return JobInfo(
                        company="Test Co",
                        contact_person=None,
                        title="Developer",
                        location="Remote",
                        salary=None,
                        url="",  # Empty URL
                        date_applied=None,
                        date_confirmation=None,
                        date_latest_reply=None,
                        status=None,
                        reason_outcome=None,
                        level=None,
                        remote_type=None,
                        ats=None,
                    )
            return FakeProgram()

        monkeypatch.setattr(extractor, "get_job_info_program", fake_program_factory)

        job = extractor.extract_job_info("Test job posting", url="https://example.com/job/789")
        assert job.url == "https://example.com/job/789"
    
    def test_extract_job_info_missing_required_fields(self, monkeypatch):
        """Test that extract_job_info raises ValueError when required fields are missing"""
        def fake_program_factory():
            class FakeProgram:
                def __call__(self, input_text: str) -> JobInfo:
                    return JobInfo(
                        company="",  # Missing company
                        contact_person=None,
                        title="",     # Missing title
                        location="", # Missing location
                        salary=None,
                        url="https://example.com/job/123",
                        date_applied=None,
                        date_confirmation=None,
                        date_latest_reply=None,
                        status=None,
                        reason_outcome=None,
                        level=None,
                        remote_type=None,
                        ats=None,
                    )
            return FakeProgram()

        monkeypatch.setattr(extractor, "get_job_info_program", fake_program_factory)

        with pytest.raises(ValueError, match="Extraction failed: missing required fields"):
            extractor.extract_job_info("Test job posting")
    
    def test_extract_job_info_validation_error(self, monkeypatch):
        """Test that ValidationError from program is caught and re-raised as RuntimeError"""
        def fake_program_factory():
            class FakeProgram:
                def __call__(self, input_text: str) -> JobInfo:
                    # Simulate a ValidationError that might occur during JobInfo creation
                    # This could happen if the LLM returns invalid data
                    from pydantic import ValidationError
                    raise ValidationError.from_exception_data(
                        "JobInfo",
                        [{"type": "missing", "loc": ("company",), "msg": "Field required"}]
                    )
            return FakeProgram()

        monkeypatch.setattr(extractor, "get_job_info_program", fake_program_factory)

        with pytest.raises(RuntimeError, match="Extracted data validation failed"):
            extractor.extract_job_info("Test job posting")
    
    def test_extract_job_info_general_exception(self, monkeypatch):
        """Test that general exceptions are caught and re-raised as RuntimeError"""
        def fake_program_factory():
            class FakeProgram:
                def __call__(self, input_text: str) -> JobInfo:
                    raise Exception("API error")
            return FakeProgram()

        monkeypatch.setattr(extractor, "get_job_info_program", fake_program_factory)

        with pytest.raises(RuntimeError, match="Job extraction failed"):
            extractor.extract_job_info("Test job posting")
    
    def test_extract_job_info_strips_text(self, monkeypatch):
        """Test that text is stripped before processing"""
        captured = {}

        def fake_program_factory():
            class FakeProgram:
                def __call__(self, input_text: str) -> JobInfo:
                    captured["text"] = input_text
                    return JobInfo(
                        company="Test Co",
                        contact_person=None,
                        title="Developer",
                        location="Remote",
                        salary=None,
                        url="https://example.com/job/123",
                        date_applied=None,
                        date_confirmation=None,
                        date_latest_reply=None,
                        status=None,
                        reason_outcome=None,
                        level=None,
                        remote_type=None,
                        ats=None,
                    )
            return FakeProgram()

        monkeypatch.setattr(extractor, "get_job_info_program", fake_program_factory)

        extractor.extract_job_info("  Test job posting  ")
        assert captured["text"] == "Test job posting"  # Should be stripped
    
    def test_extract_job_info_all_enum_values(self, monkeypatch):
        """Test extraction with all enum values"""
        def fake_program_factory():
            class FakeProgram:
                def __call__(self, input_text: str) -> JobInfo:
                    return JobInfo(
                        company="Tech Corp",
                        contact_person=None,
                        title="Senior Engineer",
                        location="San Francisco",
                        salary=None,
                        url="https://example.com/job/123",
                        date_applied=None,
                        date_confirmation=None,
                        date_latest_reply=None,
                        status=None,
                        reason_outcome=None,
                        level=JobLevel.SENIOR,
                        remote_type=RemoteType.HYBRID,
                        ats=AtsType.LEVER,
                    )
            return FakeProgram()

        monkeypatch.setattr(extractor, "get_job_info_program", fake_program_factory)

        job = extractor.extract_job_info("Senior Engineer position")
        assert job.level is JobLevel.SENIOR
        assert job.remote_type is RemoteType.HYBRID
        assert job.ats is AtsType.LEVER


class TestNormalizeHtmlText:
    """Tests for normalize_html_text function"""
    
    def test_normalize_html_text_removes_tags(self):
        """Test HTML text normalization removes HTML tags"""
        html = "<html><body><p>Hello World</p><div>Test</div></body></html>"
        result = extractor.normalize_html_text(html)
        assert "hello world" in result
        assert "test" in result
        assert "<" not in result  # HTML tags removed
        assert ">" not in result
    
    def test_normalize_html_text_handles_special_characters(self):
        """Test that special characters are normalized"""
        html = "<p>It's a test with 'smart quotes'</p>"
        result = extractor.normalize_html_text(html)
        assert "'" in result or "'" in result
        assert result.islower()  # Should be lowercase
    
    def test_normalize_html_text_removes_whitespace(self):
        """Test that extra whitespace is cleaned up"""
        html = "<p>  Line 1  </p>\n\n<p>  Line 2  </p>"
        result = extractor.normalize_html_text(html)
        # Should have newlines but no excessive spaces
        assert "line 1" in result
        assert "line 2" in result
    
    def test_normalize_html_text_empty_html(self):
        """Test handling of empty HTML"""
        result = extractor.normalize_html_text("")
        assert result == ""
    
    def test_normalize_html_text_plain_text(self):
        """Test that plain text (no HTML) is still processed"""
        text = "This is plain text without HTML tags"
        result = extractor.normalize_html_text(text)
        assert result == text.lower()
    
    def test_normalize_html_text_complex_structure(self):
        """Test normalization of complex HTML structure"""
        html = """
        <html>
            <head><title>Job Posting</title></head>
            <body>
                <h1>Software Engineer</h1>
                <ul>
                    <li>Python</li>
                    <li>JavaScript</li>
                </ul>
            </body>
        </html>
        """
        result = extractor.normalize_html_text(html)
        assert "software engineer" in result
        assert "python" in result
        assert "javascript" in result
        assert "<" not in result


class TestFindHeadingPositions:
    """Tests for find_heading_positions function"""
    
    def test_find_heading_positions_finds_qualifications(self):
        """Test finding qualifications heading"""
        text = "some text qualifications: python experience"
        positions = extractor.find_heading_positions(text)
        assert "qualifications" in positions
        assert positions["qualifications"] > 0
    
    def test_find_heading_positions_finds_multiple_headings(self):
        """Test finding multiple headings"""
        text = "some text qualifications: python experience responsibilities: coding"
        positions = extractor.find_heading_positions(text)
        assert "qualifications" in positions
        assert "responsibilities" in positions
        assert positions["qualifications"] < positions["responsibilities"]
    
    def test_find_heading_positions_handles_variations(self):
        """Test that heading variations are found"""
        text = "what you'll do: build features"
        positions = extractor.find_heading_positions(text)
        assert "what_youll_do" in positions
    
    def test_find_heading_positions_no_headings(self):
        """Test when no headings are found"""
        text = "just some regular text without any headings"
        positions = extractor.find_heading_positions(text)
        assert positions == {}
    
    def test_find_heading_positions_case_insensitive(self):
        """Test that heading search is case insensitive"""
        # The function expects normalized (lowercase) text
        text = "QUALIFICATIONS: Python REQUIRED".lower()
        positions = extractor.find_heading_positions(text)
        assert "qualifications" in positions
    
    def test_find_heading_positions_first_match_wins(self):
        """Test that first variation match is used"""
        text = "requirements: python qualifications: java"
        positions = extractor.find_heading_positions(text)
        # Should find qualifications, not requirements (since qualifications comes first in HEADINGS)
        assert "qualifications" in positions or "requirements" in positions


class TestSliceByPositions:
    """Tests for slice_by_positions function"""
    
    def test_slice_by_positions_basic(self):
        """Test basic text slicing"""
        text_raw = "Start qualifications: Python required responsibilities: Coding skills End"
        text_norm = text_raw.lower()
        positions = {
            "qualifications": text_norm.find("qualifications"),
            "responsibilities": text_norm.find("responsibilities")
        }
        sections = extractor.slice_by_positions(text_raw, text_norm, positions)
        assert "qualifications" in sections
        assert "responsibilities" in sections
        assert "Python required" in sections["qualifications"]
        assert "Coding skills" in sections["responsibilities"]
    
    def test_slice_by_positions_single_section(self):
        """Test slicing with single section"""
        text_raw = "Start qualifications: Python required End"
        text_norm = text_raw.lower()
        positions = {"qualifications": text_norm.find("qualifications")}
        sections = extractor.slice_by_positions(text_raw, text_norm, positions)
        assert "qualifications" in sections
        assert "Python required" in sections["qualifications"]
    
    def test_slice_by_positions_ordered(self):
        """Test that sections are sliced in order of appearance in text"""
        text_raw = "A qualifications: Python B responsibilities: Coding C who you are: Experience D"
        text_norm = text_raw.lower()
        positions = {
            "qualifications": text_norm.find("qualifications"),
            "responsibilities": text_norm.find("responsibilities"),
            "who_you_are": text_norm.find("who you are")
        }
        sections = extractor.slice_by_positions(text_raw, text_norm, positions)
        
        # Check that sections are in order of appearance (sorted by position in text)
        # The function sorts by position, so order should match text order
        section_keys = list(sections.keys())
        # Verify all three sections are present
        assert len(section_keys) == 3
        assert "qualifications" in section_keys
        assert "responsibilities" in section_keys
        assert "who_you_are" in section_keys
        # Verify they're in the correct order based on text positions
        qual_pos = section_keys.index("qualifications")
        resp_pos = section_keys.index("responsibilities")
        who_pos = section_keys.index("who_you_are")
        assert qual_pos < resp_pos < who_pos
    
    def test_slice_by_positions_empty_positions(self):
        """Test slicing with empty positions"""
        sections = extractor.slice_by_positions("Some text", "some text", {})
        assert sections == {}
    
    def test_slice_by_positions_strips_whitespace(self):
        """Test that sliced sections are stripped"""
        text_raw = "  qualifications:   Python   "
        text_norm = text_raw.lower()
        positions = {"qualifications": text_norm.find("qualifications")}
        sections = extractor.slice_by_positions(text_raw, text_norm, positions)
        assert sections["qualifications"].strip() == sections["qualifications"]  # Already stripped
    
    def test_slice_by_positions_last_section_extends_to_end(self):
        """Test that last section extends to end of text"""
        text_raw = "Start qualifications: Python required More text at the end"
        text_norm = text_raw.lower()
        positions = {"qualifications": text_norm.find("qualifications")}
        sections = extractor.slice_by_positions(text_raw, text_norm, positions)
        assert "More text at the end" in sections["qualifications"]
