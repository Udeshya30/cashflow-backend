from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.diary_entry import DiaryEntryRead
from app.schemas.status import CaseStatus


class CaseBase(BaseModel):
    case_title: str
    case_number: str | None = None
    party_name: str | None = None
    case_type: str | None = None
    court_name: str | None = None
    court_reference: str | None = None
    status: CaseStatus = CaseStatus.ACTIVE
    description: str | None = None


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    case_title: str | None = None
    case_number: str | None = None
    party_name: str | None = None
    case_type: str | None = None
    court_name: str | None = None
    court_reference: str | None = None
    status: CaseStatus | None = None
    description: str | None = None


class CaseRead(CaseBase):
    id: int
    created_at: datetime
    updated_at: datetime
    diary_entries: list[DiaryEntryRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)
