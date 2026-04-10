"""Initial schema — all tables

Revision ID: 001
Revises: None
Create Date: 2026-04-10
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Candidates
    op.create_table(
        "candidates",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("linkedin_url", sa.String(500), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("source_format", sa.String(20), nullable=True),
        sa.Column("parsing_confidence", sa.Float(), default=0.0),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
    )

    # Work Experiences
    op.create_table(
        "work_experiences",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("candidate_id", sa.String(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("role", sa.String(255), nullable=True),
        sa.Column("start_date", sa.String(50), nullable=True),
        sa.Column("end_date", sa.String(50), nullable=True),
        sa.Column("duration_months", sa.Integer(), nullable=True),
        sa.Column("responsibilities", sa.Text(), nullable=True),
        sa.Column("is_current", sa.Boolean(), default=False),
    )

    # Educations
    op.create_table(
        "educations",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("candidate_id", sa.String(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("institution", sa.String(255), nullable=True),
        sa.Column("degree", sa.String(255), nullable=True),
        sa.Column("field_of_study", sa.String(255), nullable=True),
        sa.Column("start_year", sa.String(10), nullable=True),
        sa.Column("end_year", sa.String(10), nullable=True),
        sa.Column("gpa", sa.String(20), nullable=True),
    )

    # Skills
    op.create_table(
        "skills",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(255), unique=True, nullable=False),
        sa.Column("canonical_name", sa.String(255), nullable=False),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("subcategory", sa.String(100), nullable=True),
        sa.Column("skill_type", sa.String(50), nullable=True),
        sa.Column("aliases", sa.JSON(), default=[]),
        sa.Column("parent_skill", sa.String(255), nullable=True),
        sa.Column("related_skills", sa.JSON(), default=[]),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # Candidate Skills
    op.create_table(
        "candidate_skills",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("candidate_id", sa.String(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("skill_name", sa.String(255), nullable=False),
        sa.Column("canonical_name", sa.String(255), nullable=True),
        sa.Column("category", sa.String(100), nullable=True),
        sa.Column("proficiency_level", sa.String(50), nullable=True),
        sa.Column("years_of_experience", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Float(), default=0.0),
        sa.Column("source", sa.String(50), nullable=True),
    )

    # Certifications
    op.create_table(
        "certifications",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("candidate_id", sa.String(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("issuing_organization", sa.String(255), nullable=True),
        sa.Column("issue_date", sa.String(50), nullable=True),
        sa.Column("expiry_date", sa.String(50), nullable=True),
    )

    # Projects
    op.create_table(
        "projects",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("candidate_id", sa.String(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("technologies", sa.JSON(), default=[]),
        sa.Column("url", sa.String(500), nullable=True),
    )

    # Publications
    op.create_table(
        "publications",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("candidate_id", sa.String(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("authors", sa.Text(), nullable=True),
        sa.Column("venue", sa.String(500), nullable=True),
        sa.Column("year", sa.String(10), nullable=True),
        sa.Column("url", sa.String(500), nullable=True),
        sa.Column("doi", sa.String(255), nullable=True),
    )

    # Job Descriptions
    op.create_table(
        "job_descriptions",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("company", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("required_skills", sa.JSON(), default=[]),
        sa.Column("preferred_skills", sa.JSON(), default=[]),
        sa.Column("experience_min_years", sa.Integer(), nullable=True),
        sa.Column("experience_max_years", sa.Integer(), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("job_type", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # Match Results
    op.create_table(
        "match_results",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("candidate_id", sa.String(), sa.ForeignKey("candidates.id"), nullable=False),
        sa.Column("job_id", sa.String(), sa.ForeignKey("job_descriptions.id"), nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("skill_match_score", sa.Float(), nullable=True),
        sa.Column("experience_score", sa.Float(), nullable=True),
        sa.Column("education_score", sa.Float(), nullable=True),
        sa.Column("matched_skills", sa.JSON(), default=[]),
        sa.Column("missing_skills", sa.JSON(), default=[]),
        sa.Column("upskilling_suggestions", sa.JSON(), default=[]),
        sa.Column("detailed_breakdown", sa.JSON(), default={}),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )

    # Batch Jobs
    op.create_table(
        "batch_jobs",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("status", sa.String(20), default="pending"),
        sa.Column("total_files", sa.Integer(), default=0),
        sa.Column("processed_files", sa.Integer(), default=0),
        sa.Column("failed_files", sa.Integer(), default=0),
        sa.Column("results", sa.JSON(), default=[]),
        sa.Column("error_log", sa.JSON(), default=[]),
        sa.Column("webhook_url", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    # API Keys
    op.create_table(
        "api_keys",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("key", sa.String(255), unique=True, nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("rate_limit", sa.Integer(), default=100),
        sa.Column("created_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("api_keys")
    op.drop_table("batch_jobs")
    op.drop_table("match_results")
    op.drop_table("job_descriptions")
    op.drop_table("publications")
    op.drop_table("projects")
    op.drop_table("certifications")
    op.drop_table("candidate_skills")
    op.drop_table("skills")
    op.drop_table("educations")
    op.drop_table("work_experiences")
    op.drop_table("candidates")
