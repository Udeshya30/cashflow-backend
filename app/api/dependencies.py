from fastapi import Depends

from app.core.config import get_settings
from app.repositories.base import CaseRepository
from app.repositories.json_repository import JsonCaseRepository
from app.services.case_service import CaseService
from app.services.diary_service import DiaryService


def get_repository() -> CaseRepository:
    settings = get_settings()
    return JsonCaseRepository(settings.data_file_path)


def get_case_service(repository: CaseRepository = Depends(get_repository)) -> CaseService:
    return CaseService(repository)


def get_diary_service(repository: CaseRepository = Depends(get_repository)) -> DiaryService:
    return DiaryService(repository)
