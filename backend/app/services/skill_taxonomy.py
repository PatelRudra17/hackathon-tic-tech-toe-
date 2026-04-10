import json
import os
from typing import Dict, List, Optional, Tuple
from loguru import logger


class SkillTaxonomyService:
    """Manages hierarchical skill taxonomy with synonym resolution and hierarchy inference."""

    def __init__(self):
        self.taxonomy: Dict = {}
        self.skill_lookup: Dict[str, Dict] = {}  # lowercase alias -> skill info
        self.canonical_names: Dict[str, str] = {}  # lowercase variant -> canonical name
        self.skill_hierarchy: Dict[str, Dict] = {}  # canonical name -> {category, subcategory, type}
        self.related_skills_map: Dict[str, List[str]] = {}
        self._load_taxonomy()

    def _load_taxonomy(self):
        taxonomy_path = os.path.join(os.path.dirname(__file__), "..", "data", "skill_taxonomy.json")
        try:
            with open(taxonomy_path, "r", encoding="utf-8") as f:
                self.taxonomy = json.load(f)
            self._build_lookup_tables()
            logger.info(f"Loaded skill taxonomy with {len(self.canonical_names)} skill mappings")
        except FileNotFoundError:
            logger.warning(f"Skill taxonomy file not found at {taxonomy_path}")
            self.taxonomy = {}

    def _build_lookup_tables(self):
        for skill_type, categories in self.taxonomy.items():
            for category, data in categories.items():
                for skill in data.get("skills", []):
                    name = skill["name"]
                    canonical_lower = name.lower()

                    # Map canonical name
                    self.canonical_names[canonical_lower] = name
                    self.skill_hierarchy[name] = {
                        "category": category,
                        "skill_type": skill_type,
                        "parent": skill_type,
                        "subcategory": category,
                    }

                    # Map all aliases
                    for alias in skill.get("aliases", []):
                        self.canonical_names[alias.lower()] = name

                    # Map related skills
                    self.related_skills_map[name] = skill.get("related", [])

    def normalize_skill(self, raw_skill: str) -> Tuple[str, float]:
        """Normalize a raw skill string to its canonical form.
        Returns (canonical_name, confidence_score)."""
        if not raw_skill:
            return raw_skill, 0.0

        raw_lower = raw_skill.strip().lower()

        # Direct match
        if raw_lower in self.canonical_names:
            return self.canonical_names[raw_lower], 1.0

        # Partial match - check if raw skill contains or is contained in any known skill
        best_match = None
        best_score = 0.0

        for known_lower, canonical in self.canonical_names.items():
            if known_lower in raw_lower or raw_lower in known_lower:
                # Score based on length similarity
                score = min(len(raw_lower), len(known_lower)) / max(len(raw_lower), len(known_lower))
                if score > best_score and score > 0.6:
                    best_match = canonical
                    best_score = score

        if best_match:
            return best_match, round(best_score, 2)

        # No match found - return as-is (emerging skill)
        return raw_skill.strip(), 0.3

    def get_skill_info(self, canonical_name: str) -> Optional[Dict]:
        """Get full information about a skill."""
        hierarchy = self.skill_hierarchy.get(canonical_name)
        if hierarchy:
            return {
                "name": canonical_name,
                "category": hierarchy["subcategory"],
                "skill_type": hierarchy["skill_type"],
                "related_skills": self.related_skills_map.get(canonical_name, []),
            }
        return None

    def infer_skills(self, skills: List[str]) -> List[Dict]:
        """Infer additional skills based on skill relationships.
        E.g., TensorFlow + PyTorch implies Deep Learning proficiency."""
        inferred = []
        normalized_skills = {s.lower() for s in skills}
        already_added = set()

        inference_rules = [
            {
                "if_has": ["tensorflow", "pytorch"],
                "then": "Deep Learning",
                "confidence": 0.9,
            },
            {
                "if_has": ["react", "redux"],
                "then": "Frontend Development",
                "confidence": 0.85,
            },
            {
                "if_has": ["docker", "kubernetes"],
                "then": "Container Orchestration",
                "confidence": 0.9,
            },
            {
                "if_has": ["python", "pandas", "numpy"],
                "then": "Data Analysis",
                "confidence": 0.85,
            },
            {
                "if_has": ["aws", "terraform"],
                "then": "Cloud Infrastructure",
                "confidence": 0.85,
            },
            {
                "if_has": ["machine learning", "python"],
                "then": "ML Engineering",
                "confidence": 0.8,
            },
            {
                "if_has": ["java", "spring boot"],
                "then": "Backend Development",
                "confidence": 0.85,
            },
            {
                "if_has": ["nlp", "transformers"],
                "then": "Natural Language Processing",
                "confidence": 0.9,
            },
            {
                "if_has": ["spark", "kafka"],
                "then": "Big Data Engineering",
                "confidence": 0.85,
            },
            {
                "if_has": ["git", "jenkins"],
                "then": "CI/CD",
                "confidence": 0.8,
            },
        ]

        for rule in inference_rules:
            required = {s.lower() for s in rule["if_has"]}
            # Check if candidate has normalized versions of required skills
            matched = all(
                any(self.canonical_names.get(r, r).lower() in normalized_skills
                    or r in normalized_skills
                    for r_alias in [r])
                for r in required
            )

            # Simpler check: see if the required skill names appear in normalized skills
            has_all = True
            for req in required:
                found = False
                for ns in normalized_skills:
                    canonical = self.canonical_names.get(ns, ns)
                    if req == ns or req == canonical.lower():
                        found = True
                        break
                if not found:
                    has_all = False
                    break

            if has_all and rule["then"] not in already_added:
                inferred.append({
                    "name": rule["then"],
                    "confidence": rule["confidence"],
                    "source": "inferred",
                    "reason": f"Inferred from: {', '.join(rule['if_has'])}",
                })
                already_added.add(rule["then"])

        return inferred

    def estimate_proficiency(self, skill_name: str, years: Optional[float] = None, context: str = "") -> str:
        """Estimate proficiency level based on years of experience and context clues."""
        context_lower = context.lower()

        # Check context clues first
        expert_keywords = ["expert", "architect", "lead", "principal", "extensive", "advanced"]
        intermediate_keywords = ["proficient", "experienced", "solid", "strong", "good"]
        beginner_keywords = ["familiar", "basic", "beginner", "learning", "exposure", "some"]

        for kw in expert_keywords:
            if kw in context_lower:
                return "expert"
        for kw in beginner_keywords:
            if kw in context_lower:
                return "beginner"
        for kw in intermediate_keywords:
            if kw in context_lower:
                return "intermediate"

        # Fall back to years of experience
        if years is not None:
            if years >= 5:
                return "expert"
            elif years >= 3:
                return "advanced"
            elif years >= 1:
                return "intermediate"
            else:
                return "beginner"

        return "intermediate"  # default

    def get_taxonomy_tree(self) -> Dict:
        """Return the full taxonomy as a structured tree."""
        result = {}
        for skill_type, categories in self.taxonomy.items():
            result[skill_type] = {}
            for category, data in categories.items():
                result[skill_type][category] = [s["name"] for s in data.get("skills", [])]
        return result

    def search_skills(self, query: str, limit: int = 20) -> List[Dict]:
        """Search skills by name or alias."""
        query_lower = query.lower()
        results = []
        seen = set()

        for skill_type, categories in self.taxonomy.items():
            for category, data in categories.items():
                for skill in data.get("skills", []):
                    name = skill["name"]
                    if name in seen:
                        continue

                    # Check name and aliases
                    match = False
                    if query_lower in name.lower():
                        match = True
                    else:
                        for alias in skill.get("aliases", []):
                            if query_lower in alias.lower():
                                match = True
                                break

                    if match:
                        seen.add(name)
                        results.append({
                            "name": name,
                            "category": category,
                            "skill_type": skill_type,
                            "aliases": skill.get("aliases", []),
                            "related_skills": skill.get("related", []),
                        })

                    if len(results) >= limit:
                        return results

        return results

    def get_all_skills_flat(self) -> List[str]:
        """Return all canonical skill names as a flat list."""
        return list(self.skill_hierarchy.keys())


# Singleton instance
_taxonomy_service = None


def get_taxonomy_service() -> SkillTaxonomyService:
    global _taxonomy_service
    if _taxonomy_service is None:
        _taxonomy_service = SkillTaxonomyService()
    return _taxonomy_service
