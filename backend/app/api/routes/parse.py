import time
import uuid
from typing import List
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks, Request
from loguru import logger

from app.api.auth import verify_api_key
from app.agents.orchestrator import get_orchestrator
from app.models.schemas import (
    ResumeParseResponse, ParsedResume, BatchParseRequest, BatchParseResponse,
    BatchStatusResponse, ErrorResponse, WebhookPayload
)
from app.services.redis_service import get_redis_service
from app.config import get_settings

settings = get_settings()
router = APIRouter(prefix="/api/v1", tags=["Resume Parsing"])


@router.post(
    "/parse",
    response_model=ResumeParseResponse,
    responses={400: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
    summary="Parse a single resume",
    description="Upload a resume file (PDF, DOCX, or TXT) and get structured parsed data.",
)
async def parse_resume(
    request: Request,
    file: UploadFile = File(..., description="Resume file (PDF, DOCX, or TXT)"),
    api_key: str = Depends(verify_api_key),
):
    """Parse a single resume file and return structured data."""
    # Validate file
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    allowed_extensions = {".pdf", ".docx", ".doc", ".txt", ".text"}
    ext = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file format '{ext}'. Allowed: {', '.join(allowed_extensions)}",
        )

    # Check file size
    content = await file.read()
    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_UPLOAD_SIZE_MB}MB",
        )

    # Process through orchestrator
    orchestrator = get_orchestrator()
    result = await orchestrator.process_resume(content, file.filename)

    if result["status"] != "success":
        raise HTTPException(
            status_code=500,
            detail=result.get("error", "Resume parsing failed"),
        )

    parsed_resume = result["parsed_resume"]
    candidate_id = str(uuid.uuid4())

    # Persist candidate in Redis
    redis_svc = get_redis_service()
    await redis_svc.store_candidate(candidate_id, {
        "parsed_resume": parsed_resume.model_dump(),
        "filename": file.filename,
        "created_at": time.time(),
    })

    return ResumeParseResponse(
        candidate_id=candidate_id,
        status="success",
        parsed_data=parsed_resume,
        processing_time_ms=result["processing_time_ms"],
        agent_traces={
            "request_id": result["request_id"],
            "total_duration_ms": result["processing_time_ms"],
            "agents": [
                {
                    "name": t.agent_name,
                    "status": t.status,
                    "duration_ms": t.duration_ms,
                }
                for t in result["traces"].agent_traces
            ],
        },
    )


@router.post(
    "/parse/batch",
    response_model=BatchParseResponse,
    summary="Parse multiple resumes (batch)",
    description="Upload multiple resume files for async batch processing with optional webhook callback.",
)
async def parse_batch(
    request: Request,
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(..., description="Resume files"),
    webhook_url: str = None,
    api_key: str = Depends(verify_api_key),
):
    """Upload multiple resumes for batch processing."""
    if not files:
        raise HTTPException(status_code=400, detail="No files provided")

    if len(files) > 100:
        raise HTTPException(status_code=400, detail="Maximum 100 files per batch")

    batch_id = str(uuid.uuid4())

    # Read all file contents
    file_data = []
    for f in files:
        content = await f.read()
        file_data.append({"content": content, "filename": f.filename or "unknown"})

    # Store batch job in Redis
    redis_svc = get_redis_service()
    await redis_svc.store_batch_job(batch_id, {
        "status": "processing",
        "total_files": len(files),
        "processed_files": 0,
        "failed_files": 0,
        "results": [],
        "error_log": [],
        "webhook_url": webhook_url,
        "created_at": time.time(),
    })

    # Process in background
    background_tasks.add_task(_process_batch, batch_id, file_data, webhook_url)

    return BatchParseResponse(
        batch_id=batch_id,
        status="processing",
        total_files=len(files),
        message=f"Batch processing started. Use GET /api/v1/parse/batch/{batch_id} to check status.",
    )


@router.get(
    "/parse/batch/{batch_id}",
    response_model=BatchStatusResponse,
    summary="Get batch processing status",
)
async def get_batch_status(
    batch_id: str,
    api_key: str = Depends(verify_api_key),
):
    """Get the status of a batch processing job."""
    redis_svc = get_redis_service()
    job = await redis_svc.get_batch_job(batch_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Batch job {batch_id} not found")

    from datetime import datetime

    return BatchStatusResponse(
        batch_id=batch_id,
        status=job["status"],
        total_files=job["total_files"],
        processed_files=job["processed_files"],
        failed_files=job["failed_files"],
        results=job.get("results", []),
        error_log=job.get("error_log", []),
        created_at=datetime.fromtimestamp(job["created_at"]),
        completed_at=datetime.fromtimestamp(job["completed_at"]) if job.get("completed_at") else None,
    )


async def _process_batch(batch_id: str, files: list, webhook_url: str = None):
    """Background task for batch processing."""
    orchestrator = get_orchestrator()
    redis_svc = get_redis_service()

    async def progress_callback(bid, index, total, status):
        job = await redis_svc.get_batch_job(bid)
        if job:
            if status == "processed":
                job["processed_files"] += 1
            elif status == "failed":
                job["failed_files"] += 1
            await redis_svc.store_batch_job(bid, job)

    result = await orchestrator.process_batch(files, callback=progress_callback)

    # Update batch job in Redis
    batch_results = []
    for r in result.get("results", []):
        if r.get("parsed_resume"):
            candidate_id = str(uuid.uuid4())
            parsed = r["parsed_resume"]
            # Persist each candidate
            await redis_svc.store_candidate(candidate_id, {
                "parsed_resume": parsed.model_dump() if hasattr(parsed, "model_dump") else parsed,
                "filename": r.get("filename"),
                "created_at": time.time(),
            })
            batch_results.append({
                "filename": r.get("filename"),
                "candidate_id": candidate_id,
                "status": "success",
                "name": parsed.personal_info.name if hasattr(parsed, "personal_info") else None,
            })

    await redis_svc.update_batch_job(batch_id, {
        "status": "completed",
        "processed_files": result["processed_files"],
        "failed_files": result["failed_files"],
        "results": batch_results,
        "error_log": result.get("error_log", []),
        "completed_at": time.time(),
    })

    # Send webhook if configured
    if webhook_url:
        try:
            import httpx
            payload = WebhookPayload(
                event="batch_completed",
                batch_id=batch_id,
                status="completed",
                data={
                    "processed_files": result["processed_files"],
                    "failed_files": result["failed_files"],
                },
            )
            async with httpx.AsyncClient() as client:
                await client.post(webhook_url, json=payload.model_dump(mode="json"))
        except Exception as e:
            logger.error(f"Webhook callback failed: {e}")
