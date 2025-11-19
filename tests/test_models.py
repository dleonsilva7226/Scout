# tests/test_models.py

import pytest
from pydantic import ValidationError

from src.scout.models import JobInfo, JobLevel, RemoteType, AtsType


def test_jobinfo_requires_core_fields():
    with pytest.raises(ValidationError):
        JobInfo()  # type: ignore[arg-type]


def test_jobinfo_allows_basic_valid_job():
    job = JobInfo(
        company="Tesla",
        contact_person="HR",
        title="SWE Intern",
        location="Remote",
        salary="$30 per hour",
        url="https://tesla.example/job",
        date_applied="22 Oct",
        date_confirmation=None,
        date_latest_reply=None,
        status="Wait for reply",
        reason_outcome=None,
        level=JobLevel.INTERN,
        remote_type=RemoteType.REMOTE,
        ats=AtsType.OTHER,
    )

    assert job.company == "Tesla"
    assert job.level is JobLevel.INTERN
    assert job.remote_type is RemoteType.REMOTE
