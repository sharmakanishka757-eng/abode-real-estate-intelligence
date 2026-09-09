"""FastAPI application for the ABODE property-ai-service."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import Base, engine
from app.models.preferences import UserPreference  # noqa: F401
from app.models.property import Property  # noqa: F401  # registers tables on Base.metadata
from app.routes.analysis import router as analysis_router
from app.routes.preferences import router as preferences_router
from app.routes.properties import router as properties_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="ABODE Property AI Service",
    description="Property listings and future AI intelligence for ABODE.",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(properties_router)
app.include_router(preferences_router)
app.include_router(analysis_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "property-ai-service",
    }
