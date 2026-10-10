from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.dependencies import get_case_service, get_diary_service
from app.schemas.calendar import CalendarDateRead, CalendarEntryRead, CalendarRangeRead
from app.services.case_service import CaseService
from app.services.diary_service import DiaryService

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/date", response_model=CalendarDateRead)
def get_calendar_date(
    entry_date: date = Query(alias="date"),
    case_service: CaseService = Depends(get_case_service),
    diary_service: DiaryService = Depends(get_diary_service),
) -> CalendarDateRead:
    entries = diary_service.list_entries_by_date(entry_date)
    return CalendarDateRead(
        entry_date=entry_date,
        items=_with_cases(entries, case_service),
    )


@router.get("/range", response_model=CalendarRangeRead)
def get_calendar_range(
    start_date: date,
    end_date: date,
    case_service: CaseService = Depends(get_case_service),
    diary_service: DiaryService = Depends(get_diary_service),
) -> CalendarRangeRead:
    if end_date < start_date:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="end_date must be on or after start_date.",
        )

    entries = diary_service.list_entries_by_date_range(start_date, end_date)
    return CalendarRangeRead(
        start_date=start_date,
        end_date=end_date,
        items=_with_cases(entries, case_service),
    )


def _with_cases(entries, case_service: CaseService) -> list[CalendarEntryRead]:
    items: list[CalendarEntryRead] = []
    for entry in entries:
        case = case_service.get_case(entry.case_id)
        if case is not None:
            items.append(CalendarEntryRead(case=case, entry=entry))
    return items
