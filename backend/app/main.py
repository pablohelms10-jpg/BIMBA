from __future__ import annotations

import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import router as v1_router
from app.config import settings

# ---- Logging ----------------------------------------------------------------

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


# ---- Lifespan ---------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info("BIMBA backend starting (env=%s)", settings.app_env)

    # Ensure storage backend is ready on startup
    try:
        from app.services.storage import StorageService
        StorageService()
        if settings.use_local_storage:
            logger.info("Local filesystem storage ready at %s", settings.local_storage_path)
        else:
            logger.info("MinIO bucket ready")
    except Exception as exc:
        logger.warning("Storage not available at startup: %s", exc)

    # Ensure Qdrant collection exists (optional)
    if settings.use_qdrant:
        try:
            from app.services.vector_store import VectorStoreService
            VectorStoreService()._get_client()
            logger.info("Qdrant collection ready")
        except Exception as exc:
            logger.warning("Qdrant not available at startup: %s", exc)
    else:
        logger.info("Qdrant disabled — using in-memory similarity fallback")

    yield
    logger.info("BIMBA backend shutting down")


# ---- Application ------------------------------------------------------------

if settings.use_local_storage:
    os.makedirs(settings.local_storage_path, exist_ok=True)

app = FastAPI(
    title="BIMBA API",
    description="Multimodal medical notes platform — backend API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Static files (local storage mode) -------------------------------------

if settings.use_local_storage:
    app.mount("/files", StaticFiles(directory=settings.local_storage_path), name="files")


# ---- Middleware: request timing ---------------------------------------------

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{elapsed:.1f}"
    return response


# ---- Routes -----------------------------------------------------------------

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Liveness probe endpoint."""
    return {"status": "ok", "service": "bimba-backend"}


@app.get("/ready", tags=["health"])
async def readiness_check() -> JSONResponse:
    """Readiness probe — checks DB, Redis, Qdrant."""
    checks: dict = {}

    # Database
    try:
        from sqlalchemy import text
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = f"error: {exc}"

    # Redis
    try:
        import redis as sync_redis
        r = sync_redis.from_url(settings.redis_url)
        r.ping()
        r.close()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    # Qdrant
    try:
        from qdrant_client import QdrantClient
        qc = QdrantClient(url=settings.qdrant_url, timeout=5)
        qc.get_collections()
        checks["qdrant"] = "ok"
    except Exception as exc:
        checks["qdrant"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in checks.values())
    return JSONResponse(
        content={"status": "ready" if all_ok else "degraded", "checks": checks},
        status_code=200 if all_ok else 503,
    )
