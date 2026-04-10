import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, TypedDict, Annotated
from loguru import logger

from langgraph.graph import StateGraph, END, START

from app.agents.parsing_agent import ParsingAgent
from app.agents.normalization_agent import NormalizationAgent
from app.agents.matching_agent import MatchingAgent
from app.models.schemas import (
    ParsedResume, AgentTrace, OrchestrationTrace,
    JobDescriptionRequest, MatchResponse
)


# ─── LangGraph State Definitions ───

class ResumeState(TypedDict, total=False):
    """State that flows through the LangGraph resume processing pipeline."""
    request_id: str
    file_content: bytes
    filename: str
    parsed_resume: Optional[ParsedResume]
    job: Optional[JobDescriptionRequest]
    match_threshold: float
    match_result: Optional[Dict]
    traces: List[AgentTrace]
    status: str
    error: Optional[str]
    start_time: float


# ─── Agent Node Functions ───

_parsing_agent: Optional[ParsingAgent] = None
_normalization_agent: Optional[NormalizationAgent] = None
_matching_agent: Optional[MatchingAgent] = None

MAX_RETRIES = 2


def _get_agents():
    global _parsing_agent, _normalization_agent, _matching_agent
    if _parsing_agent is None:
        _parsing_agent = ParsingAgent()
    if _normalization_agent is None:
        _normalization_agent = NormalizationAgent()
    if _matching_agent is None:
        _matching_agent = MatchingAgent()
    return _parsing_agent, _normalization_agent, _matching_agent


async def _run_with_retry(agent_name: str, coro_fn, request_id: str) -> tuple:
    """Run an agent coroutine with retry logic and tracing."""
    trace = AgentTrace(
        agent_name=agent_name,
        status="running",
        start_time=datetime.utcnow(),
        input_summary=f"Request: {request_id}",
    )
    last_error = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            start = time.time()
            result = await coro_fn()
            duration = (time.time() - start) * 1000
            trace.status = "success"
            trace.end_time = datetime.utcnow()
            trace.duration_ms = round(duration, 1)
            trace.output_summary = f"Completed in {duration:.0f}ms"
            trace.quality_score = getattr(result, "parsing_confidence", None)
            return result, trace
        except Exception as e:
            last_error = e
            logger.warning(f"[{request_id}] {agent_name} attempt {attempt + 1} failed: {e}")
            if attempt < MAX_RETRIES:
                await asyncio.sleep(0.5 * (attempt + 1))

    trace.status = "failed"
    trace.end_time = datetime.utcnow()
    trace.error = str(last_error)
    logger.error(f"[{request_id}] {agent_name} failed after {MAX_RETRIES + 1} attempts")
    return None, trace


async def parse_node(state: ResumeState) -> Dict:
    """LangGraph node: Parse the resume."""
    parsing_agent, _, _ = _get_agents()
    request_id = state["request_id"]
    logger.info(f"[{request_id}] LangGraph → ParsingAgent node")

    result, trace = await _run_with_retry(
        "ParsingAgent",
        lambda: parsing_agent.parse(state["file_content"], state["filename"]),
        request_id,
    )

    traces = list(state.get("traces", []))
    traces.append(trace)

    if result is None:
        return {
            "parsed_resume": None,
            "traces": traces,
            "status": "failed",
            "error": "Parsing failed",
        }
    return {"parsed_resume": result, "traces": traces, "status": "parsed"}


async def normalize_node(state: ResumeState) -> Dict:
    """LangGraph node: Normalize skills in the parsed resume."""
    _, normalization_agent, _ = _get_agents()
    request_id = state["request_id"]
    logger.info(f"[{request_id}] LangGraph → NormalizationAgent node")

    parsed_resume = state.get("parsed_resume")
    if parsed_resume is None:
        return {"status": "failed", "error": "No parsed resume to normalize"}

    result, trace = await _run_with_retry(
        "NormalizationAgent",
        lambda: normalization_agent.normalize(parsed_resume),
        request_id,
    )

    traces = list(state.get("traces", []))
    traces.append(trace)

    # Graceful degradation: use original if normalization fails
    if result is None:
        logger.warning(f"[{request_id}] Normalization failed, using raw parsed data")
        return {"traces": traces, "status": "partial"}

    return {"parsed_resume": result, "traces": traces, "status": "normalized"}


