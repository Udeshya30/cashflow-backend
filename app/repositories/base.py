from datetime import date

from abc import ABC, abstractmethod

from app.schemas.case import CaseCreate, CaseRead, CaseUpdate
from app.schemas.diary_entry import DiaryEntryCreate, DiaryEntryRead, DiaryEntryUpdate
from app.schemas.status import CaseStatus


class CaseRepository(ABC):
    @abstractmethod
    def ensure_available(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_cases(self) -> list[CaseRead]:
        raise NotImplementedError

    @abstractmethod
    def get_case(self, case_id: int) -> CaseRead | None:
        raise NotImplementedError

    @abstractmethod
    def create_case(self, case: CaseCreate) -> CaseRead:
        raise NotImplementedError

    @abstractmethod
    def update_case(self, case_id: int, case: CaseUpdate) -> CaseRead | None:
        raise NotImplementedError

    @abstractmethod
    def delete_case(self, case_id: int) -> bool:
        raise NotImplementedError

    @abstractmethod
    def list_diary_entries(self, case_id: int | None = None) -> list[DiaryEntryRead]:
        raise NotImplementedError

    @abstractmethod
    def get_diary_entry(self, entry_id: int) -> DiaryEntryRead | None:
        raise NotImplementedError

    @abstractmethod
    def get_case_timeline(self, case_id: int) -> list[DiaryEntryRead]:
        raise NotImplementedError

    @abstractmethod
    def list_diary_entries_by_date(self, entry_date: date) -> list[DiaryEntryRead]:
        raise NotImplementedError

    @abstractmethod
    def list_diary_entries_by_date_range(
        self,
        start_date: date,
        end_date: date,
    ) -> list[DiaryEntryRead]:
        raise NotImplementedError

    @abstractmethod
    def search_cases(self, query: str) -> list[CaseRead]:
        raise NotImplementedError

    @abstractmethod
    def filter_cases_by_status(self, status: CaseStatus) -> list[CaseRead]:
        raise NotImplementedError

    @abstractmethod
    def create_diary_entry(self, entry: DiaryEntryCreate) -> DiaryEntryRead:
        raise NotImplementedError

    @abstractmethod
    def update_diary_entry(self, entry_id: int, entry: DiaryEntryUpdate) -> DiaryEntryRead | None:
        raise NotImplementedError

    @abstractmethod
    def delete_diary_entry(self, entry_id: int) -> bool:
        raise NotImplementedError
