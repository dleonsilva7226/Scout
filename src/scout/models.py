"""Models for Scout"""
from enum import Enum
from pydantic import BaseModel

class JobLevel(Enum): ...

class RemoteType(Enum): ...

class AtsType(Enum): ...


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
