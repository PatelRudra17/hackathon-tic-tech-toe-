"""
Evaluation Script for Talent Intelligence System
=================================================

Computes the metrics required by the problem statement:
1. Resume parsing accuracy (field-level F1-score)
2. Skill normalization precision (correct canonical mapping rate)
3. Matching quality (NDCG and correlation with expert rankings)
4. End-to-end latency (single resume processing time)

Usage:
    python -m evaluation.evaluate
"""

import asyncio
import json
import time
import os
import sys
import math
from typing import Dict, List, Tuple
from collections import defaultdict
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.agents.parsing_agent import ParsingAgent
from app.agents.normalization_agent import NormalizationAgent
from app.agents.matching_agent import MatchingAgent
from app.agents.orchestrator import get_orchestrator
from app.services.skill_taxonomy import get_taxonomy_service
from app.models.schemas import ParsedResume, JobDescriptionRequest, SkillSchema


# ─── 1. Parsing Accuracy (F1-Score) ───

def compute_f1(predicted: set, ground_truth: set) -> Dict[str, float]:
    """Compute precision, recall, and F1 for a set of predicted vs ground-truth values."""
    if not ground_truth and not predicted:
        return {"precision": 1.0, "recall": 1.0, "f1": 1.0}
    if not ground_truth:
        return {"precision": 0.0, "recall": 1.0, "f1": 0.0}
    if not predicted:
        return {"precision": 1.0, "recall": 0.0, "f1": 0.0}

    tp = len(predicted & ground_truth)
    precision = tp / len(predicted) if predicted else 0
    recall = tp / len(ground_truth) if ground_truth else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

    return {"precision": round(precision, 4), "recall": round(recall, 4), "f1": round(f1, 4)}


async def evaluate_parsing_accuracy(ground_truth_path: str) -> Dict:
    """Evaluate parsing accuracy against ground-truth labeled resumes.

    Ground-truth format (JSON):
    {
        "file": "resume.txt",
        "expected": {
            "name": "John Doe",
            "email": "john@email.com",
            "skills": ["Python", "Docker", ...],
            "companies": ["TechCorp", ...],
            "degrees": ["Bachelor of Science", ...]
        }
    }
    """
    gt_path = Path(ground_truth_path)
    if not gt_path.exists():
        print(f"  Ground truth file not found: {gt_path}")
        return {"status": "no_data", "message": "Ground truth file not found"}

    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth_data = json.load(f)

    agent = ParsingAgent()
    field_scores = defaultdict(list)
    total_results = []

    for item in ground_truth_data:
        resume_file = Path(__file__).parent.parent / "app" / "data" / "sample_resumes" / item["file"]
        if not resume_file.exists():
            continue

        with open(resume_file, "rb") as f:
            content = f.read()

        parsed = await agent.parse(content, item["file"])
        expected = item["expected"]

        # Name accuracy
        if expected.get("name"):
            pred_name = {parsed.personal_info.name.lower().strip()} if parsed.personal_info.name else set()
            gt_name = {expected["name"].lower().strip()}
            name_f1 = compute_f1(pred_name, gt_name)
            field_scores["name"].append(name_f1["f1"])

        # Email accuracy
        if expected.get("email"):
            pred_email = {parsed.personal_info.email.lower()} if parsed.personal_info.email else set()
            gt_email = {expected["email"].lower()}
            email_f1 = compute_f1(pred_email, gt_email)
            field_scores["email"].append(email_f1["f1"])

        # Skills accuracy
        if expected.get("skills"):
            pred_skills = {s.name.lower() for s in parsed.skills}
            gt_skills = {s.lower() for s in expected["skills"]}
            skills_f1 = compute_f1(pred_skills, gt_skills)
            field_scores["skills"].append(skills_f1["f1"])

        # Companies accuracy
        if expected.get("companies"):
            pred_companies = {e.company.lower() for e in parsed.work_experiences if e.company}
            gt_companies = {c.lower() for c in expected["companies"]}
            comp_f1 = compute_f1(pred_companies, gt_companies)
            field_scores["companies"].append(comp_f1["f1"])

        # Degrees accuracy
        if expected.get("degrees"):
            pred_degrees = {e.degree.lower() for e in parsed.educations if e.degree}
            gt_degrees = {d.lower() for d in expected["degrees"]}
            deg_f1 = compute_f1(pred_degrees, gt_degrees)
            field_scores["degrees"].append(deg_f1["f1"])

        total_results.append({
            "file": item["file"],
            "confidence": parsed.parsing_confidence,
        })

    # Average F1 per field
    avg_scores = {}
    for field, scores in field_scores.items():
        avg_scores[field] = round(sum(scores) / len(scores), 4) if scores else 0.0

    overall_f1 = sum(avg_scores.values()) / len(avg_scores) if avg_scores else 0.0

    return {
        "status": "evaluated",
        "resumes_evaluated": len(total_results),
        "field_f1_scores": avg_scores,
        "overall_f1": round(overall_f1, 4),
    }


