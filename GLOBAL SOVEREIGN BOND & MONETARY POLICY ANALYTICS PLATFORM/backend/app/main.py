from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import get_settings
from app.data.seed import seed_if_empty
from app.database import Base, SessionLocal, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_if_empty(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="POLICY → YIELDS",
    description="Impact of monetary policy on global sovereign bond markets. Educational research lab — not investment advice.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins + ["http://localhost:4173", "http://127.0.0.1:4173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {
        "name": "POLICY → YIELDS",
        "subtitle": "Impact of Monetary Policy on Global Sovereign Bond Markets",
        "demo_mode": settings.demo_mode,
        "docs": "/docs",
    }
