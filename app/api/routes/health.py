from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_case_service
from app.repositories.json_repository import StorageError
from app.services.case_service import CaseService

router = APIRouter()


@router.get("/health")
def health_check(case_service: CaseService = Depends(get_case_service)) -> dict[str, str]:
    try:
        case_service.ensure_storage_available()
    except StorageError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Storage is unavailable.",
        ) from error

    return {"status": "healthy", "storage": "available"}
