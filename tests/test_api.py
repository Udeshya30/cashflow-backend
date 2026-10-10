import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import get_repository
from app.main import app
from app.repositories.json_repository import JsonCaseRepository


@pytest.fixture
def client(tmp_path):
    data_file = tmp_path / "caseflow.json"

    def override_repository() -> JsonCaseRepository:
        return JsonCaseRepository(data_file)

    app.dependency_overrides[get_repository] = override_repository
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_case(client: TestClient, **overrides):
    payload = {
        "case_title": "XYZ vs ABC",
        "case_number": "CS/10/2026",
        "party_name": "XYZ",
        "case_type": "Civil Suit",
        "court_name": "District Court",
        "court_reference": "Court 3",
        "description": "Recovery matter",
    }
    payload.update(overrides)
    return client.post("/api/v1/cases", json=payload)


def create_entry(client: TestClient, case_id: int, **overrides):
    payload = {
        "entry_date": "2026-10-10",
        "activity": "Hearing",
        "notes": "Matter listed",
        "next_date": "2026-10-18",
    }
    payload.update(overrides)
    return client.post(f"/api/v1/cases/{case_id}/entries", json=payload)


def test_case_crud_endpoints(client: TestClient) -> None:
    created_response = create_case(client)
    assert created_response.status_code == 201
    created = created_response.json()
    assert created["id"] == 1
    assert created["case_title"] == "XYZ vs ABC"

    list_response = client.get("/api/v1/cases")
    assert list_response.status_code == 200
    assert [case["id"] for case in list_response.json()] == [created["id"]]

    get_response = client.get(f"/api/v1/cases/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["case_number"] == "CS/10/2026"

    patch_response = client.patch(
        f"/api/v1/cases/{created['id']}",
        json={"status": "DISPOSED", "description": "Disposed after settlement"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "DISPOSED"

    delete_response = client.delete(f"/api/v1/cases/{created['id']}")
    assert delete_response.status_code == 204
    assert client.get(f"/api/v1/cases/{created['id']}").status_code == 404


def test_diary_entry_crud_endpoints(client: TestClient) -> None:
    case = create_case(client).json()

    created_response = create_entry(client, case["id"])
    assert created_response.status_code == 201
    created = created_response.json()
    assert created["case_id"] == case["id"]
    assert created["entry_date"] == "2026-10-10"

    list_response = client.get(f"/api/v1/cases/{case['id']}/entries")
    assert list_response.status_code == 200
    assert [entry["id"] for entry in list_response.json()] == [created["id"]]

    get_response = client.get(f"/api/v1/entries/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["activity"] == "Hearing"

    patch_response = client.patch(
        f"/api/v1/entries/{created['id']}",
        json={"notes": "Updated note", "next_date": None},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["notes"] == "Updated note"
    assert patch_response.json()["next_date"] is None

    delete_response = client.delete(f"/api/v1/entries/{created['id']}")
    assert delete_response.status_code == 204
    assert client.get(f"/api/v1/entries/{created['id']}").status_code == 404


def test_calendar_date_and_range_endpoints(client: TestClient) -> None:
    first_case = create_case(client, case_title="First Case").json()
    second_case = create_case(client, case_title="Second Case").json()
    first_entry = create_entry(client, first_case["id"], entry_date="2026-10-10").json()
    same_date_entry = create_entry(client, second_case["id"], entry_date="2026-10-10").json()
    range_entry = create_entry(client, second_case["id"], entry_date="2026-10-18").json()
    create_entry(client, first_case["id"], entry_date="2026-11-01")

    date_response = client.get("/api/v1/calendar/date", params={"date": "2026-10-10"})
    assert date_response.status_code == 200
    assert [item["entry"]["id"] for item in date_response.json()["items"]] == [
        first_entry["id"],
        same_date_entry["id"],
    ]
    assert date_response.json()["items"][0]["case"]["case_title"] == "First Case"

    range_response = client.get(
        "/api/v1/calendar/range",
        params={"start_date": "2026-10-10", "end_date": "2026-10-18"},
    )
    assert range_response.status_code == 200
    assert [item["entry"]["id"] for item in range_response.json()["items"]] == [
        first_entry["id"],
        same_date_entry["id"],
        range_entry["id"],
    ]


def test_dashboard_date_tracking_scenarios(client: TestClient) -> None:
    first_case = create_case(client, case_title="Diary Case", status="ACTIVE").json()
    second_case = create_case(client, case_title="Same Date Case", status="PENDING").json()

    today_entry = create_entry(
        client,
        first_case["id"],
        entry_date="2026-10-10",
        activity="Today hearing",
        next_date=None,
    ).json()
    same_day_entry = create_entry(
        client,
        second_case["id"],
        entry_date="2026-10-10",
        activity="Same day mention",
        next_date="2026-10-18",
    ).json()
    tomorrow_entry = create_entry(
        client,
        first_case["id"],
        entry_date="2026-10-11",
        activity="Tomorrow hearing",
    ).json()
    next_week_entry = create_entry(
        client,
        first_case["id"],
        entry_date="2026-10-19",
        activity="Next week hearing",
    ).json()
    month_entry = create_entry(
        client,
        second_case["id"],
        entry_date="2026-10-31",
        activity="Month end hearing",
    ).json()
    create_entry(
        client,
        second_case["id"],
        entry_date="2026-11-01",
        activity="Outside month hearing",
    )

    today_response = client.get("/api/v1/calendar/date", params={"date": "2026-10-10"})
    assert [item["entry"]["id"] for item in today_response.json()["items"]] == [
        today_entry["id"],
        same_day_entry["id"],
    ]
    assert today_response.json()["items"][0]["entry"]["next_date"] is None
    assert today_response.json()["items"][1]["entry"]["next_date"] == "2026-10-18"

    tomorrow_response = client.get("/api/v1/calendar/date", params={"date": "2026-10-11"})
    assert [item["entry"]["id"] for item in tomorrow_response.json()["items"]] == [tomorrow_entry["id"]]

    this_week_response = client.get(
        "/api/v1/calendar/range",
        params={"start_date": "2026-10-05", "end_date": "2026-10-11"},
    )
    assert [item["entry"]["id"] for item in this_week_response.json()["items"]] == [
        today_entry["id"],
        same_day_entry["id"],
        tomorrow_entry["id"],
    ]

    next_week_response = client.get(
        "/api/v1/calendar/range",
        params={"start_date": "2026-10-12", "end_date": "2026-10-18"},
    )
    assert next_week_response.json()["items"] == []

    following_week_response = client.get(
        "/api/v1/calendar/range",
        params={"start_date": "2026-10-19", "end_date": "2026-10-25"},
    )
    assert [item["entry"]["id"] for item in following_week_response.json()["items"]] == [
        next_week_entry["id"]
    ]

    month_response = client.get(
        "/api/v1/calendar/range",
        params={"start_date": "2026-10-01", "end_date": "2026-10-31"},
    )
    assert [item["entry"]["id"] for item in month_response.json()["items"]] == [
        today_entry["id"],
        same_day_entry["id"],
        tomorrow_entry["id"],
        next_week_entry["id"],
        month_entry["id"],
    ]

    custom_response = client.get(
        "/api/v1/calendar/range",
        params={"start_date": "2026-10-10", "end_date": "2026-10-19"},
    )
    assert [item["case"]["id"] for item in custom_response.json()["items"]] == [
        first_case["id"],
        second_case["id"],
        first_case["id"],
        first_case["id"],
    ]


def test_case_timeline_workflow(client: TestClient) -> None:
    case = create_case(client, case_title="Timeline Workflow Case").json()

    today_entry = create_entry(
        client,
        case["id"],
        entry_date="2026-10-10",
        activity="Initial hearing",
        notes="Listed for first time",
        next_date=None,
    ).json()
    assert today_entry["next_date"] is None

    updated_today_entry = client.patch(
        f"/api/v1/entries/{today_entry['id']}",
        json={"next_date": "2026-10-18"},
    )
    assert updated_today_entry.status_code == 200
    assert updated_today_entry.json()["next_date"] == "2026-10-18"

    future_entry = create_entry(
        client,
        case["id"],
        entry_date="2026-10-18",
        activity="Hearing",
        notes=None,
        next_date=None,
    ).json()

    future_date_response = client.get("/api/v1/calendar/date", params={"date": "2026-10-18"})
    assert future_date_response.status_code == 200
    assert [item["entry"]["id"] for item in future_date_response.json()["items"]] == [
        future_entry["id"]
    ]

    updated_future_entry = client.patch(
        f"/api/v1/entries/{future_entry['id']}",
        json={"activity": "Arguments", "notes": "Part heard", "next_date": "2026-10-25"},
    )
    assert updated_future_entry.status_code == 200
    assert updated_future_entry.json()["activity"] == "Arguments"
    assert updated_future_entry.json()["next_date"] == "2026-10-25"

    last_entry = create_entry(
        client,
        case["id"],
        entry_date="2026-10-25",
        activity="Final arguments",
        next_date=None,
    ).json()

    timeline_response = client.get(f"/api/v1/cases/{case['id']}")
    assert timeline_response.status_code == 200
    assert [entry["id"] for entry in timeline_response.json()["diary_entries"]] == [
        today_entry["id"],
        future_entry["id"],
        last_entry["id"],
    ]

    client.patch(f"/api/v1/cases/{case['id']}", json={"status": "DISPOSED"})
    disposed_timeline_response = client.get(f"/api/v1/cases/{case['id']}")
    assert len(disposed_timeline_response.json()["diary_entries"]) == 3


def test_search_and_status_filter_endpoints(client: TestClient) -> None:
    active = create_case(client, case_title="Alpha Recovery", party_name="Alpha Industries").json()
    stayed = create_case(
        client,
        case_title="Beta Injunction",
        party_name="Beta Traders",
        status="STAYED",
        court_name="Commercial Court",
    ).json()

    search_response = client.get("/api/v1/cases", params={"q": "alpha"})
    assert search_response.status_code == 200
    assert [case["id"] for case in search_response.json()] == [active["id"]]

    status_response = client.get("/api/v1/cases", params={"status": "STAYED"})
    assert status_response.status_code == 200
    assert [case["id"] for case in status_response.json()] == [stayed["id"]]

    combined_response = client.get("/api/v1/cases", params={"q": "beta", "status": "STAYED"})
    assert combined_response.status_code == 200
    assert [case["id"] for case in combined_response.json()] == [stayed["id"]]


def test_productivity_filters_and_sorting(client: TestClient) -> None:
    civil_case = create_case(
        client,
        case_title="Civil Recovery",
        case_number="CIV/1",
        case_type="Civil",
        status="ACTIVE",
    ).json()
    criminal_case = create_case(
        client,
        case_title="Criminal Appeal",
        case_number="CRM/2",
        case_type="Criminal",
        status="PENDING",
    ).json()
    old_case = create_case(
        client,
        case_title="Old Matter",
        case_number="OLD/3",
        case_type="Civil",
        status="ACTIVE",
    ).json()

    create_entry(
        client,
        civil_case["id"],
        entry_date="2026-10-20",
        activity="Upcoming civil hearing",
        next_date="2026-10-25",
    )
    create_entry(
        client,
        criminal_case["id"],
        entry_date="2026-10-12",
        activity="Upcoming criminal hearing",
        next_date=None,
    )
    create_entry(
        client,
        old_case["id"],
        entry_date="2026-10-01",
        activity="Old hearing",
        next_date=None,
    )

    search_response = client.get("/api/v1/cases", params={"q": "crm"})
    assert [case["id"] for case in search_response.json()] == [criminal_case["id"]]

    case_type_response = client.get("/api/v1/cases", params={"case_type": "Civil", "sort": "title_asc"})
    assert [case["id"] for case in case_type_response.json()] == [civil_case["id"], old_case["id"]]

    status_response = client.get("/api/v1/cases", params={"status": "PENDING"})
    assert [case["id"] for case in status_response.json()] == [criminal_case["id"]]

    needs_next_date_response = client.get(
        "/api/v1/cases",
        params={"needs_next_date": "true", "today": "2026-10-10", "sort": "title_asc"},
    )
    assert [case["id"] for case in needs_next_date_response.json()] == [
        criminal_case["id"],
        old_case["id"],
    ]

    upcoming_response = client.get(
        "/api/v1/cases",
        params={"sort": "next_date_asc", "today": "2026-10-10"},
    )
    assert [case["id"] for case in upcoming_response.json()] == [
        criminal_case["id"],
        civil_case["id"],
        old_case["id"],
    ]


def test_validation_errors(client: TestClient) -> None:
    assert client.post("/api/v1/cases", json={"case_number": "missing-title"}).status_code == 422
    assert create_case(client, status="NOT_A_STATUS").status_code == 422

    case = create_case(client).json()
    assert create_entry(client, case["id"], entry_date="not-a-date").status_code == 422

    reversed_range = client.get(
        "/api/v1/calendar/range",
        params={"start_date": "2026-10-18", "end_date": "2026-10-10"},
    )
    assert reversed_range.status_code == 422


def test_missing_resources(client: TestClient) -> None:
    assert client.get("/api/v1/cases/999").status_code == 404
    assert client.patch("/api/v1/cases/999", json={"case_title": "Missing"}).status_code == 404
    assert client.delete("/api/v1/cases/999").status_code == 404
    assert client.post(
        "/api/v1/cases/999/entries",
        json={"entry_date": "2026-10-10", "activity": "Hearing"},
    ).status_code == 404
    assert client.get("/api/v1/cases/999/entries").status_code == 404
    assert client.get("/api/v1/entries/999").status_code == 404
    assert client.patch("/api/v1/entries/999", json={"notes": "Missing"}).status_code == 404
    assert client.delete("/api/v1/entries/999").status_code == 404


def test_openapi_includes_api_v1_routes(client: TestClient) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/v1/cases" in paths
    assert "/api/v1/calendar/date" in paths


def test_corrupted_storage_returns_consistent_api_error(tmp_path) -> None:
    data_file = tmp_path / "caseflow.json"
    data_file.write_text("{not valid json", encoding="utf-8")

    def override_repository() -> JsonCaseRepository:
        return JsonCaseRepository(data_file)

    app.dependency_overrides[get_repository] = override_repository
    with TestClient(app) as test_client:
        response = test_client.get("/api/v1/cases")
    app.dependency_overrides.clear()

    assert response.status_code == 503
    assert response.json() == {"detail": "Storage is unavailable."}
