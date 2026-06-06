from fastapi import APIRouter

from app.api.v1 import documents, jobs, notes

router = APIRouter()

router.include_router(documents.router, prefix="/documents", tags=["documents"])
router.include_router(jobs.router, prefix="/jobs", tags=["jobs"])
router.include_router(notes.router, prefix="/notes", tags=["notes"])
