from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


class DiaryEntryBase(BaseModel):
    entry_date: date
    activity: str
    notes: str | None = None
    next_date: date | None = None


class DiaryEntryCreate(DiaryEntryBase):
    case_id: int


class DiaryEntryCreateForCase(DiaryEntryBase):
    pass


class DiaryEntryUpdate(BaseModel):
    entry_date: date | None = None
    activity: str | None = None
    notes: str | None = None
    next_date: date | None = None


class DiaryEntryRead(DiaryEntryBase):
    id: int
    case_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
