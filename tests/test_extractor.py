# tests/test_extractor.py
from src.scout.models import JobInfo, JobLevel, RemoteType, AtsType
from src.scout.tools import extractor


def test_extract_job_info_uses_llamaindex_program(monkeypatch):
    captured = {}

    def fake_program_factory():
        class FakeProgram:
            def __call__(self, text: str) -> JobInfo:
                captured["text"] = text
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
    job = extractor.extract_job_info(raw_text)

    assert captured["text"] == raw_text
    assert job.company == "Citadel"
    assert job.title == "SWE Intern"
    assert job.location == "New York"
    assert job.status == "Wait for reply"
    assert job.level is JobLevel.INTERN
