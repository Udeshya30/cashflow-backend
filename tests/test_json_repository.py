import json
from datetime import date

import pytest

from app.repositories.json_repository import CorruptedStorageError, JsonCaseRepository, StorageError
from app.schemas.case import CaseCreate, CaseUpdate
from app.schemas.diary_entry import DiaryEntryCreate, DiaryEntryUpdate
from app.schemas.status import CaseStatus
from app.services.case_service import CaseService
from app.services.diary_service import DiaryService


def test_empty_storage_is_created(tmp_path) -> None:
    data_file = tmp_path / "nested" / "caseflow.json"
    repository = JsonCaseRepository(data_file)

    repository.ensure_available()

    assert data_file.exists()
    assert json.loads(data_file.read_text(encoding="utf-8")) == {"cases": [], "diary_entries": []}


def test_create_read_update_delete_case(tmp_path) -> None:
    case_service = CaseService(JsonCaseRepository(tmp_path / "caseflow.json"))

    created = case_service.create_case(
        CaseCreate(
            case_title="XYZ vs ABC",
            case_number="CS/10/2026",
            party_name="XYZ",
            case_type="Civil Suit",
            court_name="District Court",
            court_reference="Court 3",
            description="Permanent case details",
        )
    )
    updated = case_service.update_case(created.id, CaseUpdate(status=CaseStatus.DISPOSED))

    assert created.id == 1
    assert created.case_title == "XYZ vs ABC"
    assert created.status == CaseStatus.ACTIVE
    assert updated is not None
    assert updated.status == CaseStatus.DISPOSED
    assert updated.updated_at >= created.updated_at
    assert case_service.get_case(created.id) == updated
    assert case_service.delete_case(created.id) is True
    assert case_service.get_case(created.id) is None


def test_persistence_across_repository_instances(tmp_path) -> None:
    data_file = tmp_path / "caseflow.json"
    first_service = CaseService(JsonCaseRepository(data_file))

    created = first_service.create_case(CaseCreate(case_title="Persistent Case"))

    second_service = CaseService(JsonCaseRepository(data_file))
    persisted = second_service.get_case(created.id)

    assert persisted is not None
    assert persisted.case_title == "Persistent Case"


def test_multiple_cases_receive_unique_ids(tmp_path) -> None:
    case_service = CaseService(JsonCaseRepository(tmp_path / "caseflow.json"))

    first = case_service.create_case(CaseCreate(case_title="First"))
    second = case_service.create_case(CaseCreate(case_title="Second"))

    assert [case.id for case in case_service.list_cases()] == [first.id, second.id]
    assert first.id != second.id


def test_multiple_diary_entries_reference_case_without_duplication(tmp_path) -> None:
    repository = JsonCaseRepository(tmp_path / "caseflow.json")
    case_service = CaseService(repository)
    diary_service = DiaryService(repository)
    case = case_service.create_case(CaseCreate(case_title="Timeline Case"))

    first_entry = diary_service.create_entry(
        DiaryEntryCreate(
            case_id=case.id,
            entry_date=date(2026, 10, 10),
            activity="Hearing",
            notes="Matter listed",
            next_date=date(2026, 10, 18),
        )
    )
    second_entry = diary_service.create_entry(
        DiaryEntryCreate(
            case_id=case.id,
            entry_date=date(2026, 10, 18),
            activity="Hearing",
            notes="Next date not known",
        )
    )

    stored_data = json.loads(repository.data_file_path.read_text(encoding="utf-8"))
    loaded_case = case_service.get_case(case.id)

    assert loaded_case is not None
    assert [entry.id for entry in loaded_case.diary_entries] == [first_entry.id, second_entry.id]
    assert second_entry.next_date is None
    assert "diary_entries" not in stored_data["cases"][0]
    assert stored_data["diary_entries"][0]["case_id"] == case.id
    assert "case" not in stored_data["diary_entries"][0]


def test_update_and_delete_diary_entry(tmp_path) -> None:
    repository = JsonCaseRepository(tmp_path / "caseflow.json")
    case_service = CaseService(repository)
    diary_service = DiaryService(repository)
    case = case_service.create_case(CaseCreate(case_title="Entry Case"))
    entry = diary_service.create_entry(
        DiaryEntryCreate(case_id=case.id, entry_date=date(2026, 10, 10), activity="Filed")
    )

    updated = diary_service.update_entry(entry.id, DiaryEntryUpdate(notes="Updated note"))

    assert updated is not None
    assert updated.notes == "Updated note"
    assert diary_service.delete_entry(entry.id) is True
    assert diary_service.list_entries(case.id) == []


def test_deleting_case_deletes_related_diary_entries(tmp_path) -> None:
    repository = JsonCaseRepository(tmp_path / "caseflow.json")
    case_service = CaseService(repository)
    diary_service = DiaryService(repository)
    case = case_service.create_case(CaseCreate(case_title="Cascade Case"))
    diary_service.create_entry(
        DiaryEntryCreate(case_id=case.id, entry_date=date(2026, 10, 10), activity="Hearing")
    )

    assert case_service.delete_case(case.id) is True
    assert diary_service.list_entries(case.id) == []


