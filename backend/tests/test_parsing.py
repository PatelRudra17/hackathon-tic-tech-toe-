import pytest
import asyncio
from app.agents.parsing_agent import ParsingAgent


@pytest.fixture
def parsing_agent():
    return ParsingAgent()


@pytest.fixture
def sample_resume_text():
    return b"""John Doe
john.doe@email.com
+1 (555) 123-4567
San Francisco, CA

PROFESSIONAL SUMMARY
Experienced software engineer with 5 years of experience in Python and cloud technologies.

WORK EXPERIENCE

Software Engineer | TechCorp
January 2020 - Present
- Built microservices using Python and FastAPI
- Deployed applications on AWS using Docker and Kubernetes
- Implemented CI/CD pipelines with GitHub Actions

Junior Developer | StartupXYZ
June 2018 - December 2019
- Developed web applications using React and Node.js
- Wrote unit tests with Jest and pytest

EDUCATION

Bachelor of Science in Computer Science
MIT, 2014 - 2018
GPA: 3.8

SKILLS
Python, JavaScript, React, Docker, Kubernetes, AWS, PostgreSQL, Git, FastAPI, Node.js, REST API, Agile

CERTIFICATIONS
- AWS Solutions Architect Associate
- Certified Kubernetes Administrator

PUBLICATIONS
- "Optimizing Microservice Latency at Scale", IEEE Cloud Computing, 2022
- "Efficient Container Orchestration Patterns", ACM Computing Surveys, 2021
"""


def test_parse_text_resume(parsing_agent, sample_resume_text):
    """Test parsing a plain text resume."""
    result = asyncio.get_event_loop().run_until_complete(
        parsing_agent.parse(sample_resume_text, "resume.txt")
    )

    assert result is not None
    assert result.source_format == "text"
    assert result.personal_info.name is not None
    assert result.personal_info.email == "john.doe@email.com"
    assert len(result.skills) > 0
    assert result.parsing_confidence > 0
    assert len(result.publications) > 0


def test_detect_format(parsing_agent):
    """Test file format detection."""
    assert parsing_agent._detect_format("resume.pdf") == "pdf"
    assert parsing_agent._detect_format("resume.docx") == "docx"
    assert parsing_agent._detect_format("resume.txt") == "text"
    assert parsing_agent._detect_format("resume.doc") == "doc"


def test_extract_personal_info(parsing_agent):
    """Test personal info extraction."""
    raw_text = "John Doe\njohn@email.com\n+1 555-123-4567\nlinkedin.com/in/johndoe"
    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
    info = parsing_agent._extract_personal_info(raw_text, lines)

    assert info.name == "John Doe"
    assert info.email == "john@email.com"
    assert info.phone is not None


def test_extract_skills(parsing_agent):
    """Test skill extraction."""
    section_text = "Python, JavaScript, React, Docker, AWS, Kubernetes"
    full_text = "I have experience with Python, JavaScript, React, Docker, AWS, and Kubernetes."

    skills = parsing_agent._extract_skills(section_text, full_text)
    assert len(skills) > 0
    assert "Python" in skills or "python" in [s.lower() for s in skills]
