import time
from typing import List, Dict, Optional
from loguru import logger

from app.models.schemas import SkillSchema, ParsedResume
from app.services.skill_taxonomy import get_taxonomy_service
from app.services.embedding_service import get_embedding_service


class NormalizationAgent:
    """Agent 2: Skill Taxonomy and Normalization Agent.

    Normalizes extracted skills against a hierarchical skill taxonomy.
    Handles synonyms, abbreviations, skill hierarchy inference, and proficiency estimation.
    """

    AGENT_NAME = "NormalizationAgent"

    def __init__(self):
        self.taxonomy_service = get_taxonomy_service()
        self.embedding_service = get_embedding_service()

    async def normalize(self, parsed_resume: ParsedResume) -> ParsedResume:
        """Normalize all skills in the parsed resume."""
        start_time = time.time()
        logger.info(f"NormalizationAgent: Normalizing {len(parsed_resume.skills)} skills")

        normalized_skills = []
        raw_skill_names = []

        # Step 1: Normalize each extracted skill
        for skill in parsed_resume.skills:
            normalized = self._normalize_single_skill(skill, parsed_resume)
            normalized_skills.append(normalized)
            raw_skill_names.append(normalized.canonical_name or normalized.name)

        # Step 2: Infer additional skills from combinations
        inferred = self.taxonomy_service.infer_skills(raw_skill_names)
        for inf in inferred:
            # Check if already in the list
            existing_names = {s.canonical_name or s.name for s in normalized_skills}
            if inf["name"] not in existing_names:
                normalized_skills.append(SkillSchema(
                    name=inf["name"],
                    canonical_name=inf["name"],
                    category=self._get_category(inf["name"]),
                    confidence_score=inf["confidence"],
                    source="inferred",
                    proficiency_level="intermediate",
                ))

        # Step 3: Detect emerging skills (not in taxonomy)
        for skill in normalized_skills:
            if skill.confidence_score <= 0.3 and skill.source != "inferred":
                logger.info(f"NormalizationAgent: Emerging skill detected: {skill.name}")
                skill.source = "emerging"

        parsed_resume.skills = normalized_skills

        duration = (time.time() - start_time) * 1000
        logger.info(f"NormalizationAgent: Normalized to {len(normalized_skills)} skills in {duration:.0f}ms")
        return parsed_resume

    def _normalize_single_skill(self, skill: SkillSchema, resume: ParsedResume) -> SkillSchema:
        """Normalize a single skill."""
        # Get canonical name from taxonomy
        canonical_name, confidence = self.taxonomy_service.normalize_skill(skill.name)

        # Get skill category info
        skill_info = self.taxonomy_service.get_skill_info(canonical_name)
        category = skill_info["category"] if skill_info else None
        skill_type = skill_info["skill_type"] if skill_info else None

        # Estimate proficiency from work experience context
        experience_context = self._get_experience_context(skill.name, resume)
        years = self._estimate_years(skill.name, resume)
        proficiency = self.taxonomy_service.estimate_proficiency(
            canonical_name, years=years, context=experience_context
        )

        return SkillSchema(
            name=skill.name,
            canonical_name=canonical_name,
            category=category or skill_type,
            proficiency_level=proficiency,
            years_of_experience=years,
            confidence_score=confidence,
            source=skill.source or "explicit",
        )

    def _get_experience_context(self, skill_name: str, resume: ParsedResume) -> str:
        """Get context about a skill from work experience descriptions."""
        context_parts = []
        skill_lower = skill_name.lower()

        for exp in resume.work_experiences:
            if exp.responsibilities and skill_lower in exp.responsibilities.lower():
                context_parts.append(exp.responsibilities)
            if exp.role and skill_lower in exp.role.lower():
                context_parts.append(f"Role: {exp.role}")

        return " ".join(context_parts[:3])  # Limit context

    def _estimate_years(self, skill_name: str, resume: ParsedResume) -> Optional[float]:
        """Estimate years of experience with a skill based on work history."""
        skill_lower = skill_name.lower()
        total_months = 0

        for exp in resume.work_experiences:
            # Check if skill is mentioned in this experience
            mentioned = False
            if exp.responsibilities and skill_lower in exp.responsibilities.lower():
                mentioned = True
            if exp.role and skill_lower in exp.role.lower():
                mentioned = True

            if mentioned and exp.duration_months:
                total_months += exp.duration_months

        if total_months > 0:
            return round(total_months / 12.0, 1)
        return None

    def _get_category(self, skill_name: str) -> Optional[str]:
        """Get category for a skill name."""
        info = self.taxonomy_service.get_skill_info(skill_name)
        return info["category"] if info else None

    async def get_skill_summary(self, skills: List[SkillSchema]) -> Dict[str, List[str]]:
        """Group skills by category for summary view."""
        summary = {}
        for skill in skills:
            cat = skill.category or "Other"
            if cat not in summary:
                summary[cat] = []
            display_name = skill.canonical_name or skill.name
            if display_name not in summary[cat]:
                summary[cat].append(display_name)
        return summary
