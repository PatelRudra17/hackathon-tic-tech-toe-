from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger

from app.api.auth import verify_api_key
from app.agents.normalization_agent import NormalizationAgent
from app.models.schemas import CandidateSkillsResponse, SkillSchema, ErrorResponse, ParsedResume
from app.services.redis_service import get_redis_service

router = APIRouter(prefix="/api/v1", tags=["Candidates"])


@router.get(
    "/candidates/{candidate_id}/skills",
    response_model=CandidateSkillsResponse,
    responses={404: {"model": ErrorResponse}},
    summary="Get candidate skill profile",
    description="Retrieve the normalized skill profile for a candidate.",
)
async def get_candidate_skills(
    candidate_id: str,
    api_key: str = Depends(verify_api_key),
):
    """Get a candidate's normalized skill profile."""
    redis_svc = get_redis_service()
    candidate_data = await redis_svc.get_candidate(candidate_id)
    if not candidate_data:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate {candidate_id} not found",
        )

    parsed_dict = candidate_data.get("parsed_resume", {})
    parsed_resume = ParsedResume(**parsed_dict)

    norm_agent = NormalizationAgent()
    skill_summary = await norm_agent.get_skill_summary(parsed_resume.skills)

    return CandidateSkillsResponse(
        candidate_id=candidate_id,
        name=parsed_resume.personal_info.name if parsed_resume.personal_info else None,
        skills=parsed_resume.skills,
        skill_summary=skill_summary,
    )


@router.get(
    "/candidates/{candidate_id}",
    summary="Get candidate full profile",
    description="Retrieve the full parsed profile for a candidate.",
)
async def get_candidate(
    candidate_id: str,
    api_key: str = Depends(verify_api_key),
):
    """Get a candidate's full parsed profile."""
    redis_svc = get_redis_service()
    candidate_data = await redis_svc.get_candidate(candidate_id)
    if not candidate_data:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate {candidate_id} not found",
        )

    parsed_dict = candidate_data.get("parsed_resume", {})
    parsed = ParsedResume(**parsed_dict)
    return {
        "candidate_id": candidate_id,
        "personal_info": parsed.personal_info.model_dump(),
        "work_experiences": [w.model_dump() for w in parsed.work_experiences],
        "educations": [e.model_dump() for e in parsed.educations],
        "skills": [s.model_dump() for s in parsed.skills],
        "certifications": [c.model_dump() for c in parsed.certifications],
        "projects": [p.model_dump() for p in parsed.projects],
        "publications": [pub.model_dump() for pub in parsed.publications],
        "parsing_confidence": parsed.parsing_confidence,
        "source_format": parsed.source_format,
    }


@router.get(
    "/candidates",
    summary="List all candidates",
    description="List all parsed candidates.",
)
async def list_candidates(
    api_key: str = Depends(verify_api_key),
):
    """List all stored candidates."""
    redis_svc = get_redis_service()
    all_candidates = await redis_svc.list_candidates()

    candidates = []
    for cdata in all_candidates:
        parsed_dict = cdata.get("parsed_resume", {})
        pi = parsed_dict.get("personal_info", {})
        candidates.append({
            "candidate_id": cdata.get("candidate_id", ""),
            "name": pi.get("name"),
            "email": pi.get("email"),
            "skills_count": len(parsed_dict.get("skills", [])),
            "source_format": parsed_dict.get("source_format", ""),
        })

    return {"total": len(candidates), "candidates": candidates}
