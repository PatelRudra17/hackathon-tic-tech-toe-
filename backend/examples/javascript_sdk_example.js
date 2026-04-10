/**
 * Talent Intelligence API — JavaScript SDK Example
 * ==================================================
 *
 * This module demonstrates how to integrate with the Talent Intelligence
 * REST API from JavaScript / Node.js.  It covers every endpoint: resume
 * parsing (single & batch), candidate retrieval, job matching, and the
 * skill taxonomy.
 *
 * Requirements:
 *   npm install node-fetch form-data
 *
 * Usage:
 *   node javascript_sdk_example.js
 */

const fs = require("fs");
const path = require("path");
const FormData = require("form-data");

const BASE_URL = "http://localhost:8000";
const API_KEY = "dev-api-key-change-in-production";

const HEADERS = {
  "X-API-Key": API_KEY,
  "Content-Type": "application/json",
};

// ── Helper ──

async function request(method, endpoint, { body, files, params } = {}) {
  const fetch = (await import("node-fetch")).default;

  let url = `${BASE_URL}${endpoint}`;
  if (params) {
    const qs = new URLSearchParams(params).toString();
    url += `?${qs}`;
  }

  const options = { method, headers: { "X-API-Key": API_KEY } };

  if (files) {
    const form = new FormData();
    for (const f of files) {
      form.append(f.field, fs.createReadStream(f.path), f.name);
    }
    options.body = form;
    Object.assign(options.headers, form.getHeaders());
  } else if (body) {
    options.body = JSON.stringify(body);
    options.headers["Content-Type"] = "application/json";
  }

  const resp = await fetch(url, options);
  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`${resp.status} ${resp.statusText}: ${text}`);
  }
  return resp.json();
}

// ── SDK Class ──

class TalentIntelligenceClient {
  // Health
  async healthCheck() {
    return request("GET", "/health");
  }

  // Parse a single resume
  async parseResume(filePath) {
    return request("POST", "/api/v1/parse", {
      files: [
        { field: "file", path: filePath, name: path.basename(filePath) },
      ],
    });
  }

  // Parse multiple resumes (batch)
  async parseBatch(filePaths, webhookUrl = null) {
    const files = filePaths.map((fp) => ({
      field: "files",
      path: fp,
      name: path.basename(fp),
    }));
    const params = webhookUrl ? { webhook_url: webhookUrl } : {};
    return request("POST", "/api/v1/parse/batch", { files, params });
  }

  // Get batch status
  async getBatchStatus(batchId) {
    return request("GET", `/api/v1/parse/batch/${batchId}`);
  }

  // Poll batch until done
  async pollBatch(batchId, intervalMs = 3000, timeoutMs = 300000) {
    const start = Date.now();
    while (Date.now() - start < timeoutMs) {
      const status = await this.getBatchStatus(batchId);
      if (status.status === "completed" || status.status === "failed") {
        return status;
      }
      await new Promise((r) => setTimeout(r, intervalMs));
    }
    throw new Error(`Batch ${batchId} did not complete within timeout`);
  }

  // Get candidate full profile
  async getCandidate(candidateId) {
    return request("GET", `/api/v1/candidates/${candidateId}`);
  }

  // Get candidate skills
  async getCandidateSkills(candidateId) {
    return request("GET", `/api/v1/candidates/${candidateId}/skills`);
  }

  // List all candidates
  async listCandidates() {
    return request("GET", "/api/v1/candidates");
  }

  // Create a job description
  async createJob(jobData) {
    return request("POST", "/api/v1/jobs", { body: jobData });
  }

  // Get a job description
  async getJob(jobId) {
    return request("GET", `/api/v1/jobs/${jobId}`);
  }

  // List all jobs
  async listJobs() {
    return request("GET", "/api/v1/jobs");
  }

  // Match candidate to job
  async match(candidateId, { jobId, jobDescription, threshold = 0.5 } = {}) {
    const body = { candidate_id: candidateId, matching_threshold: threshold };
    if (jobId) body.job_id = jobId;
    if (jobDescription) body.job_description = jobDescription;
    return request("POST", "/api/v1/match", { body });
  }

  // Browse skill taxonomy
  async getTaxonomy() {
    return request("GET", "/api/v1/skills/taxonomy");
  }

  // Search skills
  async searchSkills(query, limit = 20) {
    return request("GET", "/api/v1/skills/search", {
      params: { q: query, limit },
    });
  }

  // Normalize a skill
  async normalizeSkill(skill) {
    return request("GET", "/api/v1/skills/normalize", {
      params: { skill },
    });
  }
}

// ── Example Usage ──

async function main() {
  const client = new TalentIntelligenceClient();

  // 1. Health check
  console.log("=== Health Check ===");
  const health = await client.healthCheck();
  console.log(JSON.stringify(health, null, 2));

  // 2. Parse a resume
  console.log("\n=== Parse Resume ===");
  const parsed = await client.parseResume(
    "app/data/sample_resumes/sample_resume_1.txt"
  );
  const candidateId = parsed.candidate_id;
  console.log(`Candidate ID: ${candidateId}`);
  console.log(`Name: ${parsed.parsed_data.personal_info.name}`);
  console.log(`Skills found: ${parsed.parsed_data.skills.length}`);

  // 3. Get candidate skills
  console.log("\n=== Candidate Skills ===");
  const skills = await client.getCandidateSkills(candidateId);
  console.log(JSON.stringify(skills.skill_summary, null, 2));

  // 4. Create a job
  console.log("\n=== Create Job ===");
  const job = await client.createJob({
    title: "Full-Stack Developer",
    company: "StartupXYZ",
    description: "Looking for a full-stack developer",
    required_skills: ["JavaScript", "React", "Node.js"],
    preferred_skills: ["TypeScript", "PostgreSQL", "Docker"],
    experience_min_years: 3,
  });
  console.log(`Job ID: ${job.job_id}`);

  // 5. Match
  console.log("\n=== Match ===");
  const matchResult = await client.match(candidateId, { jobId: job.job_id });
  console.log(`Overall Score: ${matchResult.overall_score}`);
  console.log(`Recommendation: ${matchResult.recommendation}`);

  // 6. Search skills
  console.log("\n=== Skill Search ===");
  const search = await client.searchSkills("react");
  search.results.slice(0, 5).forEach((s) => {
    console.log(`  ${s.name} (${s.category})`);
  });

  // 7. Normalize
  console.log("\n=== Normalize ===");
  const norm = await client.normalizeSkill("JS");
  console.log(`  JS -> ${norm.canonical_name} (confidence: ${norm.confidence})`);
}

main().catch(console.error);
