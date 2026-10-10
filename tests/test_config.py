from pathlib import Path

import pytest
from pydantic import ValidationError

from app.core.config import BACKEND_ROOT, Settings


def test_data_file_path_resolves_relative_to_backend_root() -> None:
    settings = Settings(DATA_FILE_PATH="data/test-caseflow.json")

    assert settings.data_file_path == BACKEND_ROOT / "data" / "test-caseflow.json"


def test_data_file_path_must_be_json_file(tmp_path) -> None:
    with pytest.raises(ValidationError):
        Settings(DATA_FILE_PATH=str(tmp_path / "caseflow.txt"))


def test_data_file_path_must_not_be_directory(tmp_path) -> None:
    with pytest.raises(ValidationError):
        Settings(DATA_FILE_PATH=str(tmp_path))
