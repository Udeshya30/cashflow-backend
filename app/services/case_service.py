from datetime import date

from app.repositories.base import CaseRepository
from app.schemas.case import CaseCreate, CaseRead, CaseUpdate
from app.schemas.diary_entry import DiaryEntryRead
from app.schemas.status import CaseStatus


class CaseService:
    def __init__(self, repository: CaseRepository) -> None:
        self.repository = repository

    def ensure_storage_available(self) -> None:
        self.repository.ensure_available()

    def list_cases(self) -> list[CaseRead]:
        return self.repository.list_cases()

    def get_case(self, case_id: int) -> CaseRead | None:
        return self.repository.get_case(case_id)

    def create_case(self, case: CaseCreate) -> CaseRead:
        return self.repository.create_case(case)

    def update_case(self, case_id: int, case: CaseUpdate) -> CaseRead | None:
        return self.repository.update_case(case_id, case)

    def delete_case(self, case_id: int) -> bool:
        return self.repository.delete_case(case_id)

    def get_timeline(self, case_id: int) -> list[DiaryEntryRead]:
        return self.repository.get_case_timeline(case_id)

    def search_cases(self, query: str) -> list[CaseRead]:
        return self.repository.search_cases(query)

    def filter_by_status(self, status: CaseStatus) -> list[CaseRead]:
        return self.repository.filter_cases_by_status(status)

    def list_cases_filtered(
        self,
        query: str | None = None,
        status: CaseStatus | None = None,
        case_type: str | None = None,
        needs_next_date: bool | None = None,
        sort: str = "updated_desc",
        today: date | None = None,
    ) -> list[CaseRead]:
        cases = self.repository.search_cases(query) if query else self.repository.list_cases()

        if status is not None:
            cases = [case for case in cases if case.status == status]

        if case_type:
            normalized_case_type = case_type.strip().casefold()
            cases = [
                case
                for case in cases
                if (case.case_type or "").strip().casefold() == normalized_case_type
            ]

        if needs_next_date is not None:
            today_value = today or date.today()
            cases = [
                case
                for case in cases
                if self.case_needs_next_date(case, today_value) is needs_next_date
            ]

        return self.sort_cases(cases, sort, today or date.today())

    @staticmethod
    def case_needs_next_date(case: CaseRead, today: date) -> bool:
        if not case.diary_entries:
            return True

        relevant_entries = [entry for entry in case.diary_entries if entry.entry_date <= today]
        relevant_entry = max(
            relevant_entries or case.diary_entries,
            key=lambda entry: (entry.entry_date, entry.id),
        )
        return relevant_entry.next_date is None

    @staticmethod
    def get_next_known_date(case: CaseRead, today: date) -> date | None:
        upcoming_dates = sorted(
            entry.entry_date for entry in case.diary_entries if entry.entry_date >= today
        )
        return upcoming_dates[0] if upcoming_dates else None

    @classmethod
    def sort_cases(cls, cases: list[CaseRead], sort: str, today: date) -> list[CaseRead]:
        if sort == "updated_asc":
            return sorted(cases, key=lambda case: case.updated_at)
        if sort == "title_asc":
            return sorted(cases, key=lambda case: case.case_title.casefold())
        if sort == "title_desc":
            return sorted(cases, key=lambda case: case.case_title.casefold(), reverse=True)
        if sort == "next_date_asc":
            return sorted(
                cases,
                key=lambda case: (
                    cls.get_next_known_date(case, today) is None,
                    cls.get_next_known_date(case, today) or date.max,
                    case.case_title.casefold(),
                ),
            )
        if sort == "next_date_desc":
            return sorted(
                cases,
                key=lambda case: (
                    cls.get_next_known_date(case, today) is not None,
                    cls.get_next_known_date(case, today) or date.min,
                    case.case_title.casefold(),
                ),
                reverse=True,
            )

        return sorted(cases, key=lambda case: case.updated_at, reverse=True)
