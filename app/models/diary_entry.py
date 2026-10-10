from dataclasses import dataclass
from datetime import date, datetime


@dataclass(slots=True)
class DiaryEntry:
    id: int
    case_id: int
    entry_date: date
    activity: str
    notes: str | None
    next_date: date | None
    created_at: datetime
    updated_at: datetime
