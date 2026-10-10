from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_DATA_FILE_PATH = Path(__file__).resolve().parents[2] / "data" / "caseflow.json"
BACKEND_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_env: str = Field(default="development", alias="APP_ENV")
    cors_origins: list[str] = Field(default=["http://localhost:5173"], alias="CORS_ORIGINS")
    data_file_path: Path = Field(default=DEFAULT_DATA_FILE_PATH, alias="DATA_FILE_PATH")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @field_validator("data_file_path", mode="after")
    @classmethod
    def validate_data_file_path(cls, value: Path) -> Path:
        data_file_path = value if value.is_absolute() else BACKEND_ROOT / value
        if data_file_path.exists() and data_file_path.is_dir():
            raise ValueError("DATA_FILE_PATH must point to a JSON file, not a directory.")
        if data_file_path.suffix != ".json":
            raise ValueError("DATA_FILE_PATH must use a .json file.")
        return data_file_path


@lru_cache
def get_settings() -> Settings:
    return Settings()
