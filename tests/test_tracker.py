"""Unit tests for Google Sheets tracker integration"""
from datetime import datetime
from unittest.mock import Mock

from scout.models import JobInfo, JobLevel, RemoteType, AtsType
from scout.tools.tracker import log_job_to_sheet


class FakeWorksheet:
    """Mock worksheet for testing"""
    def __init__(self):
        self.append_calls = []

    def append_row(self, values, value_input_option="RAW"):
        self.append_calls.append(values)


def test_log_job_to_sheet_column_order():
    """Test that columns are in the correct order"""
    ws = FakeWorksheet()
    job = JobInfo(
        company="TestCo",
        contact_person="Jane Doe",
        title="Software Engineer",
        location="San Francisco, CA",
        salary="$100k",
        url="https://test.com/job",
        date_applied=None,
        date_confirmation=None,
        date_latest_reply=None,
        status=None,
        reason_outcome=None,
        level=JobLevel.SENIOR,
        remote_type=RemoteType.REMOTE,
        ats=AtsType.GREENHOUSE,
    )

    log_job_to_sheet(job, ws)

    assert len(ws.append_calls) == 1
    row = ws.append_calls[0]
    
    assert row[0] == "TestCo"
    assert row[1] == "Jane Doe"
    assert row[2] == "Software Engineer"
    assert row[3] == "San Francisco, CA"
    assert row[4] == "$100k"
    assert row[5] == "https://test.com/job"
    assert row[6]  # date_applied auto-populated
    assert row[7] == ""  # date_confirmation
    assert row[8] == ""  # date_latest_reply
    assert row[9] == "to_apply"  # status default
    assert row[10] == ""  # reason_outcome
    assert row[11] == "senior"  # level enum value
    assert row[12] == "remote"  # remote_type enum value
    assert row[13] == "greenhouse"  # ats enum value


def test_log_job_to_sheet_defaults():
    """Test auto-populated default values"""
    ws = FakeWorksheet()
    job = JobInfo(
        company="TestCo",
        contact_person=None,
        title="Engineer",
        location="Remote",
        salary=None,
        url="https://test.com/job",
        date_applied=None,
        date_confirmation=None,
        date_latest_reply=None,
        status=None,
        reason_outcome=None,
        level=None,
        remote_type=None,
        ats=None,
    )

    log_job_to_sheet(job, ws)

    row = ws.append_calls[0]
    today = datetime.now().strftime("%Y-%m-%d")
    
    assert row[6] == today  # date_applied defaults to today
    assert row[9] == "to_apply"  # status defaults to "to_apply"
    assert row[13] == "unknown"  # ats defaults to "unknown"


def test_log_job_to_sheet_optional_fields():
    """Test handling of optional fields"""
    ws = FakeWorksheet()
    job = JobInfo(
        company="TestCo",
        contact_person=None,
        title="Engineer",
        location="Remote",
        salary=None,
        url="https://test.com/job",
        date_applied=None,
        date_confirmation=None,
        date_latest_reply=None,
        status=None,
        reason_outcome=None,
        level=None,
        remote_type=None,
        ats=None,
    )

    log_job_to_sheet(job, ws)

    row = ws.append_calls[0]
    assert row[1] == ""  # contact_person
    assert row[4] == ""  # salary
    assert row[7] == ""  # date_confirmation
    assert row[8] == ""  # date_latest_reply
    assert row[10] == ""  # reason_outcome
    assert row[11] == ""  # level
    assert row[12] == ""  # remote_type


def test_log_job_to_sheet_preserves_existing_values():
    """Test that existing values are preserved"""
    ws = FakeWorksheet()
    job = JobInfo(
        company="TestCo",
        contact_person=None,
        title="Engineer",
        location="Remote",
        salary=None,
        url="https://test.com/job",
        date_applied="2024-01-15",
        date_confirmation=None,
        date_latest_reply=None,
        status="applied",
        reason_outcome=None,
        level=None,
        remote_type=None,
        ats=AtsType.LEVER,
    )

    log_job_to_sheet(job, ws)

    row = ws.append_calls[0]
    assert row[6] == "2024-01-15"  # Preserved date_applied
    assert row[9] == "applied"  # Preserved status
    assert row[13] == "lever"  # Preserved ats
