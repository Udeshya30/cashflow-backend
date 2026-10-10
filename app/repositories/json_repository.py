import json
import os
import tempfile
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from app.repositories.base import CaseRepository
from app.schemas.case import CaseCreate, CaseRead, CaseUpdate
from app.schemas.diary_entry import DiaryEntryCreate, DiaryEntryRead, DiaryEntryUpdate
from app.schemas.status import CaseStatus

DataStore = dict[str, list[dict[str, Any]]]


class StorageError(RuntimeError):
    pass


class CorruptedStorageError(StorageError):
    pass


class JsonCaseRepository(CaseRepository):
    def __init__(self, data_file_path: Path | str) -> None:
        self.data_file_path = Path(data_file_path)

    def ensure_available(self) -> None:
        self._read_data()

    def list_cases(self) -> list[CaseRead]:
        data = self._read_data()
        return [self._build_case(case_data, data) for case_data in data["cases"]]

    def get_case(self, case_id: int) -> CaseRead | None:
        data = self._read_data()
        case_data = self._find_by_id(data["cases"], case_id)
        if case_data is None:
            return None
        return self._build_case(case_data, data)

    def create_case(self, case: CaseCreate) -> CaseRead:
        data = self._read_data()
        now = self._now()
        case_data = {
            **case.model_dump(),
            "id": self._next_id(data["cases"]),
            "created_at": now,
            "updated_at": now,
        }
        data["cases"].append(case_data)
        self._write_data(data)
        return self._build_case(case_data, data)

    def update_case(self, case_id: int, case: CaseUpdate) -> CaseRead | None:
        data = self._read_data()
        case_data = self._find_by_id(data["cases"], case_id)
        if case_data is None:
            return None

        updates = case.model_dump(exclude_unset=True)
        case_data.update(updates)
        case_data["updated_at"] = self._now()
        self._write_data(data)
        return self._build_case(case_data, data)

    def delete_case(self, case_id: int) -> bool:
        data = self._read_data()
        original_count = len(data["cases"])
        data["cases"] = [case_data for case_data in data["cases"] if case_data.get("id") != case_id]
        if len(data["cases"]) == original_count:
            return False

        data["diary_entries"] = [
            entry_data for entry_data in data["diary_entries"] if entry_data.get("case_id") != case_id
        ]
        self._write_data(data)
        return True

    def list_diary_entries(self, case_id: int | None = None) -> list[DiaryEntryRead]:
        data = self._read_data()
        entries = data["diary_entries"]
        if case_id is not None:
            entries = [entry_data for entry_data in entries if entry_data.get("case_id") == case_id]
        return [DiaryEntryRead.model_validate(entry_data) for entry_data in entries]

    def get_diary_entry(self, entry_id: int) -> DiaryEntryRead | None:
        data = self._read_data()
        entry_data = self._find_by_id(data["diary_entries"], entry_id)
        if entry_data is None:
            return None
        return DiaryEntryRead.model_validate(entry_data)

    def get_case_timeline(self, case_id: int) -> list[DiaryEntryRead]:
        data = self._read_data()
        if self._find_by_id(data["cases"], case_id) is None:
            return []

        entries = [
            DiaryEntryRead.model_validate(entry_data)
            for entry_data in data["diary_entries"]
            if entry_data.get("case_id") == case_id
        ]
        return sorted(entries, key=lambda entry: (entry.entry_date, entry.id))

    def list_diary_entries_by_date(self, entry_date: date) -> list[DiaryEntryRead]:
        data = self._read_data()
        entries = [
            DiaryEntryRead.model_validate(entry_data)
            for entry_data in data["diary_entries"]
            if entry_data.get("entry_date") == entry_date
        ]
        return sorted(entries, key=lambda entry: (entry.entry_date, entry.id))

    def list_diary_entries_by_date_range(
        self,
        start_date: date,
        end_date: date,
    ) -> list[DiaryEntryRead]:
        data = self._read_data()
        entries = [
            DiaryEntryRead.model_validate(entry_data)
            for entry_data in data["diary_entries"]
            if start_date <= entry_data.get("entry_date") <= end_date
        ]
        return sorted(entries, key=lambda entry: (entry.entry_date, entry.id))

    def search_cases(self, query: str) -> list[CaseRead]:
        data = self._read_data()
        normalized_query = query.strip().casefold()
        if not normalized_query:
            return self.list_cases()

        searchable_fields = (
            "case_title",
            "case_number",
            "party_name",
            "case_type",
            "court_name",
            "court_reference",
            "description",
        )
        matching_cases = [
            case_data
            for case_data in data["cases"]
            if any(
                normalized_query in str(case_data.get(field) or "").casefold()
                for field in searchable_fields
            )
        ]
        return [self._build_case(case_data, data) for case_data in matching_cases]

    def filter_cases_by_status(self, status: CaseStatus) -> list[CaseRead]:
        data = self._read_data()
        return [
            self._build_case(case_data, data)
            for case_data in data["cases"]
            if case_data.get("status") == status
        ]

    def create_diary_entry(self, entry: DiaryEntryCreate) -> DiaryEntryRead:
        data = self._read_data()
        if self._find_by_id(data["cases"], entry.case_id) is None:
            raise StorageError(f"Case {entry.case_id} does not exist.")

        now = self._now()
        entry_data = {
            **entry.model_dump(),
            "id": self._next_id(data["diary_entries"]),
            "created_at": now,
            "updated_at": now,
        }
        data["diary_entries"].append(entry_data)
        self._write_data(data)
        return DiaryEntryRead.model_validate(entry_data)

    def update_diary_entry(self, entry_id: int, entry: DiaryEntryUpdate) -> DiaryEntryRead | None:
        data = self._read_data()
        entry_data = self._find_by_id(data["diary_entries"], entry_id)
        if entry_data is None:
            return None

        entry_data.update(entry.model_dump(exclude_unset=True))
        entry_data["updated_at"] = self._now()
        self._write_data(data)
        return DiaryEntryRead.model_validate(entry_data)

    def delete_diary_entry(self, entry_id: int) -> bool:
        data = self._read_data()
        original_count = len(data["diary_entries"])
        data["diary_entries"] = [
            entry_data for entry_data in data["diary_entries"] if entry_data.get("id") != entry_id
        ]
        if len(data["diary_entries"]) == original_count:
            return False

        self._write_data(data)
        return True

    def _read_data(self) -> DataStore:
        self.data_file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.data_file_path.exists() or self.data_file_path.stat().st_size == 0:
            data = self._empty_data()
            self._write_data(data)
            return data

        try:
            raw_data = json.loads(self.data_file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise CorruptedStorageError(
                f"Storage file contains invalid JSON: {self.data_file_path}"
            ) from error

        return self._validate_data(raw_data)

    def _write_data(self, data: DataStore) -> None:
        validated_data = self._validate_data(data)
        self.data_file_path.parent.mkdir(parents=True, exist_ok=True)

        serializable_data = {
            "cases": [self._json_ready(case_data) for case_data in validated_data["cases"]],
            "diary_entries": [
                self._json_ready(entry_data) for entry_data in validated_data["diary_entries"]
            ],
        }

        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            dir=self.data_file_path.parent,
            encoding="utf-8",
        ) as temporary_file:
            json.dump(serializable_data, temporary_file, indent=2)
            temporary_file.write("\n")
            temporary_file_path = Path(temporary_file.name)

        os.replace(temporary_file_path, self.data_file_path)

    def _validate_data(self, raw_data: Any) -> DataStore:
        if not isinstance(raw_data, dict):
            raise CorruptedStorageError("Storage root must be a JSON object.")

        cases = raw_data.get("cases", [])
        diary_entries = raw_data.get("diary_entries", [])
        if not isinstance(cases, list) or not isinstance(diary_entries, list):
            raise CorruptedStorageError("Storage must contain cases and diary_entries arrays.")

        self._ensure_unique_ids(cases, "cases")
        self._ensure_unique_ids(diary_entries, "diary_entries")
        case_ids = {case_data.get("id") for case_data in cases}

        try:
            validated_cases = [
                CaseRead.model_validate({**case_data, "diary_entries": []}).model_dump(
                    exclude={"diary_entries"}
                )
                for case_data in cases
            ]
            validated_entries = [DiaryEntryRead.model_validate(entry_data).model_dump() for entry_data in diary_entries]
        except (TypeError, ValidationError) as error:
            raise CorruptedStorageError("Storage file does not match the CaseFlow data shape.") from error

        for entry_data in validated_entries:
            if entry_data["case_id"] not in case_ids:
                raise CorruptedStorageError("Diary entry references an unknown case_id.")

        return {"cases": validated_cases, "diary_entries": validated_entries}

    def _build_case(self, case_data: dict[str, Any], data: DataStore) -> CaseRead:
        entries = [
            DiaryEntryRead.model_validate(entry_data)
            for entry_data in data["diary_entries"]
            if entry_data.get("case_id") == case_data["id"]
        ]
        entries.sort(key=lambda entry: (entry.entry_date, entry.id))
        return CaseRead.model_validate({**case_data, "diary_entries": entries})

    @staticmethod
    def _empty_data() -> DataStore:
        return {"cases": [], "diary_entries": []}

    @staticmethod
    def _find_by_id(items: list[dict[str, Any]], item_id: int) -> dict[str, Any] | None:
        return next((item for item in items if item.get("id") == item_id), None)

    @staticmethod
    def _next_id(items: list[dict[str, Any]]) -> int:
        return max((int(item["id"]) for item in items), default=0) + 1

    @staticmethod
    def _ensure_unique_ids(items: list[dict[str, Any]], collection_name: str) -> None:
        ids = [item.get("id") for item in items]
        if len(ids) != len(set(ids)):
            raise CorruptedStorageError(f"Duplicate IDs found in {collection_name}.")

    @staticmethod
    def _json_ready(data: dict[str, Any]) -> dict[str, Any]:
        return {
            key: value.isoformat() if hasattr(value, "isoformat") else value
            for key, value in data.items()
        }

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC)
