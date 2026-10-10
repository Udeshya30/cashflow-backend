from datetime import date

from app.repositories.base import CaseRepository
from app.schemas.diary_entry import DiaryEntryCreate, DiaryEntryRead, DiaryEntryUpdate


class DiaryService:
    def __init__(self, repository: CaseRepository) -> None:
        self.repository = repository

    def list_entries(self, case_id: int | None = None) -> list[DiaryEntryRead]:
        return self.repository.list_diary_entries(case_id)

    def get_entry(self, entry_id: int) -> DiaryEntryRead | None:
        return self.repository.get_diary_entry(entry_id)

    def list_entries_by_date(self, entry_date: date) -> list[DiaryEntryRead]:
        return self.repository.list_diary_entries_by_date(entry_date)

    def list_entries_by_date_range(
        self,
        start_date: date,
        end_date: date,
    ) -> list[DiaryEntryRead]:
        return self.repository.list_diary_entries_by_date_range(start_date, end_date)

    def create_entry(self, entry: DiaryEntryCreate) -> DiaryEntryRead:
        return self.repository.create_diary_entry(entry)

    def update_entry(self, entry_id: int, entry: DiaryEntryUpdate) -> DiaryEntryRead | None:
        return self.repository.update_diary_entry(entry_id, entry)

    def delete_entry(self, entry_id: int) -> bool:
        return self.repository.delete_diary_entry(entry_id)
