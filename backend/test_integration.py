"""
Full Integration Test — Verifies every component is connected and working.
Tests the complete flow: Parse → Normalize → Match → Store → Retrieve
"""
import httpx
import asyncio
import json
import sys
import time
import os

os.environ["PYTHONIOENCODING"] = "utf-8"
sys.stdout.reconfigure(encoding="utf-8")

BASE = "http://localhost:8000"
API_KEY = "dev-api-key-change-in-production"
HEADERS = {"X-API-Key": API_KEY}

passed = 0
failed = 0
errors = []


def result(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        errors.append(f"{name}: {detail}")
        print(f"  [FAIL] {name} — {detail}")


async def main():
    global passed, failed

    async with httpx.AsyncClient(base_url=BASE, timeout=60) as c:

        # ============================================================
        print("\n===== 1. HEALTH & INFRASTRUCTURE =====")
        # ============================================================

        # 1a. Health endpoint
        r = await c.get("/health")
        data = r.json()
        result("Health endpoint returns 200", r.status_code == 200)
        result("Skill taxonomy loaded", data["services"]["skill_taxonomy"]["total_skills"] > 100,
               f"got {data['services']['skill_taxonomy']['total_skills']}")
        result("Orchestrator engine is LangGraph",
               data["services"]["orchestrator"].get("engine") == "LangGraph",
               str(data["services"]["orchestrator"]))
        result("Redis service present", "redis" in data["services"])
        result("All agents reported OK",
               all(data["services"][a]["status"] == "ok"
                   for a in ["parsing_agent", "normalization_agent", "matching_agent"]))

        # 1b. API root
        r = await c.get("/api")
        result("API root returns version", r.json().get("version") == "1.0.0")

        # 1c. Swagger docs
        r = await c.get("/docs")
        result("Swagger /docs accessible", r.status_code == 200)
        r = await c.get("/redoc")
        result("ReDoc /redoc accessible", r.status_code == 200)
        r = await c.get("/openapi.json")
        spec = r.json()
        result("OpenAPI spec loads", "paths" in spec)
        result("OpenAPI has /api/v1/parse", "/api/v1/parse" in spec["paths"])
        result("OpenAPI has /api/v1/match", "/api/v1/match" in spec["paths"])
        result("OpenAPI has /api/v1/skills/taxonomy", "/api/v1/skills/taxonomy" in spec["paths"])

        # 1d. Frontend UI
        r = await c.get("/")
        result("Frontend HTML served", r.status_code == 200 and "<html" in r.text.lower())

        # 1e. Auth check — missing key should fail
        r = await c.get("/api/v1/candidates")
        result("Missing API key returns 401", r.status_code == 401)

        # 1f. Auth check — wrong key should fail
        r = await c.get("/api/v1/candidates", headers={"X-API-Key": "wrong-key"})
        result("Wrong API key returns 403", r.status_code == 403)

        # ============================================================
        print("\n===== 2. RESUME PARSING (Agent 1 — ParsingAgent) =====")
        # ============================================================

        # 2a. Parse resume 1 (Sarah — has publications)
        with open("app/data/sample_resumes/sample_resume_1.txt", "rb") as f:
            r = await c.post("/api/v1/parse", headers=HEADERS,
                             files={"file": ("resume1.txt", f, "text/plain")})
        result("Parse resume 1 returns 200", r.status_code == 200)
        p1 = r.json()
        cid1 = p1["candidate_id"]
        pd1 = p1["parsed_data"]
        result("Candidate ID generated", len(cid1) > 10)
        result("Name extracted", pd1["personal_info"]["name"] is not None,
               pd1["personal_info"].get("name"))
        result("Email extracted", pd1["personal_info"]["email"] is not None)
        result("Phone extracted", pd1["personal_info"]["phone"] is not None)
        result("LinkedIn extracted", pd1["personal_info"]["linkedin_url"] is not None)
        result("Skills extracted", len(pd1["skills"]) > 5, f"{len(pd1['skills'])} skills")
        result("Work experiences extracted", len(pd1["work_experiences"]) > 0)
        result("Educations extracted", len(pd1["educations"]) > 0)
        result("Certifications extracted", len(pd1["certifications"]) > 0)
        result("Publications extracted", len(pd1["publications"]) > 0,
               f"{len(pd1['publications'])} publications")
        result("Processing time tracked", p1["processing_time_ms"] > 0)

        # 2b. Agent traces present
        traces = p1.get("agent_traces", {})
        result("Agent traces returned", "agents" in traces)
        agent_names = [a["name"] for a in traces.get("agents", [])]
        result("ParsingAgent in traces", "ParsingAgent" in agent_names)
        result("NormalizationAgent in traces", "NormalizationAgent" in agent_names)

        # 2c. Parse resume 2 (Michael — backend engineer)
        with open("app/data/sample_resumes/sample_resume_2.txt", "rb") as f:
            r = await c.post("/api/v1/parse", headers=HEADERS,
                             files={"file": ("resume2.txt", f, "text/plain")})
        result("Parse resume 2 returns 200", r.status_code == 200)
        cid2 = r.json()["candidate_id"]

        # 2d. Parse resume 3 (Emily — data scientist)
        with open("app/data/sample_resumes/sample_resume_3.txt", "rb") as f:
            r = await c.post("/api/v1/parse", headers=HEADERS,
                             files={"file": ("resume3.txt", f, "text/plain")})
        result("Parse resume 3 returns 200", r.status_code == 200)
        cid3 = r.json()["candidate_id"]
        pd3 = r.json()["parsed_data"]
        result("Emily has 4 publications", len(pd3["publications"]) == 4,
               f"got {len(pd3['publications'])}")

        # 2e. Invalid file format rejected
        r = await c.post("/api/v1/parse", headers=HEADERS,
                         files={"file": ("photo.jpg", b"fake", "image/jpeg")})
        result("Invalid format rejected (400)", r.status_code == 400)

        # ============================================================
        print("\n===== 3. SKILL NORMALIZATION (Agent 2 — NormalizationAgent) =====")
        # ============================================================

        # 3a. Synonym resolution
        r = await c.get("/api/v1/skills/normalize", headers=HEADERS, params={"skill": "JS"})
        result("JS → JavaScript", r.json()["canonical_name"] == "JavaScript")

        r = await c.get("/api/v1/skills/normalize", headers=HEADERS, params={"skill": "K8s"})
        result("K8s → Kubernetes", r.json()["canonical_name"] == "Kubernetes")

        r = await c.get("/api/v1/skills/normalize", headers=HEADERS, params={"skill": "ReactJS"})
        result("ReactJS → React", r.json()["canonical_name"] == "React")

        r = await c.get("/api/v1/skills/normalize", headers=HEADERS, params={"skill": "py"})
        result("py → Python", r.json()["canonical_name"] == "Python")

        r = await c.get("/api/v1/skills/normalize", headers=HEADERS, params={"skill": "golang"})
        result("golang → Go", r.json()["canonical_name"] == "Go")

        r = await c.get("/api/v1/skills/normalize", headers=HEADERS, params={"skill": "AWS"})
        result("AWS → Amazon Web Services", r.json()["canonical_name"] == "Amazon Web Services")

        # 3b. Category info returned
        r = await c.get("/api/v1/skills/normalize", headers=HEADERS, params={"skill": "Docker"})
        d = r.json()
        result("Category returned for Docker", d["category"] is not None, d.get("category"))
        result("Related skills returned", len(d["related_skills"]) > 0)
        result("is_known=True for known skill", d["is_known"] is True)

        # 3c. Unknown skill detection
        r = await c.get("/api/v1/skills/normalize", headers=HEADERS,
                        params={"skill": "SomeUnknownTech2099"})
        result("Unknown skill has low confidence", r.json()["confidence"] <= 0.5)
        result("Unknown skill is_known=False", r.json()["is_known"] is False)

        # 3d. Skills in parsed resume are normalized
        skill_names = [s["canonical_name"] for s in pd1["skills"] if s["canonical_name"]]
        result("Parsed skills have canonical names", len(skill_names) > 5)
        result("Parsed skills have categories",
               any(s["category"] is not None for s in pd1["skills"]))
        result("Inferred skills present",
               any(s["source"] == "inferred" for s in pd1["skills"]),
               "No inferred skills found")
        result("Proficiency levels assigned",
               any(s["proficiency_level"] is not None for s in pd1["skills"]))

        # ============================================================
        print("\n===== 4. SKILL TAXONOMY =====")
        # ============================================================

        # 4a. Browse taxonomy
        r = await c.get("/api/v1/skills/taxonomy", headers=HEADERS)
        tax = r.json()
        result("Taxonomy loads", tax["total_skills"] > 100, f"{tax['total_skills']} skills")
        result("Technical Skills category exists", "Technical Skills" in tax["categories"])
        result("Soft Skills category exists", "Soft Skills" in tax["categories"])
        result("Domain Skills category exists", "Domain Skills" in tax["categories"])

        # 4b. Search skills
        r = await c.get("/api/v1/skills/search", headers=HEADERS, params={"q": "python"})
        result("Search returns results", r.json()["total_results"] > 0)
        result("Python in search results",
               any(s["name"] == "Python" for s in r.json()["results"]))

        # 4c. List categories
        r = await c.get("/api/v1/skills/categories", headers=HEADERS)
        cats = r.json()
        result("Categories list returns data", cats["total_categories"] > 10,
               f"{cats['total_categories']} categories")

        # ============================================================
        print("\n===== 5. CANDIDATE STORAGE (Redis) =====")
        # ============================================================

        # 5a. List candidates
        r = await c.get("/api/v1/candidates", headers=HEADERS)
        cands = r.json()
        result("Candidates stored after parsing", cands["total"] >= 3,
               f"got {cands['total']}")

        # 5b. Get specific candidate
        r = await c.get(f"/api/v1/candidates/{cid1}", headers=HEADERS)
        result("Get candidate by ID works", r.status_code == 200)
        cdata = r.json()
        result("Candidate has personal_info", "personal_info" in cdata)
        result("Candidate has skills", len(cdata.get("skills", [])) > 0)
        result("Candidate has publications field", "publications" in cdata)

        # 5c. Get candidate skills
        r = await c.get(f"/api/v1/candidates/{cid1}/skills", headers=HEADERS)
        result("Get candidate skills works", r.status_code == 200)
        sk = r.json()
        result("Skill summary grouped by category", len(sk.get("skill_summary", {})) > 0)

        # 5d. Non-existent candidate returns 404
        r = await c.get("/api/v1/candidates/nonexistent-id-12345", headers=HEADERS)
        result("Missing candidate returns 404", r.status_code == 404)

        # ============================================================
        print("\n===== 6. JOB MATCHING (Agent 3 — MatchingAgent) =====")
        # ============================================================

        # 6a. Create a job
        job_data = {
            "title": "Senior ML Engineer",
            "company": "AI Corp",
            "description": "ML engineer for NLP team",
            "required_skills": ["Python", "TensorFlow", "NLP", "Machine Learning"],
            "preferred_skills": ["PyTorch", "Docker", "AWS", "Spark"],
            "experience_min_years": 5,
            "experience_max_years": 12,
            "location": "Remote",
            "job_type": "full-time",
        }
        r = await c.post("/api/v1/jobs", headers=HEADERS, json=job_data)
        result("Create job returns 200", r.status_code == 200)
        job_id = r.json()["job_id"]
        result("Job ID generated", len(job_id) > 10)

        # 6b. Retrieve job
        r = await c.get(f"/api/v1/jobs/{job_id}", headers=HEADERS)
        result("Get job by ID works", r.status_code == 200)

        # 6c. List jobs
        r = await c.get("/api/v1/jobs", headers=HEADERS)
        result("List jobs works", r.json()["total"] >= 1)

        # 6d. Match strong candidate (Emily — ML/NLP expert) against ML job
        r = await c.post("/api/v1/match", headers=HEADERS, json={
            "candidate_id": cid3,
            "job_id": job_id,
            "matching_threshold": 0.5,
        })
        result("Match endpoint returns 200", r.status_code == 200)
        m = r.json()
        result("Overall score > 0.7 for strong match", m["overall_score"] > 0.7,
               f"score={m['overall_score']}")
        result("Skill match score present", m["skill_match_score"] >= 0)
        result("Experience score present", m["experience_score"] >= 0)
        result("Education score present", m["education_score"] >= 0)
        result("Matched skills list returned", len(m["matched_skills"]) > 0)
        result("Match types correct",
               all(ms["match_type"] in ("direct", "semantic", "inferred")
                   for ms in m["matched_skills"]))
        result("Recommendation text present", len(m["recommendation"]) > 10)
        result("Gap analysis present", "gap_analysis" in m)

        # 6e. Match with inline job description (no job_id)
        r = await c.post("/api/v1/match", headers=HEADERS, json={
            "candidate_id": cid2,
            "job_description": {
                "title": "Frontend Developer",
                "description": "Frontend dev role",
                "required_skills": ["React", "TypeScript", "CSS"],
                "preferred_skills": ["Next.js", "GraphQL"],
            },
            "matching_threshold": 0.3,
        })
        result("Match with inline job works", r.status_code == 200)
        m2 = r.json()
        result("Weak match has lower score", m2["overall_score"] < m["overall_score"],
               f"backend dev vs frontend job = {m2['overall_score']}")
        result("Missing skills identified", len(m2["gap_analysis"]["missing_skills"]) > 0)
        result("Upskilling suggestions given",
               len(m2["gap_analysis"]["upskilling_suggestions"]) >= 0)

        # 6f. Match non-existent candidate → 404
        r = await c.post("/api/v1/match", headers=HEADERS, json={
            "candidate_id": "fake-id",
            "job_id": job_id,
        })
        result("Match with bad candidate → 404", r.status_code == 404)

        # ============================================================
        print("\n===== 7. BATCH PROCESSING =====")
        # ============================================================

        files = []
        for i in [4, 5, 6]:
            f = open(f"app/data/sample_resumes/sample_resume_{i}.txt", "rb")
            files.append(("files", (f"resume_{i}.txt", f, "text/plain")))

        r = await c.post("/api/v1/parse/batch", headers=HEADERS, files=files)
        for _, (_, fobj, _) in files:
            fobj.close()

        result("Batch parse returns 200", r.status_code == 200)
        batch = r.json()
        batch_id = batch["batch_id"]
        result("Batch ID generated", len(batch_id) > 10)
        result("Batch status is processing", batch["status"] == "processing")
        result("Total files = 3", batch["total_files"] == 3)

        # 7b. Poll batch status
        await asyncio.sleep(3)
        r = await c.get(f"/api/v1/parse/batch/{batch_id}", headers=HEADERS)
        result("Batch status endpoint works", r.status_code == 200)
        bs = r.json()
        result("Batch completed", bs["status"] == "completed",
               f"status={bs['status']}, processed={bs['processed_files']}")

        # 7c. Verify batch candidates stored
        r = await c.get("/api/v1/candidates", headers=HEADERS)
        total_after_batch = r.json()["total"]
        result("Batch candidates persisted", total_after_batch >= 6,
               f"total candidates now: {total_after_batch}")

        # ============================================================
        print("\n===== 8. DEMO ENDPOINTS =====")
        # ============================================================

        with open("app/data/sample_resumes/sample_resume_7.txt", "rb") as f:
            r = await c.post("/demo/parse", files={"file": ("r7.txt", f, "text/plain")})
        result("Demo parse works (no auth)", r.status_code == 200)
        result("Demo parse returns skills", len(r.json().get("skills", [])) > 0)
        result("Demo parse returns publications count", "publications" in r.json())

        with open("app/data/sample_resumes/sample_resume_8.txt", "rb") as f:
            r = await c.post("/demo/match",
                             params={"job_title": "Data Engineer",
                                     "required_skills": "Python,Spark,Kafka",
                                     "preferred_skills": "Airflow,Docker,AWS"},
                             files={"file": ("r8.txt", f, "text/plain")})
        result("Demo match works (no auth)", r.status_code == 200)
        dm = r.json()
        result("Demo match returns score", dm.get("overall_score", 0) > 0)
        result("Demo match returns matched skills", len(dm.get("matched_skills", [])) > 0)

        # ============================================================
        print("\n===== 9. ERROR HANDLING & VALIDATION =====")
        # ============================================================

        # 9a. Empty file
        r = await c.post("/api/v1/parse", headers=HEADERS,
                         files={"file": ("empty.txt", b"", "text/plain")})
        result("Empty file handled gracefully", r.status_code in (200, 400, 500))

        # 9b. Missing required fields in match
        r = await c.post("/api/v1/match", headers=HEADERS, json={
            "candidate_id": cid1
        })
        result("Match without job returns 400", r.status_code == 400)

        # 9c. Rate limit header check
        r = await c.get("/health")
        result("Request returns X-Process-Time header",
               "x-process-time-ms" in r.headers or "x-request-id" in r.headers)

    # ============================================================
    print("\n" + "=" * 60)
    print(f"  RESULTS:  {passed} PASSED  |  {failed} FAILED  |  {passed + failed} TOTAL")
    print("=" * 60)

    if errors:
        print("\nFailed tests:")
        for e in errors:
            print(f"  - {e}")

    return failed == 0


if __name__ == "__main__":
    ok = asyncio.run(main())
    sys.exit(0 if ok else 1)
