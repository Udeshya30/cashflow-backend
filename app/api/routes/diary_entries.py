from fastapi import APIRouter, Depends, HTTPException, Response, status

from app.api.dependencies import get_case_service, get_diary_service
from app.schemas.diary_entry import (
    DiaryEntryCreate,
    DiaryEntryCreateForCase,
    DiaryEntryRead,
    DiaryEntryUpdate,
)
from app.services.case_service import CaseService
from app.services.diary_service import DiaryService

router = APIRouter(tags=["diary entries"])


@router.post(
    "/cases/{case_id}/entries",
    response_model=DiaryEntryRead,
    status_code=status.HTTP_201_CREATED,
)
def create_diary_entry(
    case_id: int,
    entry: DiaryEntryCreateForCase,
    case_service: CaseService = Depends(get_case_service),
    diary_service: DiaryService = Depends(get_diary_service),
) -> DiaryEntryRead:
    if case_service.get_case(case_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    return diary_service.create_entry(DiaryEntryCreate(case_id=case_id, **entry.model_dump()))


@router.get("/cases/{case_id}/entries", response_model=list[DiaryEntryRead])
def list_case_entries(
    case_id: int,
    case_service: CaseService = Depends(get_case_service),
    diary_service: DiaryService = Depends(get_diary_service),
) -> list[DiaryEntryRead]:
    if case_service.get_case(case_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    return diary_service.list_entries(case_id)


@router.get("/entries/{entry_id}", response_model=DiaryEntryRead)
def get_diary_entry(
    entry_id: int,
    diary_service: DiaryService = Depends(get_diary_service),
) -> DiaryEntryRead:
    entry = diary_service.get_entry(entry_id)
    if entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diary entry not found.")
    return entry


@router.patch("/entries/{entry_id}", response_model=DiaryEntryRead)
def update_diary_entry(
    entry_id: int,
    entry: DiaryEntryUpdate,
    diary_service: DiaryService = Depends(get_diary_service),
) -> DiaryEntryRead:
    updated_entry = diary_service.update_entry(entry_id, entry)
    if updated_entry is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diary entry not found.")
    return updated_entry


@router.delete("/entries/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_diary_entry(
    entry_id: int,
    diary_service: DiaryService = Depends(get_diary_service),
) -> Response:
    if not diary_service.delete_entry(entry_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Diary entry not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
