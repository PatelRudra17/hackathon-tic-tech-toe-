import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Float, Integer, DateTime, ForeignKey, JSON, Boolean, Enum as SAEnum
)
from sqlalchemy.orm import relationship
from app.models.database import Base


def generate_uuid():
    return str(uuid.uuid4())


class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    location = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    linkedin_url = Column(String(500), nullable=True)
    raw_text = Column(Text, nullable=True)
    source_format = Column(String(20), nullable=True)  # pdf, docx, text
    parsing_confidence = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    work_experiences = relationship("WorkExperience", back_populates="candidate", cascade="all, delete-orphan")
    educations = relationship("Education", back_populates="candidate", cascade="all, delete-orphan")
    skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    certifications = relationship("Certification", back_populates="candidate", cascade="all, delete-orphan")
    projects = relationship("Project", back_populates="candidate", cascade="all, delete-orphan")
    publications = relationship("Publication", back_populates="candidate", cascade="all, delete-orphan")
    match_results = relationship("MatchResult", back_populates="candidate", cascade="all, delete-orphan")


class WorkExperience(Base):
    __tablename__ = "work_experiences"

    id = Column(String, primary_key=True, default=generate_uuid)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    company = Column(String(255), nullable=True)
    role = Column(String(255), nullable=True)
    start_date = Column(String(50), nullable=True)
    end_date = Column(String(50), nullable=True)
    duration_months = Column(Integer, nullable=True)
    responsibilities = Column(Text, nullable=True)
    is_current = Column(Boolean, default=False)

    candidate = relationship("Candidate", back_populates="work_experiences")


class Education(Base):
    __tablename__ = "educations"

    id = Column(String, primary_key=True, default=generate_uuid)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    institution = Column(String(255), nullable=True)
    degree = Column(String(255), nullable=True)
    field_of_study = Column(String(255), nullable=True)
    start_year = Column(String(10), nullable=True)
    end_year = Column(String(10), nullable=True)
    gpa = Column(String(20), nullable=True)

    candidate = relationship("Candidate", back_populates="educations")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String(255), unique=True, nullable=False)
    canonical_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=True)
    subcategory = Column(String(100), nullable=True)
    skill_type = Column(String(50), nullable=True)  # technical, soft, domain
    aliases = Column(JSON, default=list)
    parent_skill = Column(String(255), nullable=True)
    related_skills = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)


class CandidateSkill(Base):
    __tablename__ = "candidate_skills"

    id = Column(String, primary_key=True, default=generate_uuid)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    skill_name = Column(String(255), nullable=False)
    canonical_name = Column(String(255), nullable=True)
    category = Column(String(100), nullable=True)
    proficiency_level = Column(String(50), nullable=True)  # beginner, intermediate, advanced, expert
    years_of_experience = Column(Float, nullable=True)
    confidence_score = Column(Float, default=0.0)
    source = Column(String(50), nullable=True)  # explicit, inferred

    candidate = relationship("Candidate", back_populates="skills")


class Certification(Base):
    __tablename__ = "certifications"

    id = Column(String, primary_key=True, default=generate_uuid)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    name = Column(String(255), nullable=False)
    issuing_organization = Column(String(255), nullable=True)
    issue_date = Column(String(50), nullable=True)
    expiry_date = Column(String(50), nullable=True)

    candidate = relationship("Candidate", back_populates="certifications")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=generate_uuid)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    technologies = Column(JSON, default=list)
    url = Column(String(500), nullable=True)

    candidate = relationship("Candidate", back_populates="projects")


class Publication(Base):
    __tablename__ = "publications"

    id = Column(String, primary_key=True, default=generate_uuid)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    title = Column(String(500), nullable=False)
    authors = Column(Text, nullable=True)
    venue = Column(String(500), nullable=True)
    year = Column(String(10), nullable=True)
    url = Column(String(500), nullable=True)
    doi = Column(String(255), nullable=True)

    candidate = relationship("Candidate", back_populates="publications")


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id = Column(String, primary_key=True, default=generate_uuid)
    title = Column(String(255), nullable=False)
    company = Column(String(255), nullable=True)
    description = Column(Text, nullable=False)
    required_skills = Column(JSON, default=list)
    preferred_skills = Column(JSON, default=list)
    experience_min_years = Column(Integer, nullable=True)
    experience_max_years = Column(Integer, nullable=True)
    location = Column(String(255), nullable=True)
    job_type = Column(String(50), nullable=True)  # full-time, part-time, contract
    created_at = Column(DateTime, default=datetime.utcnow)


class MatchResult(Base):
    __tablename__ = "match_results"

    id = Column(String, primary_key=True, default=generate_uuid)
    candidate_id = Column(String, ForeignKey("candidates.id"), nullable=False)
    job_id = Column(String, ForeignKey("job_descriptions.id"), nullable=False)
    overall_score = Column(Float, nullable=False)
    skill_match_score = Column(Float, nullable=True)
    experience_score = Column(Float, nullable=True)
    education_score = Column(Float, nullable=True)
    matched_skills = Column(JSON, default=list)
    missing_skills = Column(JSON, default=list)
    upskilling_suggestions = Column(JSON, default=list)
    detailed_breakdown = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("Candidate", back_populates="match_results")
    job = relationship("JobDescription")


class BatchJob(Base):
    __tablename__ = "batch_jobs"

    id = Column(String, primary_key=True, default=generate_uuid)
    status = Column(String(20), default="pending")  # pending, processing, completed, failed
    total_files = Column(Integer, default=0)
    processed_files = Column(Integer, default=0)
    failed_files = Column(Integer, default=0)
    results = Column(JSON, default=list)
    error_log = Column(JSON, default=list)
    webhook_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(String, primary_key=True, default=generate_uuid)
    key = Column(String(255), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    rate_limit = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)