async def match_node(state: ResumeState) -> Dict:
    """LangGraph node: Match candidate against job description."""
    _, _, matching_agent = _get_agents()
    request_id = state["request_id"]
    logger.info(f"[{request_id}] LangGraph → MatchingAgent node")

    parsed_resume = state.get("parsed_resume")
    job = state.get("job")
    threshold = state.get("match_threshold", 0.5)

    if parsed_resume is None or job is None:
        return {"status": "failed", "error": "Missing resume or job for matching"}

    result, trace = await _run_with_retry(
        "MatchingAgent",
        lambda: matching_agent.match(parsed_resume, job, threshold),
        request_id,
    )

    traces = list(state.get("traces", []))
    traces.append(trace)

    return {"match_result": result, "traces": traces, "status": "matched"}


def should_match(state: ResumeState) -> str:
    """Conditional edge: decide whether to proceed to matching or end."""
    if state.get("status") == "failed":
        return "end"
    if state.get("job") is not None:
        return "match"
    return "end"


def should_normalize(state: ResumeState) -> str:
    """Conditional edge: skip normalization if parsing failed."""
    if state.get("status") == "failed" or state.get("parsed_resume") is None:
        return "end"
    return "normalize"


# ─── Build LangGraph Pipelines ───

def _build_parse_normalize_graph():
    """Build the resume parsing + normalization pipeline graph."""
    graph = StateGraph(ResumeState)

    graph.add_node("parse", parse_node)
    graph.add_node("normalize", normalize_node)

    graph.add_edge(START, "parse")
    graph.add_conditional_edges("parse", should_normalize, {
        "normalize": "normalize",
        "end": END,
    })
    graph.add_edge("normalize", END)

    return graph.compile()


def _build_full_pipeline_graph():
    """Build the full pipeline: parse → normalize → match."""
    graph = StateGraph(ResumeState)

    graph.add_node("parse", parse_node)
    graph.add_node("normalize", normalize_node)
    graph.add_node("match", match_node)

    graph.add_edge(START, "parse")
    graph.add_conditional_edges("parse", should_normalize, {
        "normalize": "normalize",
        "end": END,
    })
    graph.add_conditional_edges("normalize", should_match, {
        "match": "match",
        "end": END,
    })
    graph.add_edge("match", END)

    return graph.compile()


def _build_match_only_graph():
    """Build a matching-only graph for already-parsed candidates."""
    graph = StateGraph(ResumeState)

    graph.add_node("match", match_node)

    graph.add_edge(START, "match")
    graph.add_edge("match", END)

    return graph.compile()


# ─── Orchestrator Wrapper ───

