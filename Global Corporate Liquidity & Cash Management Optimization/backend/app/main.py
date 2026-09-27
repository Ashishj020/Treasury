from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.routes import router
from app.config import settings
from app.database import SessionLocal, engine
from app.data.generate import seed
from app.models.entities import Country


def _ensure_seed() -> None:
    db: Session = SessionLocal()
    try:
        if db.query(Country).count() == 0:
            seed(db, settings.seed)
    finally:
        db.close()


def create_app() -> FastAPI:
    app = FastAPI(
        title="LIQUIDITY → CONTROL",
        description="Simulated corporate treasury lab for Orion Global Industries. All figures are project data.",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(router)

    @app.on_event("startup")
    def startup():
        _ensure_seed()

    @app.get("/health")
    def health():
        return {"ok": True, "disclaimer": settings.data_disclaimer}

    return app


app = create_app()
