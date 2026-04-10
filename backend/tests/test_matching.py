import pytest
import asyncio
from app.agents.matching_agent import MatchingAgent
from app.models.schemas import (
    ParsedResume, PersonalInfo, SkillSchema,
    WorkExperienceSchema, EducationSchema, JobDescriptionRequest
)


@pytest.fixture
def matching_agent():
    return MatchingAgent()


@pytest.fixture
def sample_candidate():
    return ParsedResume(
        personal_info=PersonalInfo(name="John Doe"),
        skills=[
            SkillSchema(name="Python", canonical_name="Python", category="Programming Languages"),
            SkillSchema(name="Docker", canonical_name="Docker", category="DevOps & Infrastructure"),
            SkillSchema(name="AWS", canonical_name="Amazon Web Services", category="Cloud Platforms"),
            SkillSchema(name="PostgreSQL", canonical_name="PostgreSQL", category="Databases"),
            SkillSchema(name="React", canonical_name="React", category="Web Frameworks"),
        ],
        work_experiences=[
            WorkExperienceSchema(
                company="TechCorp",
                role="Software Engineer",
                duration_months=36,
            ),
        ],
        educations=[
            EducationSchema(
                institution="MIT",
                degree="Bachelor of Science",
                field_of_study="Computer Science",
            ),
        ],
    )


@pytest.fixture
def sample_job():
    return JobDescriptionRequest(
        title="Software Engineer",
        description="Looking for a software engineer",
        required_skills=["Python", "Docker", "PostgreSQL"],
        preferred_skills=["AWS", "Kubernetes"],
        experience_min_years=3,
    )


def test_match_strong_candidate(matching_agent, sample_candidate, sample_job):
    """Test matching a strong candidate."""
    result = asyncio.get_event_loop().run_until_complete(
        matching_agent.match(sample_candidate, sample_job)
    )

    assert result["overall_score"] > 0.5
    assert result["skill_match_score"] > 0.5
    assert len(result["matched_skills"]) > 0
    assert result["recommendation"] != ""


def test_match_weak_candidate(matching_agent, sample_job):
    """Test matching a weak candidate."""
    weak_candidate = ParsedResume(
        personal_info=PersonalInfo(name="Jane Doe"),
        skills=[
            SkillSchema(name="HTML", canonical_name="HTML"),
            SkillSchema(name="CSS", canonical_name="CSS"),
        ],
        work_experiences=[],
        educations=[],
    )

    result = asyncio.get_event_loop().run_until_complete(
        matching_agent.match(weak_candidate, sample_job)
    )

    assert result["overall_score"] < 0.7
    assert len(result["missing_skills"]) > 0


def test_gap_analysis(matching_agent, sample_candidate, sample_job):
    """Test gap analysis generation."""
    result = asyncio.get_event_loop().run_until_complete(
        matching_agent.match(sample_candidate, sample_job)
    )

    gap = result["gap_analysis"]
    assert hasattr(gap, "missing_skills")
    assert hasattr(gap, "upskilling_suggestions")


def test_experience_scoring(matching_agent, sample_candidate, sample_job):
    """Test experience scoring."""
    score = matching_agent._score_experience(sample_candidate, sample_job)
    assert 0.0 <= score <= 1.0


def test_education_scoring(matching_agent, sample_candidate, sample_job):
    """Test education scoring."""
    score = matching_agent._score_education(sample_candidate, sample_job)
    assert 0.0 <= score <= 1.0
    assert score >= 0.7  # Bachelor's degree
