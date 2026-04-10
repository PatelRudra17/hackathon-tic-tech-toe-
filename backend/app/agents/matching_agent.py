import time
from typing import List, Dict, Optional
from loguru import logger

from app.models.schemas import (
    SkillSchema, MatchResponse, SkillMatchDetail,
    GapAnalysis, JobDescriptionRequest, ParsedResume
)
from app.services.embedding_service import get_embedding_service
from app.services.skill_taxonomy import get_taxonomy_service


class MatchingAgent:
    """Agent 3: Semantic Skill-to-Job Matching Agent.

    Performs semantic similarity matching between candidate skill profiles
    and job requirements. Goes beyond keyword matching using embeddings.
    """

    AGENT_NAME = "MatchingAgent"

    # Weights for scoring
    SKILL_WEIGHT = 0.50
    EXPERIENCE_WEIGHT = 0.30
    EDUCATION_WEIGHT = 0.20

    def __init__(self):
        self.embedding_service = get_embedding_service()
        self.taxonomy_service = get_taxonomy_service()

    async def match(
        self,
        parsed_resume: ParsedResume,
        job: JobDescriptionRequest,
        threshold: float = 0.5,
    ) -> Dict:
        """Match a candidate's profile against a job description."""
        start_time = time.time()
        logger.info(f"MatchingAgent: Matching candidate against '{job.title}'")

        # Step 1: Skill matching
        skill_match_result = self._match_skills(parsed_resume.skills, job)

        # Step 2: Experience scoring
        experience_score = self._score_experience(parsed_resume, job)

        # Step 3: Education scoring
        education_score = self._score_education(parsed_resume, job)

        # Step 4: Calculate overall score
        overall_score = (
            skill_match_result["score"] * self.SKILL_WEIGHT +
            experience_score * self.EXPERIENCE_WEIGHT +
            education_score * self.EDUCATION_WEIGHT
        )

        # Step 5: Gap analysis
        gap_analysis = self._analyze_gaps(
            parsed_resume.skills, job, skill_match_result["unmatched_job_skills"]
        )

        # Step 6: Generate recommendation
        recommendation = self._generate_recommendation(overall_score, threshold)

        duration = (time.time() - start_time) * 1000
        logger.info(f"MatchingAgent: Match score {overall_score:.2f} in {duration:.0f}ms")

        return {
            "overall_score": round(overall_score, 3),
            "skill_match_score": round(skill_match_result["score"], 3),
            "experience_score": round(experience_score, 3),
            "education_score": round(education_score, 3),
            "matched_skills": skill_match_result["matched_skills"],
            "missing_skills": skill_match_result["unmatched_job_skills"],
            "gap_analysis": gap_analysis,
            "recommendation": recommendation,
            "processing_time_ms": round(duration, 1),
            "detailed_breakdown": {
                "skill_weight": self.SKILL_WEIGHT,
                "experience_weight": self.EXPERIENCE_WEIGHT,
                "education_weight": self.EDUCATION_WEIGHT,
                "required_skills_matched": skill_match_result["required_matched"],
                "required_skills_total": len(job.required_skills),
                "preferred_skills_matched": skill_match_result["preferred_matched"],
                "preferred_skills_total": len(job.preferred_skills),
            },
        }

    def _match_skills(self, candidate_skills: List[SkillSchema], job: JobDescriptionRequest) -> Dict:
        """Match candidate skills against job requirements using multi-strategy matching."""
        candidate_skill_names = [s.canonical_name or s.name for s in candidate_skills]
        candidate_skill_lower = {s.lower() for s in candidate_skill_names}

        all_job_skills = []
        skill_importance = {}  # skill -> weight

        for s in job.required_skills:
            all_job_skills.append(s)
            skill_importance[s] = 1.0  # Required = full weight

        for s in job.preferred_skills:
            all_job_skills.append(s)
            skill_importance[s] = 0.5  # Nice-to-have = half weight

        if not all_job_skills:
            return {
                "score": 0.5,
                "matched_skills": [],
                "unmatched_job_skills": [],
                "required_matched": 0,
                "preferred_matched": 0,
            }

        matched_skills = []
        unmatched = []
        required_matched = 0
        preferred_matched = 0

        # Strategy 1: Direct match (exact or canonical)
        # Strategy 2: Semantic embedding match
        semantic_matches = self.embedding_service.compute_skill_similarity(
            candidate_skill_names, all_job_skills
        )

        for i, job_skill in enumerate(all_job_skills):
            job_lower = job_skill.lower()
            importance = skill_importance[job_skill]

            # Check direct match
            canonical, conf = self.taxonomy_service.normalize_skill(job_skill)
            canonical_lower = canonical.lower()

            direct_match = (
                job_lower in candidate_skill_lower or
                canonical_lower in candidate_skill_lower
            )

            if direct_match:
                matched_skills.append(SkillMatchDetail(
                    skill=job_skill,
                    match_type="direct",
                    confidence=1.0,
                    job_requirement="required" if importance == 1.0 else "preferred",
                ))
                if importance == 1.0:
                    required_matched += 1
                else:
                    preferred_matched += 1
                continue

            # Check semantic match
            sem_match = semantic_matches[i] if i < len(semantic_matches) else None
            if sem_match and sem_match["similarity_score"] >= 0.6:
                match_type = sem_match["match_type"]
                matched_skills.append(SkillMatchDetail(
                    skill=job_skill,
                    match_type=match_type,
                    confidence=sem_match["similarity_score"],
                    job_requirement="required" if importance == 1.0 else "preferred",
                ))
                if importance == 1.0:
                    required_matched += 1
                else:
                    preferred_matched += 1
                continue

            # No match
            unmatched.append(job_skill)

        # Calculate weighted score
        total_weight = sum(skill_importance.values())
        matched_weight = sum(
            skill_importance.get(m.skill, 0.5) * m.confidence
            for m in matched_skills
        )
        score = matched_weight / total_weight if total_weight > 0 else 0.0

        return {
            "score": min(score, 1.0),
            "matched_skills": matched_skills,
            "unmatched_job_skills": unmatched,
            "required_matched": required_matched,
            "preferred_matched": preferred_matched,
        }

    def _score_experience(self, resume: ParsedResume, job: JobDescriptionRequest) -> float:
        """Score candidate's experience relevance."""
        if not resume.work_experiences:
            return 0.2

        # Calculate total years of experience
        total_months = 0
        for exp in resume.work_experiences:
            if exp.duration_months:
                total_months += exp.duration_months
            else:
                # Estimate ~24 months per position if duration unknown
                total_months += 24

        total_years = total_months / 12.0

        # Score based on required years
        min_years = job.experience_min_years or 0
        max_years = job.experience_max_years or 20

        if total_years >= min_years:
            if total_years <= max_years:
                return 1.0  # Perfect range
            else:
                return 0.85  # Overqualified but still good
        else:
            # Partial credit
            return max(0.2, total_years / min_years) if min_years > 0 else 0.5

    def _score_education(self, resume: ParsedResume, job: JobDescriptionRequest) -> float:
        """Score candidate's education relevance."""
        if not resume.educations:
            return 0.3

        # Degree hierarchy scoring
        degree_scores = {
            "phd": 1.0, "doctorate": 1.0, "doctor": 1.0,
            "master": 0.9, "mba": 0.9, "ms": 0.9, "ma": 0.9,
            "bachelor": 0.7, "bs": 0.7, "ba": 0.7, "bsc": 0.7,
            "associate": 0.5, "diploma": 0.4,
        }

        best_score = 0.3
        for edu in resume.educations:
            if edu.degree:
                degree_lower = edu.degree.lower()
                for key, score in degree_scores.items():
                    if key in degree_lower:
                        best_score = max(best_score, score)
                        break

        return best_score

    def _analyze_gaps(
        self,
        candidate_skills: List[SkillSchema],
        job: JobDescriptionRequest,
        missing_skills: List[str],
    ) -> GapAnalysis:
        """Identify skill gaps and suggest upskilling paths."""
        suggestions = []

        for missing in missing_skills:
            # Find related skills the candidate already has
            skill_info = self.taxonomy_service.get_skill_info(missing)
            related = skill_info["related_skills"] if skill_info else []

            candidate_names = {(s.canonical_name or s.name).lower() for s in candidate_skills}
            has_related = [r for r in related if r.lower() in candidate_names]

            if has_related:
                suggestion = {
                    "missing_skill": missing,
                    "suggestion": f"You already know {', '.join(has_related[:2])}. Learning {missing} would be a natural next step.",
                    "difficulty": "moderate",
                }
            else:
                suggestion = {
                    "missing_skill": missing,
                    "suggestion": f"Consider taking a course or certification in {missing}.",
                    "difficulty": "significant",
                }

            suggestions.append(suggestion)

        return GapAnalysis(
            missing_skills=missing_skills,
            upskilling_suggestions=suggestions,
        )

    def _generate_recommendation(self, score: float, threshold: float) -> str:
        """Generate a human-readable recommendation."""
        if score >= 0.85:
            return "Strong Match - Highly recommended for this position. Candidate meets most requirements."
        elif score >= 0.7:
            return "Good Match - Candidate has strong relevant skills with minor gaps that can be addressed."
        elif score >= threshold:
            return "Moderate Match - Candidate meets basic requirements but has notable skill gaps."
        elif score >= 0.3:
            return "Weak Match - Significant skill gaps exist. Consider for junior roles or with training plan."
        else:
            return "Poor Match - Candidate's profile does not align well with this position's requirements."
