from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ─── Resume Parsing Schemas ───

class PersonalInfo(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    linkedin_url: Optional[str] = None
    summary: Optional[str] = None


class WorkExperienceSchema(BaseModel):
    company: Optional[str] = None
    role: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_months: Optional[int] = None
    responsibilities: Optional[str] = None
    is_current: bool = False


class EducationSchema(BaseModel):
    institution: Optional[str] = None
    degree: Optional[str] = None
    field_of_study: Optional[str] = None
    start_year: Optional[str] = None
    end_year: Optional[str] = None
    gpa: Optional[str] = None


class SkillSchema(BaseModel):
    name: str
    canonical_name: Optional[str] = None
    category: Optional[str] = None
    proficiency_level: Optional[str] = None
    years_of_experience: Optional[float] = None
    confidence_score: float = 0.0
    source: str = "explicit"


class CertificationSchema(BaseModel):
    name: str
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None


class ProjectSchema(BaseModel):
    name: str
    description: Optional[str] = None
    technologies: List[str] = []
    url: Optional[str] = None


class PublicationSchema(BaseModel):
    title: str
    authors: Optional[str] = None
    venue: Optional[str] = None
    year: Optional[str] = None
    url: Optional[str] = None
    doi: Optional[str] = None


class ParsedResume(BaseModel):
    personal_info: PersonalInfo = PersonalInfo()
    work_experiences: List[WorkExperienceSchema] = []
    educations: List[EducationSchema] = []
    skills: List[SkillSchema] = []
    certifications: List[CertificationSchema] = []
    projects: List[ProjectSchema] = []
    publications: List[PublicationSchema] = []
    raw_text: str = ""
    source_format: str = ""
    parsing_confidence: float = 0.0


# ─── API Request/Response Schemas ───

class ResumeParseResponse(BaseModel):
    candidate_id: str
    status: str = "success"
    parsed_data: ParsedResume
    processing_time_ms: float
    agent_traces: Optional[Dict[str, Any]] = None


class BatchParseRequest(BaseModel):
    webhook_url: Optional[str] = None


class BatchParseResponse(BaseModel):
    batch_id: str
    status: str = "pending"
    total_files: int
    message: str


class BatchStatusResponse(BaseModel):
    batch_id: str
    status: str
    total_files: int
    processed_files: int
    failed_files: int
    results: List[Dict[str, Any]] = []
    error_log: List[Dict[str, Any]] = []
    created_at: datetime
    completed_at: Optional[datetime] = None


class CandidateSkillsResponse(BaseModel):
    candidate_id: str
    name: Optional[str] = None
    skills: List[SkillSchema] = []
    skill_summary: Dict[str, List[str]] = {}


class JobDescriptionRequest(BaseModel):
    title: str
    company: Optional[str] = None
    description: str
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    experience_min_years: Optional[int] = None
    experience_max_years: Optional[int] = None
    location: Optional[str] = None
    job_type: Optional[str] = None


class MatchRequest(BaseModel):
    candidate_id: str
    job_description: Optional[JobDescriptionRequest] = None
    job_id: Optional[str] = None
    matching_threshold: float = Field(default=0.5, ge=0.0, le=1.0)


class SkillMatchDetail(BaseModel):
    skill: str
    match_type: str  # direct, semantic, inferred
    confidence: float
    job_requirement: str


class GapAnalysis(BaseModel):
    missing_skills: List[str] = []
    upskilling_suggestions: List[Dict[str, str]] = []


class MatchResponse(BaseModel):
    match_id: str
    candidate_id: str
    job_id: str
    overall_score: float
    skill_match_score: float
    experience_score: float
    education_score: float
    matched_skills: List[SkillMatchDetail] = []
    gap_analysis: GapAnalysis = GapAnalysis()
    recommendation: str = ""
    processing_time_ms: float = 0.0


class SkillTaxonomyNode(BaseModel):
    name: str
    category: str
    subcategory: Optional[str] = None
    skill_type: str
    aliases: List[str] = []
    parent_skill: Optional[str] = None
    related_skills: List[str] = []


class SkillTaxonomyResponse(BaseModel):
    total_skills: int
    categories: Dict[str, Dict[str, List[str]]]


class SkillSearchResponse(BaseModel):
    query: str
    results: List[SkillTaxonomyNode]
    total_results: int


# ─── Agent Trace Schemas ───

class AgentTrace(BaseModel):
    agent_name: str
    status: str  # success, failed, partial
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: float = 0.0
    input_summary: str = ""
    output_summary: str = ""
    error: Optional[str] = None
    quality_score: Optional[float] = None


class OrchestrationTrace(BaseModel):
    request_id: str
    total_duration_ms: float
    agent_traces: List[AgentTrace] = []
    status: str = "success"


# ─── Webhook Schema ───

class WebhookPayload(BaseModel):
    event: str  # batch_completed, parse_completed, match_completed
    batch_id: Optional[str] = None
    candidate_id: Optional[str] = None
    status: str
    data: Dict[str, Any] = {}
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# ─── Error Schema ───

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int
