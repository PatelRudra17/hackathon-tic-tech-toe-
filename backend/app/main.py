import os
import uuid
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, UploadFile, File, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from loguru import logger
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.api.middleware import RequestLoggingMiddleware
from app.api.routes import parse, match, candidates, skills
from app.api.auth import verify_api_key

settings = get_settings()

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
PROJECT_ROOT = BASE_DIR.parent  # project root
FRONTEND_DIR = PROJECT_ROOT / "frontend"

# ─── Rate Limiter ───
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown events."""
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")

    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

    # Initialize services
    from app.services.skill_taxonomy import get_taxonomy_service
    taxonomy = get_taxonomy_service()
    logger.info(f"Skill taxonomy loaded: {len(taxonomy.get_all_skills_flat())} skills")

    # Initialize Redis
    from app.services.redis_service import get_redis_service
    redis_svc = get_redis_service()
    await redis_svc._ensure_connected()

    yield

    # Shutdown: close Redis
    from app.services.redis_service import get_redis_service
    await get_redis_service().close()
    logger.info(f"Shutting down {settings.APP_NAME}")


# Create FastAPI app
app = FastAPI(
    title="Talent Intelligence API",
    description="""
## Multi-Agent AI System for Intelligent Resume Parsing, Skill-Set Matching, and API-Ready Talent Intelligence

### Features
- **Resume Parsing**: Upload PDF, DOCX, or TXT resumes for AI-powered structured data extraction
- **Skill Normalization**: Automatic mapping of skills to a canonical taxonomy (JS → JavaScript, K8s → Kubernetes)
- **Semantic Matching**: Smart candidate-to-job matching using vector embeddings beyond keyword search
- **Batch Processing**: Process hundreds of resumes concurrently with async job tracking
- **Skill Taxonomy**: Browse and search a hierarchical database of 5000+ skills
- **Webhook Callbacks**: Get notified when async batch processing completes

### Authentication
All endpoints require an API key passed via the `X-API-Key` header.

### Rate Limiting
API is rate-limited to 100 requests per minute per IP.

### Architecture
The system uses a multi-agent architecture powered by **LangGraph**:
1. **Parsing Agent** — Extracts structured data from resumes (PDF, DOCX, TXT)
2. **Normalization Agent** — Maps skills to canonical taxonomy with proficiency estimation
3. **Matching Agent** — Performs semantic skill-to-job matching with gap analysis
4. **Orchestrator** — LangGraph StateGraph pipeline with retry logic and observability
    """,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ─── Rate Limiting ───
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ─── Middleware ───
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(parse.router)
app.include_router(match.router)
app.include_router(candidates.router)
app.include_router(skills.router)

# Serve static files (CSS, JS) from frontend/
app.mount("/static/css", StaticFiles(directory=str(FRONTEND_DIR / "static" / "css")), name="css")
app.mount("/static/js", StaticFiles(directory=str(FRONTEND_DIR / "static" / "js")), name="js")

# Serve sample resumes as static files for the frontend demo buttons
app.mount("/static/samples", StaticFiles(directory=str(BASE_DIR / "app" / "data" / "sample_resumes")), name="samples")


# ─── Root & Health Endpoints ───

@app.get("/", response_class=HTMLResponse, tags=["Frontend"])
async def root():
    """Serve the frontend UI."""
    html_path = FRONTEND_DIR / "templates" / "index.html"
    return HTMLResponse(content=html_path.read_text(encoding="utf-8"))


@app.get("/api", tags=["Health"])
async def api_root():
    """API root — basic info."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    from app.services.skill_taxonomy import get_taxonomy_service
    from app.services.redis_service import get_redis_service

    taxonomy = get_taxonomy_service()
    redis_svc = get_redis_service()

    # Check Redis
    redis_ok = False
    try:
        if redis_svc._redis:
            await redis_svc._redis.ping()
            redis_ok = True
    except Exception:
        pass

    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "services": {
            "skill_taxonomy": {
                "status": "ok",
                "total_skills": len(taxonomy.get_all_skills_flat()),
            },
            "redis": {"status": "ok" if redis_ok else "fallback (in-memory)"},
            "parsing_agent": {"status": "ok"},
            "normalization_agent": {"status": "ok"},
            "matching_agent": {"status": "ok"},
            "orchestrator": {"status": "ok", "engine": "LangGraph"},
        },
    }


# ─── Quick Demo Endpoint (no auth required) ───

@app.post("/demo/parse", tags=["Demo"])
@limiter.limit("20/minute")
async def demo_parse(request: Request, file: UploadFile = File(...)):
    """Demo endpoint — parse a resume without API key (for testing)."""
    content = await file.read()

    from app.agents.orchestrator import get_orchestrator
    orchestrator = get_orchestrator()
    result = await orchestrator.process_resume(content, file.filename or "resume.txt")

    if result["status"] != "success":
        return {"status": "error", "message": result.get("error", "Parsing failed")}

    parsed = result["parsed_resume"]
    return {
        "status": "success",
        "candidate_id": str(uuid.uuid4()),
        "name": parsed.personal_info.name,
        "email": parsed.personal_info.email,
        "phone": parsed.personal_info.phone,
        "skills": [{"name": s.canonical_name or s.name, "category": s.category} for s in parsed.skills],
        "work_experiences": len(parsed.work_experiences),
        "educations": len(parsed.educations),
        "certifications": len(parsed.certifications),
        "publications": len(parsed.publications),
        "processing_time_ms": result["processing_time_ms"],
    }


@app.post("/demo/match", tags=["Demo"])
@limiter.limit("20/minute")
async def demo_match(
    request: Request,
    file: UploadFile = File(...),
    job_title: str = "Software Engineer",
    required_skills: str = "Python,JavaScript,Docker",
    preferred_skills: str = "AWS,Kubernetes,React",
):
    """Demo endpoint — parse resume and match against a job (no auth)."""
    content = await file.read()

    from app.agents.orchestrator import get_orchestrator
    from app.models.schemas import JobDescriptionRequest

    job = JobDescriptionRequest(
        title=job_title,
        description=f"Looking for a {job_title}",
        required_skills=[s.strip() for s in required_skills.split(",")],
        preferred_skills=[s.strip() for s in preferred_skills.split(",")],
    )

    orchestrator = get_orchestrator()
    result = await orchestrator.process_and_match(content, file.filename or "resume.txt", job)

    if result["status"] != "success":
        return {"status": "error", "message": result.get("error", "Processing failed")}

    match_result = result.get("match_result", {})
    return {
        "status": "success",
        "overall_score": match_result.get("overall_score", 0),
        "skill_match_score": match_result.get("skill_match_score", 0),
        "experience_score": match_result.get("experience_score", 0),
        "recommendation": match_result.get("recommendation", ""),
        "matched_skills": [
            {"skill": m.skill, "type": m.match_type, "confidence": m.confidence}
            for m in match_result.get("matched_skills", [])
        ],
        "missing_skills": match_result.get("missing_skills", []),
        "processing_time_ms": result["processing_time_ms"],
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
