import json
import re
import time
from typing import Optional, Dict, Any
from loguru import logger

from app.models.schemas import (
    ParsedResume, PersonalInfo, WorkExperienceSchema,
    EducationSchema, SkillSchema, CertificationSchema, ProjectSchema, PublicationSchema
)
from app.services.pdf_parser import PDFParser
from app.services.docx_parser import DOCXParser
from app.services.text_parser import TextParser
from app.config import get_settings

settings = get_settings()


class ParsingAgent:
    """Agent 1: Multi-Format Resume Parsing Agent.

    Extracts structured information from resumes in PDF, DOCX, and plain text formats.
    Uses NLP-based section detection and LLM-powered extraction.
    """

    AGENT_NAME = "ParsingAgent"

    # Section detection patterns
    SECTION_PATTERNS = {
        "experience": r"(?i)(work\s*experience|professional\s*experience|employment|work\s*history|experience)",
        "education": r"(?i)(education|academic|qualification|degree)",
        "skills": r"(?i)(skills|technical\s*skills|core\s*competencies|technologies|proficiencies|expertise)",
        "certifications": r"(?i)(certification|certificate|licenses|accreditation)",
        "projects": r"(?i)(projects|personal\s*projects|key\s*projects|portfolio)",
        "publications": r"(?i)(publications|papers|research\s*papers|published\s*work|articles|conference\s*papers|journal\s*papers)",
        "summary": r"(?i)(summary|objective|profile|about\s*me|professional\s*summary)",
        "contact": r"(?i)(contact|personal\s*info|personal\s*details)",
    }

    # Regex patterns for contact info extraction
    EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    PHONE_PATTERN = r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"
    LINKEDIN_PATTERN = r"(?:https?://)?(?:www\.)?linkedin\.com/in/[\w-]+"

    def __init__(self):
        self.llm_client = None
        self._init_llm()

    def _init_llm(self):
        """Initialize LLM client for complex extraction."""
        try:
            from openai import OpenAI
            if settings.OPENAI_API_KEY:
                self.llm_client = OpenAI(api_key=settings.OPENAI_API_KEY)
                logger.info("ParsingAgent: LLM client initialized")
            else:
                logger.info("ParsingAgent: No API key, using rule-based parsing only")
        except Exception as e:
            logger.warning(f"ParsingAgent: Could not init LLM: {e}")

    async def parse(self, file_content: bytes, filename: str) -> ParsedResume:
        """Parse a resume file and extract structured data."""
        start_time = time.time()
        logger.info(f"ParsingAgent: Parsing {filename}")

        # Detect format and extract raw text
        source_format = self._detect_format(filename)
        raw_text = self._extract_text(file_content, source_format)

        if not raw_text:
            logger.error(f"ParsingAgent: Could not extract text from {filename}")
            return ParsedResume(source_format=source_format, parsing_confidence=0.0)

        # Parse using LLM if available, otherwise use rule-based
        if self.llm_client:
            result = await self._parse_with_llm(raw_text, source_format)
        else:
            result = self._parse_with_rules(raw_text, source_format)

        result.raw_text = raw_text
        result.source_format = source_format

        duration = (time.time() - start_time) * 1000
        logger.info(f"ParsingAgent: Parsed {filename} in {duration:.0f}ms (confidence: {result.parsing_confidence})")
        return result

    def _detect_format(self, filename: str) -> str:
        """Detect file format from filename."""
        lower = filename.lower()
        if lower.endswith(".pdf"):
            return "pdf"
        elif lower.endswith(".docx"):
            return "docx"
        elif lower.endswith(".doc"):
            return "doc"
        else:
            return "text"

    def _extract_text(self, file_content: bytes, source_format: str) -> Optional[str]:
        """Extract raw text from file content."""
        if source_format == "pdf":
            return PDFParser.extract_text(file_content)
        elif source_format in ("docx", "doc"):
            return DOCXParser.extract_text(file_content)
        else:
            return TextParser.extract_text(file_content)

    async def _parse_with_llm(self, raw_text: str, source_format: str) -> ParsedResume:
        """Use LLM for intelligent resume parsing."""
        try:
            prompt = f"""Extract structured information from this resume text. Return a valid JSON object with these fields:

{{
    "personal_info": {{
        "name": "Full Name",
        "email": "email@example.com",
        "phone": "phone number",
        "location": "City, State/Country",
        "linkedin_url": "LinkedIn URL if found",
        "summary": "Professional summary if found"
    }},
    "work_experiences": [
        {{
            "company": "Company Name",
            "role": "Job Title",
            "start_date": "Start Date",
            "end_date": "End Date or Present",
            "responsibilities": "Key responsibilities and achievements",
            "is_current": false
        }}
    ],
    "educations": [
        {{
            "institution": "University/School",
            "degree": "Degree Type",
            "field_of_study": "Major/Field",
            "start_year": "Year",
            "end_year": "Year",
            "gpa": "GPA if mentioned"
        }}
    ],
    "skills": ["skill1", "skill2"],
    "certifications": [
        {{
            "name": "Certification Name",
            "issuing_organization": "Issuer",
            "issue_date": "Date"
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "description": "Brief description",
            "technologies": ["tech1", "tech2"]
        }}
    ],
    "publications": [
        {{
            "title": "Paper Title",
            "authors": "Author1, Author2",
            "venue": "Conference or Journal Name",
            "year": "2023",
            "url": "URL if available",
            "doi": "DOI if available"
        }}
    ]
}}

Resume Text:
{raw_text[:4000]}

Return ONLY valid JSON, no other text."""

            response = self.llm_client.chat.completions.create(
                model=settings.LLM_MODEL,
                messages=[
                    {"role": "system", "content": "You are an expert resume parser. Extract structured data from resumes accurately. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=2000,
            )

            content = response.choices[0].message.content.strip()
            # Clean up markdown code blocks if present
            if content.startswith("```"):
                content = re.sub(r"^```(?:json)?\n?", "", content)
                content = re.sub(r"\n?```$", "", content)

            data = json.loads(content)
            return self._json_to_parsed_resume(data, confidence=0.9)

        except Exception as e:
            logger.warning(f"LLM parsing failed: {e}, falling back to rule-based")
            return self._parse_with_rules(raw_text, source_format)

    def _parse_with_rules(self, raw_text: str, source_format: str) -> ParsedResume:
        """Rule-based resume parsing fallback."""
        lines = raw_text.split("\n")
        lines = [l.strip() for l in lines if l.strip()]

        personal_info = self._extract_personal_info(raw_text, lines)
        sections = self._detect_sections(raw_text)
        work_experiences = self._extract_work_experience(sections.get("experience", ""))
        educations = self._extract_education(sections.get("education", ""))
        skills = self._extract_skills(sections.get("skills", ""), raw_text)
        certifications = self._extract_certifications(sections.get("certifications", ""))
        projects = self._extract_projects(sections.get("projects", ""))
        publications = self._extract_publications(sections.get("publications", ""))

        # Calculate confidence based on how much we extracted
        filled_fields = sum([
            bool(personal_info.name),
            bool(personal_info.email),
            len(work_experiences) > 0,
            len(educations) > 0,
            len(skills) > 0,
        ])
        confidence = min(filled_fields / 5.0, 1.0) * 0.7  # Max 0.7 for rule-based

        return ParsedResume(
            personal_info=personal_info,
            work_experiences=work_experiences,
            educations=educations,
            skills=[SkillSchema(name=s) for s in skills],
            certifications=certifications,
            projects=projects,
            publications=publications,
            parsing_confidence=round(confidence, 2),
        )

    def _extract_personal_info(self, raw_text: str, lines: list) -> PersonalInfo:
        """Extract personal/contact information."""
        email_match = re.search(self.EMAIL_PATTERN, raw_text)
        phone_match = re.search(self.PHONE_PATTERN, raw_text)
        linkedin_match = re.search(self.LINKEDIN_PATTERN, raw_text)

        # Name is typically the first non-empty line
        name = lines[0] if lines else None
        # If the first line looks like an email or phone, skip it
        if name and (re.match(self.EMAIL_PATTERN, name) or re.match(self.PHONE_PATTERN, name)):
            name = lines[1] if len(lines) > 1 else None

        return PersonalInfo(
            name=name,
            email=email_match.group() if email_match else None,
            phone=phone_match.group() if phone_match else None,
            linkedin_url=linkedin_match.group() if linkedin_match else None,
        )

    def _detect_sections(self, raw_text: str) -> Dict[str, str]:
        """Detect and split resume into sections."""
        sections = {}
        section_positions = []

        for section_name, pattern in self.SECTION_PATTERNS.items():
            matches = list(re.finditer(pattern, raw_text))
            for match in matches:
                section_positions.append((match.start(), section_name, match.end()))

        # Sort by position
        section_positions.sort(key=lambda x: x[0])

        # Extract text between sections
        for i, (start, name, content_start) in enumerate(section_positions):
            end = section_positions[i + 1][0] if i + 1 < len(section_positions) else len(raw_text)
            sections[name] = raw_text[content_start:end].strip()

        return sections

    def _extract_work_experience(self, section_text: str) -> list:
        """Extract work experiences from section text."""
        if not section_text:
            return []

        experiences = []
        # Split by common patterns (company names usually follow dates or bullets)
        blocks = re.split(r"\n(?=\S)", section_text)

        for block in blocks:
            if len(block.strip()) < 10:
                continue

            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue

            # Try to extract structured info from block
            date_pattern = r"(\w+\s*\d{4})\s*[-–to]+\s*(\w+\s*\d{4}|[Pp]resent|[Cc]urrent)"
            date_match = re.search(date_pattern, block)

            exp = WorkExperienceSchema(
                role=lines[0] if lines else None,
                company=lines[1] if len(lines) > 1 else None,
                start_date=date_match.group(1) if date_match else None,
                end_date=date_match.group(2) if date_match else None,
                is_current=bool(date_match and re.search(r"[Pp]resent|[Cc]urrent", date_match.group(2) or "")),
                responsibilities="\n".join(lines[2:]) if len(lines) > 2 else None,
            )
            experiences.append(exp)

        return experiences[:10]  # Limit

    def _extract_education(self, section_text: str) -> list:
        """Extract education from section text."""
        if not section_text:
            return []

        educations = []
        blocks = re.split(r"\n(?=\S)", section_text)

        for block in blocks:
            if len(block.strip()) < 10:
                continue

            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines:
                continue

            # Look for degree keywords
            degree_pattern = r"(?i)(B\.?S\.?|B\.?A\.?|M\.?S\.?|M\.?A\.?|Ph\.?D\.?|MBA|Bachelor|Master|Doctor|Associate|Diploma)"
            degree_match = re.search(degree_pattern, block)

            year_pattern = r"(20\d{2}|19\d{2})"
            years = re.findall(year_pattern, block)

            edu = EducationSchema(
                institution=lines[0] if lines else None,
                degree=degree_match.group() if degree_match else (lines[1] if len(lines) > 1 else None),
                field_of_study=lines[1] if len(lines) > 1 and not degree_match else None,
                start_year=years[0] if len(years) >= 2 else None,
                end_year=years[-1] if years else None,
            )
            educations.append(edu)

        return educations[:5]

    def _extract_skills(self, section_text: str, full_text: str) -> list:
        """Extract skills from skills section and full text."""
        skills = set()

        # From skills section
        if section_text:
            # Split by common delimiters
            raw_skills = re.split(r"[,;|•·\n]", section_text)
            for skill in raw_skills:
                cleaned = skill.strip().strip("-").strip("•").strip()
                if cleaned and len(cleaned) < 50 and not cleaned.isdigit():
                    skills.add(cleaned)

        # Common tech skills to look for in full text
        tech_keywords = [
            "Python", "Java", "JavaScript", "TypeScript", "C\\+\\+", "C#", "Go", "Rust", "Ruby", "PHP",
            "React", "Angular", "Vue", "Node\\.js", "Django", "Flask", "FastAPI", "Spring",
            "Docker", "Kubernetes", "AWS", "Azure", "GCP", "Terraform",
            "PostgreSQL", "MySQL", "MongoDB", "Redis", "Elasticsearch",
            "Machine Learning", "Deep Learning", "TensorFlow", "PyTorch",
            "Git", "Linux", "Agile", "Scrum", "REST API", "GraphQL",
            "HTML", "CSS", "SQL", "NoSQL", "Microservices",
        ]

        for keyword in tech_keywords:
            if re.search(r"\b" + keyword + r"\b", full_text, re.IGNORECASE):
                # Use the properly cased version
                clean_kw = keyword.replace("\\+", "+").replace("\\.", ".")
                skills.add(clean_kw)

        return list(skills)

    def _extract_certifications(self, section_text: str) -> list:
        """Extract certifications from section text."""
        if not section_text:
            return []

        certs = []
        lines = [l.strip() for l in section_text.split("\n") if l.strip()]

        for line in lines:
            if len(line) > 5:
                certs.append(CertificationSchema(name=line.strip("-•* ")))

        return certs[:10]

    def _extract_projects(self, section_text: str) -> list:
        """Extract projects from section text."""
        if not section_text:
            return []

        projects = []
        blocks = re.split(r"\n(?=\S)", section_text)

        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if not lines or len(lines[0]) < 3:
                continue

            projects.append(ProjectSchema(
                name=lines[0].strip("-•* "),
                description="\n".join(lines[1:]) if len(lines) > 1 else None,
            ))

        return projects[:10]

    def _extract_publications(self, section_text: str) -> list:
        """Extract publications from section text."""
        if not section_text:
            return []

        publications = []
        # Split by numbered entries or newlines that look like new entries
        entries = re.split(r"\n(?=\d+[\.\)]\s*|\[\d+\]|\•|\-\s+[A-Z])", section_text)
        if len(entries) <= 1:
            entries = [l.strip() for l in section_text.split("\n") if l.strip() and len(l.strip()) > 15]

        for entry in entries:
            entry = entry.strip().strip("-•*[] 0123456789.)")
            if len(entry) < 10:
                continue

            # Try to extract year
            year_match = re.search(r"\b(19|20)\d{2}\b", entry)
            # Try to extract DOI
            doi_match = re.search(r"(10\.\d{4,}/\S+)", entry)
            # Try to extract URL
            url_match = re.search(r"https?://\S+", entry)

            # Try splitting title from rest: often title is in quotes or before a comma/period followed by venue
            title = entry
            venue = None
            authors = None

            # Pattern: "Title", Authors, Venue, Year
            quoted = re.match(r'"([^"]+)"[,.\s]*(.*)', entry)
            if quoted:
                title = quoted.group(1)
                rest = quoted.group(2)
                parts = [p.strip() for p in rest.split(",") if p.strip()]
                if len(parts) >= 2:
                    authors = parts[0]
                    venue = parts[1]
                elif len(parts) == 1:
                    venue = parts[0]
            else:
                # Pattern: Title. Venue. Year
                dot_parts = [p.strip() for p in entry.split(".") if p.strip()]
                if len(dot_parts) >= 2:
                    title = dot_parts[0]
                    venue = dot_parts[1] if len(dot_parts) > 1 else None

            publications.append(PublicationSchema(
                title=title[:500],
                authors=authors,
                venue=venue,
                year=year_match.group() if year_match else None,
                url=url_match.group() if url_match else None,
                doi=doi_match.group(1) if doi_match else None,
            ))

        return publications[:20]

    def _json_to_parsed_resume(self, data: dict, confidence: float) -> ParsedResume:
        """Convert LLM JSON output to ParsedResume schema."""
        pi = data.get("personal_info", {})
        personal_info = PersonalInfo(**{k: v for k, v in pi.items() if k in PersonalInfo.model_fields})

        work_experiences = []
        for we in data.get("work_experiences", []):
            work_experiences.append(WorkExperienceSchema(**{k: v for k, v in we.items() if k in WorkExperienceSchema.model_fields}))

        educations = []
        for edu in data.get("educations", []):
            educations.append(EducationSchema(**{k: v for k, v in edu.items() if k in EducationSchema.model_fields}))

        skills = []
        for s in data.get("skills", []):
            if isinstance(s, str):
                skills.append(SkillSchema(name=s))
            elif isinstance(s, dict):
                skills.append(SkillSchema(**{k: v for k, v in s.items() if k in SkillSchema.model_fields}))

        certifications = []
        for c in data.get("certifications", []):
            if isinstance(c, str):
                certifications.append(CertificationSchema(name=c))
            elif isinstance(c, dict):
                certifications.append(CertificationSchema(**{k: v for k, v in c.items() if k in CertificationSchema.model_fields}))

        projects = []
        for p in data.get("projects", []):
            if isinstance(p, str):
                projects.append(ProjectSchema(name=p))
            elif isinstance(p, dict):
                projects.append(ProjectSchema(**{k: v for k, v in p.items() if k in ProjectSchema.model_fields}))

        publications = []
        for pub in data.get("publications", []):
            if isinstance(pub, str):
                publications.append(PublicationSchema(title=pub))
            elif isinstance(pub, dict):
                publications.append(PublicationSchema(**{k: v for k, v in pub.items() if k in PublicationSchema.model_fields}))

        return ParsedResume(
            personal_info=personal_info,
            work_experiences=work_experiences,
            educations=educations,
            skills=skills,
            certifications=certifications,
            projects=projects,
            publications=publications,
            parsing_confidence=confidence,
        )