def test_diary_entry_requires_existing_case(tmp_path) -> None:
    diary_service = DiaryService(JsonCaseRepository(tmp_path / "caseflow.json"))

    with pytest.raises(StorageError):
        diary_service.create_entry(
            DiaryEntryCreate(case_id=999, entry_date=date(2026, 10, 10), activity="Hearing")
        )


def test_corrupted_json_is_reported_without_overwriting_file(tmp_path) -> None:
    data_file = tmp_path / "caseflow.json"
    data_file.write_text("{not valid json", encoding="utf-8")
    repository = JsonCaseRepository(data_file)

    with pytest.raises(CorruptedStorageError):
        repository.ensure_available()

    assert data_file.read_text(encoding="utf-8") == "{not valid json"


def test_duplicate_ids_are_rejected(tmp_path) -> None:
    data_file = tmp_path / "caseflow.json"
    data_file.write_text(
        json.dumps(
            {
                "cases": [
                    {
                        "id": 1,
                        "case_title": "First",
                        "case_number": None,
                        "party_name": None,
                        "case_type": None,
                        "court_name": None,
                        "court_reference": None,
                        "status": "ACTIVE",
                        "description": None,
                        "created_at": "2026-10-10T00:00:00Z",
                        "updated_at": "2026-10-10T00:00:00Z",
                    },
                    {
                        "id": 1,
                        "case_title": "Second",
                        "case_number": None,
                        "party_name": None,
                        "case_type": None,
                        "court_name": None,
                        "court_reference": None,
                        "status": "ACTIVE",
                        "description": None,
                        "created_at": "2026-10-10T00:00:00Z",
                        "updated_at": "2026-10-10T00:00:00Z",
                    },
                ],
                "diary_entries": [],
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(CorruptedStorageError):
        JsonCaseRepository(data_file).list_cases()


def test_case_timeline_is_chronological(tmp_path) -> None:
    repository = JsonCaseRepository(tmp_path / "caseflow.json")
    case_service = CaseService(repository)
    diary_service = DiaryService(repository)
    case = case_service.create_case(CaseCreate(case_title="Chronology Case"))

    later = diary_service.create_entry(
        DiaryEntryCreate(case_id=case.id, entry_date=date(2026, 10, 25), activity="Final hearing")
    )
    earlier = diary_service.create_entry(
        DiaryEntryCreate(case_id=case.id, entry_date=date(2026, 10, 10), activity="First hearing")
    )

    assert [entry.id for entry in case_service.get_timeline(case.id)] == [earlier.id, later.id]


def test_entries_by_date_and_date_range_use_diary_entry_dates(tmp_path) -> None:
    repository = JsonCaseRepository(tmp_path / "caseflow.json")
    case_service = CaseService(repository)
    diary_service = DiaryService(repository)
    first_case = case_service.create_case(CaseCreate(case_title="First Date Case"))
    second_case = case_service.create_case(CaseCreate(case_title="Second Date Case"))
    first_entry = diary_service.create_entry(
        DiaryEntryCreate(case_id=first_case.id, entry_date=date(2026, 10, 10), activity="Hearing")
    )
    same_date_entry = diary_service.create_entry(
        DiaryEntryCreate(case_id=second_case.id, entry_date=date(2026, 10, 10), activity="Mention")
    )
    range_entry = diary_service.create_entry(
        DiaryEntryCreate(case_id=second_case.id, entry_date=date(2026, 10, 18), activity="Evidence")
    )
    diary_service.create_entry(
        DiaryEntryCreate(case_id=first_case.id, entry_date=date(2026, 11, 1), activity="Outside range")
    )

    assert [entry.id for entry in diary_service.list_entries_by_date(date(2026, 10, 10))] == [
        first_entry.id,
        same_date_entry.id,
    ]
    assert [
        entry.id
        for entry in diary_service.list_entries_by_date_range(date(2026, 10, 10), date(2026, 10, 18))
    ] == [first_entry.id, same_date_entry.id, range_entry.id]


def test_search_and_status_filtering(tmp_path) -> None:
    case_service = CaseService(JsonCaseRepository(tmp_path / "caseflow.json"))
    active = case_service.create_case(
        CaseCreate(
            case_title="Alpha Recovery",
            case_number="ARB/20/2026",
            party_name="Alpha Industries",
            case_type="Arbitration",
            court_name="Commercial Court",
        )
    )
    stayed = case_service.create_case(
        CaseCreate(
            case_title="Beta Injunction",
            party_name="Beta Traders",
            status=CaseStatus.STAYED,
            description="Temporary stay ordered",
        )
    )

    assert [case.id for case in case_service.search_cases("alpha")] == [active.id]
    assert [case.id for case in case_service.search_cases("temporary stay")] == [stayed.id]
    assert [case.id for case in case_service.filter_by_status(CaseStatus.STAYED)] == [stayed.id]


def test_update_next_date(tmp_path) -> None:
    repository = JsonCaseRepository(tmp_path / "caseflow.json")
    case_service = CaseService(repository)
    diary_service = DiaryService(repository)
    case = case_service.create_case(CaseCreate(case_title="Next Date Case"))
    entry = diary_service.create_entry(
        DiaryEntryCreate(case_id=case.id, entry_date=date(2026, 10, 10), activity="Hearing")
    )

    updated = diary_service.update_entry(entry.id, DiaryEntryUpdate(next_date=date(2026, 10, 18)))

    assert updated is not None
    assert updated.next_date == date(2026, 10, 18)
