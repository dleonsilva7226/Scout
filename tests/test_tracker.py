# tests/test_tracker.py

from src.scout.models import JobInfo, JobLevel, RemoteType, AtsType
from src.scout.tools.tracker import log_job_to_sheet

class FakeWorksheet:
    def __init__(self) -> None:
        self.append_calls: list[list[str]] = []

    def append_row(self, values, value_input_option="RAW"):
        # Only care about the row values for now
        self.append_calls.append(values)

def make_job() -> JobInfo:
    # Use whatever defaults you like; this mirrors your sheet pattern
    return JobInfo(
        company="IBM",
        contact_person="HR",
        title="Entry Level Web Developer",
        location="On-site",               # matches your dropdown label
        salary="78 - 144K",               # could be str, that’s fine
        url="https://ibm.example/job",
        date_applied="22 Oct",
        date_confirmation=None,
        date_latest_reply=None,
        status="Wait for reply",
        reason_outcome=None,
        level=JobLevel.NEW_GRAD,
        remote_type=RemoteType.ON_SITE,
        ats=AtsType.WORKDAY,
    )

def test_log_job_to_sheet_appends_row_with_correct_columns():
    ws = FakeWorksheet()
    job = make_job()

    log_job_to_sheet(job, ws)

    assert len(ws.append_calls) == 1
    row = ws.append_calls[0]

    # Expect EXACT order to match Google Sheet columns
    assert row[0] == job.company
    assert row[1] == job.contact_person
    assert row[2] == job.title
    assert row[3] == job.location
    assert row[4] == job.salary
    assert row[5] == job.url
    assert row[6] == job.date_applied
    assert row[7] == (job.date_confirmation or "")
    assert row[8] == (job.date_latest_reply or "")
    assert row[9] == job.status
    assert row[10] == (job.reason_outcome or "")


def test_log_job_to_sheet_handles_optional_fields_as_empty_strings():
    ws = FakeWorksheet()
    job = make_job()
    job.date_confirmation = None
    job.date_latest_reply = None
    job.reason_outcome = None

    log_job_to_sheet(job, ws)

    row = ws.append_calls[0]

    assert row[7] == ""   # Date confirmation
    assert row[8] == ""   # Date latest reply
    assert row[10] == ""  # Reason outcome
