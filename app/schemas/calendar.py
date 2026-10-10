from datetime import date

from pydantic import BaseModel

from app.schemas.case import CaseRead
from app.schemas.diary_entry import DiaryEntryRead


class CalendarEntryRead(BaseModel):
    case: CaseRead
    entry: DiaryEntryRead


class CalendarDateRead(BaseModel):
    entry_date: date
    items: list[CalendarEntryRead]


class CalendarRangeRead(BaseModel):
    start_date: date
    end_date: date
    items: list[CalendarEntryRead]
