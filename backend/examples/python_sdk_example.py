"""
Talent Intelligence API — Python SDK Example
=============================================

This module demonstrates how to integrate with the Talent Intelligence
REST API from Python. It covers every endpoint: resume parsing (single
and batch), candidate retrieval, job matching, and skill taxonomy.

Requirements:
    pip install httpx

Usage:
    python python_sdk_example.py
"""

import httpx
import asyncio
import json
import time
from pathlib import Path

BASE_URL = "http://localhost:8000"
API_KEY = "dev-api-key-change-in-production"

HEADERS = {
    "X-API-Key": API_KEY,
}


class TalentIntelligenceClient:
    """Python SDK client for the Talent Intelligence API."""

    def __init__(self, base_url: str = BASE_URL, api_key: str = API_KEY):
        self.base_url = base_url.rstrip("/")
        self.headers = {"X-API-Key": api_key}

    # ── Health ──

    async def health_check(self) -> dict:
        """Check API health status."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.base_url}/health")
            resp.raise_for_status()
            return resp.json()

    # ── Resume Parsing ──

    async def parse_resume(self, file_path: str) -> dict:
        """Parse a single resume file.

        Args:
            file_path: Path to the resume file (PDF, DOCX, or TXT).

        Returns:
            Parsed resume data with candidate_id.
        """
        path = Path(file_path)
        async with httpx.AsyncClient(timeout=60) as client:
            with open(path, "rb") as f:
                resp = await client.post(
                    f"{self.base_url}/api/v1/parse",
                    headers=self.headers,
                    files={"file": (path.name, f, "application/octet-stream")},
                )
            resp.raise_for_status()
            return resp.json()

    async def parse_batch(
        self, file_paths: list[str], webhook_url: str = None
    ) -> dict:
        """Parse multiple resumes in a batch.

        Args:
            file_paths: List of paths to resume files.
            webhook_url: Optional URL to receive callback when done.

        Returns:
            Batch job info with batch_id for tracking.
        """
        files = []
        for fp in file_paths:
            path = Path(fp)
            files.append(("files", (path.name, open(path, "rb"), "application/octet-stream")))

        params = {}
        if webhook_url:
            params["webhook_url"] = webhook_url

        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/parse/batch",
                headers=self.headers,
                files=files,
                params=params,
            )
            resp.raise_for_status()

        # Close opened files
        for _, (_, fobj, _) in files:
            fobj.close()

        return resp.json()

    async def get_batch_status(self, batch_id: str) -> dict:
        """Check the status of a batch parsing job."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/parse/batch/{batch_id}",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def poll_batch(self, batch_id: str, interval: int = 3, timeout: int = 300) -> dict:
        """Poll batch status until completed or timeout."""
        start = time.time()
        while time.time() - start < timeout:
            status = await self.get_batch_status(batch_id)
            if status["status"] in ("completed", "failed"):
                return status
            await asyncio.sleep(interval)
        raise TimeoutError(f"Batch {batch_id} did not complete within {timeout}s")

    # ── Candidates ──

    async def get_candidate(self, candidate_id: str) -> dict:
        """Retrieve full parsed profile for a candidate."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/candidates/{candidate_id}",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def get_candidate_skills(self, candidate_id: str) -> dict:
        """Retrieve normalized skill profile for a candidate."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/candidates/{candidate_id}/skills",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def list_candidates(self) -> dict:
        """List all parsed candidates."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/candidates",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    # ── Job Matching ──

    async def create_job(self, job_data: dict) -> dict:
        """Store a job description.

        Args:
            job_data: Dict with title, description, required_skills, etc.
        """
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/jobs",
                headers=self.headers,
                json=job_data,
            )
            resp.raise_for_status()
            return resp.json()

    async def match(
        self,
        candidate_id: str,
        job_id: str = None,
        job_description: dict = None,
        threshold: float = 0.5,
    ) -> dict:
        """Match a candidate against a job description.

        Args:
            candidate_id: ID of the candidate (from parse_resume).
            job_id: ID of a previously stored job, OR
            job_description: Inline job description dict.
            threshold: Match score threshold (0.0 to 1.0).
        """
        payload = {
            "candidate_id": candidate_id,
            "matching_threshold": threshold,
        }
        if job_id:
            payload["job_id"] = job_id
        elif job_description:
            payload["job_description"] = job_description

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(
                f"{self.base_url}/api/v1/match",
                headers=self.headers,
                json=payload,
            )
            resp.raise_for_status()
            return resp.json()

    # ── Skill Taxonomy ──

    async def get_taxonomy(self) -> dict:
        """Browse the full skill taxonomy."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/skills/taxonomy",
                headers=self.headers,
            )
            resp.raise_for_status()
            return resp.json()

    async def search_skills(self, query: str, limit: int = 20) -> dict:
        """Search skills by name or alias."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/skills/search",
                headers=self.headers,
                params={"q": query, "limit": limit},
            )
            resp.raise_for_status()
            return resp.json()

    async def normalize_skill(self, skill: str) -> dict:
        """Map a raw skill name to its canonical form."""
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.base_url}/api/v1/skills/normalize",
                headers=self.headers,
                params={"skill": skill},
            )
            resp.raise_for_status()
            return resp.json()


# ── Example Usage ──

async def main():
    client = TalentIntelligenceClient()

    # 1. Health check
    print("=== Health Check ===")
    health = await client.health_check()
    print(json.dumps(health, indent=2))

    # 2. Parse a single resume
    print("\n=== Parse Resume ===")
    result = await client.parse_resume("app/data/sample_resumes/sample_resume_1.txt")
    candidate_id = result["candidate_id"]
    print(f"Candidate ID: {candidate_id}")
    print(f"Name: {result['parsed_data']['personal_info']['name']}")
    print(f"Skills: {len(result['parsed_data']['skills'])} found")
    print(f"Processing time: {result['processing_time_ms']}ms")

    # 3. Get candidate skills
    print("\n=== Candidate Skills ===")
    skills = await client.get_candidate_skills(candidate_id)
    print(json.dumps(skills["skill_summary"], indent=2))

    # 4. Create a job description
    print("\n=== Create Job ===")
    job = await client.create_job({
        "title": "Senior Backend Engineer",
        "company": "TechCorp",
        "description": "Looking for a senior backend engineer",
        "required_skills": ["Python", "PostgreSQL", "Docker"],
        "preferred_skills": ["Kubernetes", "AWS", "GraphQL"],
        "experience_min_years": 5,
    })
    print(f"Job ID: {job['job_id']}")

    # 5. Match candidate to job
    print("\n=== Match Result ===")
    match = await client.match(candidate_id, job_id=job["job_id"])
    print(f"Overall Score: {match['overall_score']}")
    print(f"Skill Match: {match['skill_match_score']}")
    print(f"Recommendation: {match['recommendation']}")
    if match["gap_analysis"]["missing_skills"]:
        print(f"Missing Skills: {match['gap_analysis']['missing_skills']}")

    # 6. Search skills
    print("\n=== Skill Search ===")
    search = await client.search_skills("python")
    for s in search["results"][:5]:
        print(f"  {s['name']} ({s['category']}) — aliases: {s['aliases']}")

    # 7. Normalize a skill
    print("\n=== Normalize Skill ===")
    norm = await client.normalize_skill("K8s")
    print(f"  K8s -> {norm['canonical_name']} (confidence: {norm['confidence']})")


if __name__ == "__main__":
    asyncio.run(main())
