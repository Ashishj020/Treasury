from pathlib import Path

from pydantic_settings import BaseSettings


ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    app_name: str = "LIQUIDITY → CONTROL"
    company_name: str = "Orion Global Industries"
    headquarters: str = "London"
    data_disclaimer: str = "SIMULATED CORPORATE TREASURY DATA"
    reporting_currency: str = "INR"
    database_url: str = f"sqlite:///{(ROOT / 'treasury.db').as_posix()}"
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:4173",
        "http://127.0.0.1:4173",
    ]
    as_of_date: str = "2026-09-01"
    seed: int = 42


settings = Settings()
