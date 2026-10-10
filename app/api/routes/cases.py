from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.dependencies import get_case_service
from app.schemas.case import CaseCreate, CaseRead, CaseUpdate
from app.schemas.status import CaseStatus
from app.services.case_service import CaseService

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_case(
    case: CaseCreate,
    case_service: CaseService = Depends(get_case_service),
) -> CaseRead:
    return case_service.create_case(case)


@router.get("", response_model=list[CaseRead])
def list_cases(
    q: str | None = Query(default=None, min_length=1),
    status_filter: CaseStatus | None = Query(default=None, alias="status"),
    case_type: str | None = Query(default=None, min_length=1),
    needs_next_date: bool | None = None,
    sort: str = Query(default="updated_desc", pattern="^(updated_desc|updated_asc|title_asc|title_desc|next_date_asc|next_date_desc)$"),
    today: date | None = None,
    case_service: CaseService = Depends(get_case_service),
) -> list[CaseRead]:
    return case_service.list_cases_filtered(
        query=q,
        status=status_filter,
        case_type=case_type,
        needs_next_date=needs_next_date,
        sort=sort,
        today=today,
    )


@router.get("/{case_id}", response_model=CaseRead)
def get_case(
    case_id: int,
    case_service: CaseService = Depends(get_case_service),
) -> CaseRead:
    case = case_service.get_case(case_id)
    if case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    return case


@router.patch("/{case_id}", response_model=CaseRead)
def update_case(
    case_id: int,
    case: CaseUpdate,
    case_service: CaseService = Depends(get_case_service),
) -> CaseRead:
    updated_case = case_service.update_case(case_id, case)
    if updated_case is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    return updated_case


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(
    case_id: int,
    case_service: CaseService = Depends(get_case_service),
) -> Response:
    if not case_service.delete_case(case_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Case not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