class Orchestrator:
    """Multi-Agent Orchestration Layer using LangGraph.

    Coordinates the Parsing, Normalization, and Matching agents through
    LangGraph's StateGraph pipeline. Handles:
    - Agent lifecycle and task delegation via LangGraph nodes
    - Concurrent resume processing (batch mode)
    - Retry logic and graceful degradation
    - Per-agent execution traces and observability
    """

    BATCH_CONCURRENCY = 5

    def __init__(self):
        _get_agents()  # Initialize agents
        self.parse_normalize_graph = _build_parse_normalize_graph()
        self.full_pipeline_graph = _build_full_pipeline_graph()
        self.match_only_graph = _build_match_only_graph()
        logger.info("Orchestrator initialized with LangGraph pipelines")

    async def process_resume(
        self, file_content: bytes, filename: str
    ) -> Dict[str, Any]:
        """Process a single resume through the LangGraph pipeline.
        Returns parsed + normalized resume data with traces."""
        request_id = str(uuid.uuid4())
        start_time = time.time()

        logger.info(f"[{request_id}] Starting LangGraph resume processing: {filename}")

        initial_state: ResumeState = {
            "request_id": request_id,
            "file_content": file_content,
            "filename": filename,
            "parsed_resume": None,
            "job": None,
            "match_threshold": 0.5,
            "match_result": None,
            "traces": [],
            "status": "pending",
            "error": None,
            "start_time": start_time,
        }

        result_state = await self.parse_normalize_graph.ainvoke(initial_state)

        total_duration = (time.time() - start_time) * 1000
        traces = result_state.get("traces", [])

        orchestration_trace = OrchestrationTrace(
            request_id=request_id,
            total_duration_ms=round(total_duration, 1),
            agent_traces=traces,
            status="success" if result_state.get("parsed_resume") else "failed",
        )

        logger.info(f"[{request_id}] Resume processing complete in {total_duration:.0f}ms")

        if result_state.get("status") == "failed" or result_state.get("parsed_resume") is None:
            return {
                "request_id": request_id,
                "status": "failed",
                "error": result_state.get("error", "Processing failed"),
                "parsed_resume": None,
                "traces": orchestration_trace,
                "processing_time_ms": round(total_duration, 1),
            }

        return {
            "request_id": request_id,
            "status": "success",
            "parsed_resume": result_state["parsed_resume"],
            "traces": orchestration_trace,
            "processing_time_ms": round(total_duration, 1),
        }

    async def process_and_match(
        self,
        file_content: bytes,
        filename: str,
        job: JobDescriptionRequest,
        threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """Process a resume and match against a job description via LangGraph."""
        request_id = str(uuid.uuid4())
        start_time = time.time()

        initial_state: ResumeState = {
            "request_id": request_id,
            "file_content": file_content,
            "filename": filename,
            "parsed_resume": None,
            "job": job,
            "match_threshold": threshold,
            "match_result": None,
            "traces": [],
            "status": "pending",
            "error": None,
            "start_time": start_time,
        }

        result_state = await self.full_pipeline_graph.ainvoke(initial_state)

        total_duration = (time.time() - start_time) * 1000
        traces = result_state.get("traces", [])

        orchestration_trace = OrchestrationTrace(
            request_id=request_id,
            total_duration_ms=round(total_duration, 1),
            agent_traces=traces,
            status=result_state.get("status", "failed"),
        )

        return {
            "request_id": request_id,
            "status": "success" if result_state.get("match_result") else result_state.get("status", "failed"),
            "parsed_resume": result_state.get("parsed_resume"),
            "match_result": result_state.get("match_result"),
            "traces": orchestration_trace,
            "processing_time_ms": round(total_duration, 1),
        }

    async def match_candidate(
        self,
        parsed_resume: ParsedResume,
        job: JobDescriptionRequest,
        threshold: float = 0.5,
    ) -> Dict[str, Any]:
        """Match an already-parsed candidate against a job description."""
        request_id = str(uuid.uuid4())
        start_time = time.time()

        initial_state: ResumeState = {
            "request_id": request_id,
            "file_content": b"",
            "filename": "",
            "parsed_resume": parsed_resume,
            "job": job,
            "match_threshold": threshold,
            "match_result": None,
            "traces": [],
            "status": "normalized",
            "error": None,
            "start_time": start_time,
        }

        result_state = await self.match_only_graph.ainvoke(initial_state)

        total_duration = (time.time() - start_time) * 1000
        traces = result_state.get("traces", [])

        return {
            "request_id": request_id,
            "status": "success" if result_state.get("match_result") else "failed",
            "match_result": result_state.get("match_result"),
            "processing_time_ms": round(total_duration, 1),
            "trace": traces[-1] if traces else None,
        }

    async def process_batch(
        self,
        files: List[Dict[str, Any]],
        callback=None,
    ) -> Dict[str, Any]:
        """Process multiple resumes concurrently with LangGraph.

        Args:
            files: List of {"content": bytes, "filename": str}
            callback: Optional async callback for progress updates
        """
        batch_id = str(uuid.uuid4())
        start_time = time.time()
        results = []
        errors = []

        logger.info(f"[Batch {batch_id}] Starting batch processing of {len(files)} files")

        semaphore = asyncio.Semaphore(self.BATCH_CONCURRENCY)

        async def process_one(file_info: Dict, index: int):
            async with semaphore:
                try:
                    result = await self.process_resume(
                        file_info["content"], file_info["filename"]
                    )
                    result["file_index"] = index
                    result["filename"] = file_info["filename"]

                    if callback:
                        await callback(batch_id, index, len(files), "processed")

                    return result
                except Exception as e:
                    error = {
                        "file_index": index,
                        "filename": file_info["filename"],
                        "error": str(e),
                    }
                    logger.error(f"[Batch {batch_id}] Error processing {file_info['filename']}: {e}")

                    if callback:
                        await callback(batch_id, index, len(files), "failed")

                    return {"status": "failed", **error}

        tasks = [process_one(f, i) for i, f in enumerate(files)]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in all_results:
            if isinstance(r, Exception):
                errors.append({"error": str(r)})
            elif isinstance(r, dict) and r.get("status") == "failed":
                errors.append(r)
            else:
                results.append(r)

        total_duration = (time.time() - start_time) * 1000

        logger.info(
            f"[Batch {batch_id}] Complete: {len(results)} success, {len(errors)} failed in {total_duration:.0f}ms"
        )

        return {
            "batch_id": batch_id,
            "status": "completed",
            "total_files": len(files),
            "processed_files": len(results),
            "failed_files": len(errors),
            "results": results,
            "error_log": errors,
            "processing_time_ms": round(total_duration, 1),
        }


# Singleton
_orchestrator = None


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = Orchestrator()
    return _orchestrator
