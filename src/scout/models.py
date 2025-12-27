"""Models for Scout"""
from enum import Enum
from pydantic import BaseModel

class JobLevel(Enum):
    """Job experience level"""
    INTERN = "intern"
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"
    EXECUTIVE = "executive"

class RemoteType(Enum):
    """Remote work arrangement type"""
    ON_SITE = "on_site"
    REMOTE = "remote"
    HYBRID = "hybrid"
    FLEXIBLE = "flexible"

class AtsType(Enum):
    """Applicant Tracking System type"""
    GREENHOUSE = "greenhouse"
    LEVER = "lever"
    WORKDAY = "workday"
    TALEO = "taleo"
    ICIMS = "icims"
    CUSTOM = "custom"
    UNKNOWN = "unknown"


class JobInfo(BaseModel):
    company: str
    contact_person: str | None
    title: str
    location: str
    salary: str | None
    url: str
    date_applied: str | None
    date_confirmation: str | None
    date_latest_reply: str | None
    status: str | None
    reason_outcome: str | None
    level: JobLevel | None
    remote_type: RemoteType | None
    ats: AtsType | None