# ─── 2. Skill Normalization Precision ───

def evaluate_normalization_precision(ground_truth_path: str) -> Dict:
    """Evaluate skill normalization against ground-truth mappings.

    Ground-truth format (JSON):
    [
        {"raw": "JS", "expected_canonical": "JavaScript"},
        {"raw": "K8s", "expected_canonical": "Kubernetes"},
        ...
    ]
    """
    gt_path = Path(ground_truth_path)
    if not gt_path.exists():
        print(f"  Ground truth file not found: {gt_path}")
        return {"status": "no_data"}

    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    taxonomy = get_taxonomy_service()
    correct = 0
    total = len(ground_truth)
    results = []

    for item in ground_truth:
        canonical, confidence = taxonomy.normalize_skill(item["raw"])
        is_correct = canonical.lower() == item["expected_canonical"].lower()
        if is_correct:
            correct += 1
        results.append({
            "raw": item["raw"],
            "expected": item["expected_canonical"],
            "predicted": canonical,
            "confidence": confidence,
            "correct": is_correct,
        })

    precision = correct / total if total > 0 else 0.0

    return {
        "status": "evaluated",
        "total_skills": total,
        "correct_mappings": correct,
        "precision": round(precision, 4),
        "details": results,
    }


# ─── 3. Matching Quality (NDCG) ───

def dcg(scores: List[float], k: int = None) -> float:
    """Compute Discounted Cumulative Gain."""
    if k:
        scores = scores[:k]
    return sum(s / math.log2(i + 2) for i, s in enumerate(scores))


def ndcg(predicted_scores: List[float], ideal_scores: List[float], k: int = None) -> float:
    """Compute Normalized Discounted Cumulative Gain."""
    ideal = dcg(sorted(ideal_scores, reverse=True), k)
    if ideal == 0:
        return 0.0
    return dcg(predicted_scores, k) / ideal


async def evaluate_matching_quality(ground_truth_path: str) -> Dict:
    """Evaluate matching quality against expert rankings.

    Ground-truth format (JSON):
    [
        {
            "job": { "title": "...", "required_skills": [...], ... },
            "candidates": [
                { "skills": [...], "expert_score": 0.9 },
                ...
            ]
        }
    ]
    """
    gt_path = Path(ground_truth_path)
    if not gt_path.exists():
        print(f"  Ground truth file not found: {gt_path}")
        return {"status": "no_data"}

    with open(gt_path, "r", encoding="utf-8") as f:
        ground_truth = json.load(f)

    agent = MatchingAgent()
    ndcg_scores = []
    correlations = []

    for scenario in ground_truth:
        job = JobDescriptionRequest(**scenario["job"])
        predicted = []
        expected = []

        for cand in scenario["candidates"]:
            resume = ParsedResume(
                skills=[SkillSchema(name=s) for s in cand["skills"]],
            )
            result = await agent.match(resume, job)
            predicted.append(result["overall_score"])
            expected.append(cand["expert_score"])

        # Sort by predicted score and get expert scores in that order
        paired = sorted(zip(predicted, expected), key=lambda x: -x[0])
        pred_sorted = [p for p, _ in paired]
        exp_sorted = [e for _, e in paired]

        n = ndcg(exp_sorted, expected)
        ndcg_scores.append(n)

        # Spearman-like correlation
        if len(predicted) > 1:
            from statistics import correlation as stat_corr
            try:
                corr = stat_corr(predicted, expected)
            except Exception:
                corr = 0.0
            correlations.append(corr)

    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0
    avg_corr = sum(correlations) / len(correlations) if correlations else 0.0

    return {
        "status": "evaluated",
        "scenarios_evaluated": len(ground_truth),
        "average_ndcg": round(avg_ndcg, 4),
        "average_correlation": round(avg_corr, 4),
    }


