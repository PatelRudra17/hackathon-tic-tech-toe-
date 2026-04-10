from fastapi import APIRouter, Depends, Query, Request
from app.api.auth import verify_api_key
from app.services.skill_taxonomy import get_taxonomy_service
from app.models.schemas import SkillTaxonomyResponse, SkillSearchResponse, SkillTaxonomyNode

router = APIRouter(prefix="/api/v1", tags=["Skill Taxonomy"])


@router.get(
    "/skills/taxonomy",
    response_model=SkillTaxonomyResponse,
    summary="Browse skill taxonomy",
    description="Get the full hierarchical skill taxonomy tree.",
)
async def get_taxonomy(
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    """Browse the full skill taxonomy hierarchy."""
    service = get_taxonomy_service()
    tree = service.get_taxonomy_tree()
    total = len(service.get_all_skills_flat())

    return SkillTaxonomyResponse(
        total_skills=total,
        categories=tree,
    )


@router.get(
    "/skills/search",
    response_model=SkillSearchResponse,
    summary="Search skills",
    description="Search for skills by name, alias, or category.",
)
async def search_skills(
    request: Request,
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    api_key: str = Depends(verify_api_key),
):
    """Search the skill taxonomy."""
    service = get_taxonomy_service()
    results = service.search_skills(q, limit=limit)

    return SkillSearchResponse(
        query=q,
        results=[
            SkillTaxonomyNode(
                name=r["name"],
                category=r["category"],
                skill_type=r["skill_type"],
                aliases=r.get("aliases", []),
                related_skills=r.get("related_skills", []),
            )
            for r in results
        ],
        total_results=len(results),
    )


@router.get(
    "/skills/normalize",
    summary="Normalize a skill name",
    description="Map a raw skill name to its canonical form.",
)
async def normalize_skill(
    request: Request,
    skill: str = Query(..., description="Raw skill name to normalize"),
    api_key: str = Depends(verify_api_key),
):
    """Normalize a single skill name to its canonical form."""
    service = get_taxonomy_service()
    canonical, confidence = service.normalize_skill(skill)
    info = service.get_skill_info(canonical)

    return {
        "raw_skill": skill,
        "canonical_name": canonical,
        "confidence": confidence,
        "category": info["category"] if info else None,
        "skill_type": info["skill_type"] if info else None,
        "related_skills": info["related_skills"] if info else [],
        "is_known": confidence > 0.5,
    }


@router.get(
    "/skills/categories",
    summary="List skill categories",
    description="Get all top-level skill categories.",
)
async def list_categories(
    request: Request,
    api_key: str = Depends(verify_api_key),
):
    """List all skill categories."""
    service = get_taxonomy_service()
    tree = service.get_taxonomy_tree()

    categories = []
    for top_level, subcats in tree.items():
        for subcat, skills in subcats.items():
            categories.append({
                "type": top_level,
                "category": subcat,
                "skill_count": len(skills),
            })

    return {"total_categories": len(categories), "categories": categories}
