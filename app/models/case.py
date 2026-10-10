from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class Case:
    id: int
    case_title: str
    case_number: str | None
    party_name: str | None
    case_type: str | None
    court_name: str | None
    court_reference: str | None
    status: str
    description: str | None
    created_at: datetime
    updated_at: datetime