# ─── 4. End-to-End Latency ───

async def evaluate_latency(sample_dir: str, num_runs: int = 5) -> Dict:
    """Measure end-to-end single resume processing latency."""
    sample_path = Path(sample_dir)
    if not sample_path.exists():
        return {"status": "no_data"}

    sample_files = list(sample_path.glob("*.txt")) + list(sample_path.glob("*.pdf"))
    if not sample_files:
        return {"status": "no_data", "message": "No sample files found"}

    orchestrator = get_orchestrator()
    latencies = []

    for _ in range(num_runs):
        for fpath in sample_files[:3]:
            with open(fpath, "rb") as f:
                content = f.read()

            start = time.time()
            await orchestrator.process_resume(content, fpath.name)
            elapsed_ms = (time.time() - start) * 1000
            latencies.append(elapsed_ms)

    avg_latency = sum(latencies) / len(latencies) if latencies else 0
    p95 = sorted(latencies)[int(len(latencies) * 0.95)] if latencies else 0
    meets_target = avg_latency < 10000  # < 10 seconds

    return {
        "status": "evaluated",
        "runs": len(latencies),
        "avg_latency_ms": round(avg_latency, 1),
        "p95_latency_ms": round(p95, 1),
        "min_latency_ms": round(min(latencies), 1) if latencies else 0,
        "max_latency_ms": round(max(latencies), 1) if latencies else 0,
        "meets_target_10s": meets_target,
    }


# ─── Main Evaluation Runner ───

async def run_all_evaluations():
    """Run all evaluations and print results."""
    base = Path(__file__).parent.parent
    gt_dir = base / "app" / "data" / "ground_truth"

    print("=" * 60)
    print("  TALENT INTELLIGENCE — EVALUATION REPORT")
    print("=" * 60)

    # 1. Parsing accuracy
    print("\n1. RESUME PARSING ACCURACY (F1-Score)")
    print("-" * 40)
    parsing_result = await evaluate_parsing_accuracy(str(gt_dir / "parsing_ground_truth.json"))
    if parsing_result.get("field_f1_scores"):
        for field, score in parsing_result["field_f1_scores"].items():
            print(f"   {field:15s}: F1 = {score:.4f}")
        print(f"   {'OVERALL':15s}: F1 = {parsing_result['overall_f1']:.4f}")
    else:
        print(f"   {parsing_result.get('message', 'No data')}")

    # 2. Normalization precision
    print("\n2. SKILL NORMALIZATION PRECISION")
    print("-" * 40)
    norm_result = evaluate_normalization_precision(str(gt_dir / "normalization_ground_truth.json"))
    if norm_result.get("precision") is not None:
        print(f"   Total skills tested: {norm_result.get('total_skills', 0)}")
        print(f"   Correct mappings:    {norm_result.get('correct_mappings', 0)}")
        print(f"   Precision:           {norm_result.get('precision', 0):.4f}")
    else:
        print("   No data")

    # 3. Matching quality
    print("\n3. MATCHING QUALITY (NDCG)")
    print("-" * 40)
    match_result = await evaluate_matching_quality(str(gt_dir / "matching_ground_truth.json"))
    if match_result.get("average_ndcg") is not None:
        print(f"   Scenarios evaluated: {match_result.get('scenarios_evaluated', 0)}")
        print(f"   Average NDCG:        {match_result.get('average_ndcg', 0):.4f}")
        print(f"   Average Correlation: {match_result.get('average_correlation', 0):.4f}")
    else:
        print("   No data")

    # 4. Latency
    print("\n4. END-TO-END LATENCY")
    print("-" * 40)
    latency_result = await evaluate_latency(str(base / "app" / "data" / "sample_resumes"))
    if latency_result.get("avg_latency_ms"):
        print(f"   Runs:          {latency_result['runs']}")
        print(f"   Avg latency:   {latency_result['avg_latency_ms']:.1f}ms")
        print(f"   P95 latency:   {latency_result['p95_latency_ms']:.1f}ms")
        print(f"   Min latency:   {latency_result['min_latency_ms']:.1f}ms")
        print(f"   Max latency:   {latency_result['max_latency_ms']:.1f}ms")
        print(f"   Meets <10s:    {'YES' if latency_result['meets_target_10s'] else 'NO'}")
    else:
        print("   No data")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_evaluations())
