from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "app" / "data" / "store"
# Relative file URL so parent folders with "&" never enter the sqlite URL.
_DB_FILE = "policy_yields.db"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "POLICY → YIELDS"
    demo_mode: bool = True
    database_url: str = f"sqlite:///{_DB_FILE}"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    fred_api_key: str | None = None

    @property
    def origins(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
