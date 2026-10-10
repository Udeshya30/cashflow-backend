from fastapi.testclient import TestClient

from app.api.dependencies import get_case_service
from app.main import app
from app.repositories.json_repository import JsonCaseRepository
from app.services.case_service import CaseService


def test_health_check(tmp_path) -> None:
    data_file = tmp_path / "caseflow.json"

    def override_case_service() -> CaseService:
        return CaseService(JsonCaseRepository(data_file))

    app.dependency_overrides[get_case_service] = override_case_service
    client = TestClient(app)

    response = client.get("/health")

    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "storage": "available"}
    assert data_file.exists()
