import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger

from app.api.auth import verify_api_key
from app.agents.orchestrator import get_orchestrator
from app.models.schemas import (
    MatchRequest, MatchResponse, JobDescriptionRequest,
    SkillMatchDetail, GapAnalysis, ErrorResponse, ParsedResume
)
from app.services.redis_service import get_redis_service

router = APIRouter(prefix="/api/v1", tags=["Job Matching"])


@router.post(
    "/match",
    response_model=MatchResponse,
    responses={400: {"model": ErrorResponse}, 404: {"model": ErrorResponse}},
    summary="Match candidate to job",
    description="Match a candidate's skill profile against a job description using semantic matching.",
)
async def match_candidate_to_job(
    request: Request,
    match_req: MatchRequest,
    api_key: str = Depends(verify_api_key),
):
    """Match a candidate against a job description."""
    redis_svc = get_redis_service()

    # Get candidate data from Redis
    candidate_data = await redis_svc.get_candidate(match_req.candidate_id)
    if not candidate_data:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate {match_req.candidate_id} not found. Parse a resume first.",
        )

    # Reconstruct ParsedResume from stored data
    parsed_dict = candidate_data.get("parsed_resume", {})
    parsed_resume = ParsedResume(**parsed_dict)

    # Get or create job description
    job = None
    job_id = match_req.job_id
    if match_req.job_id:
        job_data = await redis_svc.get_job(match_req.job_id)
        if job_data:
            job = JobDescriptionRequest(**job_data)
        else:
            raise HTTPException(status_code=404, detail=f"Job {match_req.job_id} not found")
    elif match_req.job_description:
        job = match_req.job_description
        job_id = str(uuid.uuid4())
        await redis_svc.store_job(job_id, job.model_dump())
    else:
        raise HTTPException(
            status_code=400,
            detail="Provide either job_id or job_description",
        )

    # Run matching
    orchestrator = get_orchestrator()
    result = await orchestrator.match_candidate(
        parsed_resume=parsed_resume,
        job=job,
        threshold=match_req.matching_threshold,
    )

    if result["status"] != "success" or not result.get("match_result"):
        raise HTTPException(status_code=500, detail="Matching failed")

    match = result["match_result"]
    match_id = str(uuid.uuid4())

    return MatchResponse(
        match_id=match_id,
        candidate_id=match_req.candidate_id,
        job_id=job_id,
        overall_score=match["overall_score"],
        skill_match_score=match["skill_match_score"],
        experience_score=match["experience_score"],
        education_score=match["education_score"],
        matched_skills=match["matched_skills"],
        gap_analysis=GapAnalysis(
            missing_skills=match["gap_analysis"].missing_skills,
            upskilling_suggestions=match["gap_analysis"].upskilling_suggestions,
        ),
        recommendation=match["recommendation"],
        processing_time_ms=match.get("processing_time_ms", 0),
    )


@router.post(
    "/jobs",
    summary="Create a job description",
    description="Store a job description for matching.",
)
async def create_job(
    request: Request,
    job: JobDescriptionRequest,
    api_key: str = Depends(verify_api_key),
):
    """Create and store a job description."""
    redis_svc = get_redis_service()
    job_id = str(uuid.uuid4())
    await redis_svc.store_job(job_id, job.model_dump())

    return {
        "job_id": job_id,
        "status": "created",
        "title": job.title,
        "required_skills": job.required_skills,
        "preferred_skills": job.preferred_skills,
    }


@router.get(
    "/jobs/{job_id}",
    summary="Get job description",
)
async def get_job(
    job_id: str,
    api_key: str = Depends(verify_api_key),
):
    """Retrieve a stored job description."""
    redis_svc = get_redis_service()
    job_data = await redis_svc.get_job(job_id)
    if not job_data:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return {"job_id": job_id, **job_data}


@router.get(
    "/jobs",
    summary="List all job descriptions",
)
async def list_jobs(
    api_key: str = Depends(verify_api_key),
):
    """List all stored job descriptions."""
    redis_svc = get_redis_service()
    jobs = await redis_svc.list_jobs()
    return {
        "total": len(jobs),
        "jobs": [
            {"job_id": j.get("job_id", ""), "title": j.get("title", ""), "company": j.get("company", "")}
            for j in jobs
        ],
    }
