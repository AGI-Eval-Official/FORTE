"""FORTE grading engine.

Host-side wrapper around the in-container judge (judge/grade.py): turn the
judge's `judge_outcome` dict into a `GradeResult`, plus the dispatch helpers
(`grade_task`, `pass_k_stats`) and the in-container launcher
(`run_incontainer_judge`).
"""

from __future__ import annotations

import json
import logging
import os
import re
import sys
import urllib.request
import urllib.error
import time
from math import comb
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from lib_agent import ensure_agent_exists, run_openclaw_prompt, slugify_model
from lib_tasks import Task

# Make the judge package importable. scripts/ is
# on sys.path (script dir), but the judge package lives one level up at the repo
# root, so we add it explicitly.
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


logger = logging.getLogger(__name__)

OPENCLAW_ENV_FILE = Path(__file__).parent.parent / "openclaw_config" / ".env"

DEFAULT_JUDGE_MODEL = "claude-opus-4-5-20251101"
DEFAULT_JUDGE_AGENT_PREFIX = "bench-judge"
DEFAULT_JUDGE_TIMEOUT_SECONDS = 1800
JUDGE_API_MAX_RETRIES = 100
JUDGE_API_RETRY_BASE_SECONDS = 5

# Threshold for the penalized hybrid scoring (default):
# if auto_score < this value, the LLM judge contribution is zeroed out.
AUTO_PENALTY_THRESHOLD = 0.75

def _load_openclaw_env(env_file: Path = OPENCLAW_ENV_FILE) -> Dict[str, str]:
    """Parse KEY=VALUE pairs from openclaw_config/.env (ignores comments and blank lines)."""
    env = {}
    if not env_file.exists():
        return env
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    return env


def _call_llm_judge_api(
    prompt: str,
    model: str,
    base_url: str,
    api_key: str,
    timeout_seconds: float = DEFAULT_JUDGE_TIMEOUT_SECONDS,
) -> str:
    """Call an OpenAI-compatible chat completions API using only stdlib.

    Returns the assistant message content.
    """
    url = base_url.rstrip("/") + "/chat/completions"
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 20480
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout_seconds) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
        raise RuntimeError(
            f"LLM judge API returned {exc.code}: {error_body}"
        ) from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"LLM judge API request failed: {exc}") from exc

    choices = body.get("choices", [])
    if not choices:
        raise RuntimeError(f"LLM judge API returned no choices: {body}")
    return choices[0].get("message", {}).get("content", "")


@dataclass
class GradeResult:
    task_id: str
    score: float
    max_score: float
    grading_type: str
    breakdown: Dict[str, float]
    notes: str
    # score_simple: simple weighted average for hybrid tasks (auto * w + llm * w) / total.
    # None means the task is not hybrid (score_simple == score in that case).
    score_simple: Optional[float] = None
    # extra: non-serialized side-channel for the LLM judge artifacts (rendered
    # system/user prompt, image/pdf manifest, per-rubric results). benchmark.py
    # writes this to judge_prompt.json; it is intentionally NOT in to_dict() so
    # grading.json stays compact.
    extra: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "score": self.score,
            "score_simple": self.score_simple if self.score_simple is not None else self.score,
            "max_score": self.max_score,
            "grading_type": self.grading_type,
            "breakdown": self.breakdown,
            "notes": self.notes,
        }


def grade_task(
    *,
    task: Task,
    execution_result: Dict[str, Any],
    skill_dir: Path,
    judge_model: str = DEFAULT_JUDGE_MODEL,
    judge_agent_prefix: str = DEFAULT_JUDGE_AGENT_PREFIX,
    judge_timeout_seconds: float = DEFAULT_JUDGE_TIMEOUT_SECONDS,
    verbose: bool = False,
) -> GradeResult:
    grading_type = task.grading_type
    if verbose:
        logger.info("   [VERBOSE] Grading task %s with type: %s", task.task_id, grading_type)
        logger.info("   [VERBOSE] Execution status: %s", execution_result.get("status", "unknown"))
    
    if grading_type == "automated":
        result = _grade_automated(task, execution_result, verbose=verbose)
        if verbose:
            logger.info("   [VERBOSE] Automated grade breakdown: %s", result.breakdown)
        return result
    if grading_type == "llm_judge":
        result = _grade_llm_judge(
            task=task,
            execution_result=execution_result,
            judge_model=judge_model,
            judge_agent_prefix=judge_agent_prefix,
            judge_timeout_seconds=judge_timeout_seconds,
            skill_dir=skill_dir,
            verbose=verbose,
        )
        if verbose:
            logger.info("   [VERBOSE] LLM judge breakdown: %s", result.breakdown)
        return result
    if grading_type == "hybrid":
        auto_result = _grade_automated(task, execution_result, verbose=verbose)
        llm_result = _grade_llm_judge(
            task=task,
            execution_result=execution_result,
            judge_model=judge_model,
            judge_agent_prefix=judge_agent_prefix,
            judge_timeout_seconds=judge_timeout_seconds,
            skill_dir=skill_dir,
            verbose=verbose,
        )
        return _combine_grades(task, auto_result, llm_result)
    raise ValueError(f"Unknown grading type: {grading_type}")


def _grade_automated(task: Task, execution_result: Dict[str, Any], verbose: bool = False) -> GradeResult:
    grading_code = _extract_grading_code(task)
    if not grading_code:
        return GradeResult(
            task_id=task.task_id,
            score=0.0,
            max_score=1.0,
            grading_type="automated",
            breakdown={},
            notes="No automated grading code found",
        )

    namespace: Dict[str, Any] = {}
    exec(grading_code, namespace)
    grade_func = namespace.get("grade")
    if not callable(grade_func):
        return GradeResult(
            task_id=task.task_id,
            score=0.0,
            max_score=1.0,
            grading_type="automated",
            breakdown={},
            notes="Automated grading function missing",
        )

    scores = grade_func(
        execution_result.get("transcript", []),
        execution_result.get("workspace", ""),
    )
    if not isinstance(scores, dict):
        scores = {}
    
    if verbose:
        logger.info("   [VERBOSE] Automated grading scores: %s", scores)

    total = _average_scores(scores)
    return GradeResult(
        task_id=task.task_id,
        score=total,
        max_score=1.0,
        grading_type="automated",
        breakdown=_normalize_score_dict(scores),
        notes="",
    )


def _openclaw_transcript_to_messages(transcript: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Flatten an OpenClaw JSONL transcript to the {role, content:str} message list
    that the judge's extract_model_response expects.

    OpenClaw stores message content as a list of typed blocks (text / thinking /
    toolCall / ...). We join the text blocks (and wrap any thinking block in
    <think>...</think> so `split("</think>")[-1]` still discards reasoning).
    """
    messages: List[Dict[str, Any]] = []
    for entry in transcript:
        if entry.get("type") != "message":
            continue
        msg = entry.get("message", {})
        role = msg.get("role")
        content = msg.get("content")
        if isinstance(content, list):
            parts: List[str] = []
            for item in content:
                if isinstance(item, dict):
                    itype = item.get("type")
                    if itype == "text":
                        parts.append(item.get("text", ""))
                    elif itype == "thinking":
                        think = item.get("thinking") or item.get("text") or ""
                        if think:
                            parts.append(f"<think>{think}</think>")
                elif isinstance(item, str):
                    parts.append(item)
            content_str: Optional[str] = "".join(parts)
        elif isinstance(content, str):
            content_str = content
        else:
            content_str = None
        messages.append({"role": role, "content": content_str})
    return messages


def _grade_llm_judge(
    *,
    task: Task,
    execution_result: Dict[str, Any],
    judge_model: str,
    judge_agent_prefix: str,
    judge_timeout_seconds: float,
    skill_dir: Path,
    verbose: bool = False,
) -> GradeResult:
    """All-or-nothing LLM-judge grading from the in-container judge outcome.

    The judge itself (grade_one) runs INSIDE the agent container — see
    run_incontainer_judge below, called from lib_docker.execute_task_in_docker
    before teardown. This function just turns the precomputed `judge_outcome`
    dict into a GradeResult. score is 1 iff every rubric passes; the host
    process does no judge work of its own.
    """
    outcome = execution_result.get("judge_outcome")
    if not outcome:
        # No in-container outcome: either grading_type wasn't llm/hybrid (shouldn't
        # reach here) or the container judge step never produced a result.
        return GradeResult(
            task_id=task.task_id, score=0.0, max_score=1.0, grading_type="llm_judge",
            breakdown={}, notes="No in-container judge outcome produced",
        )

    if outcome.get("error"):
        # call_api exhausted retries or the container step failed — surface
        # so anomaly detection can flag it.
        return GradeResult(
            task_id=task.task_id, score=0.0, max_score=1.0, grading_type="llm_judge",
            breakdown={}, notes=f"Grading failed: {outcome['error']}",
            extra=_judge_extra(outcome),
        )

    breakdown: Dict[str, float] = {}
    note_parts: List[str] = []
    if outcome.get("skipped_judge"):
        note_parts.append(
            "Missing required file(s), judge skipped: "
            + ", ".join(outcome.get("missing_files") or [])
        )
    elif outcome.get("result_json"):
        for r in outcome["result_json"].get("results", []):
            rid = str(r.get("rubric_id", "?"))
            passed = bool(r.get("pass", False))
            breakdown[rid] = 1.0 if passed else 0.0
            if not passed:
                note_parts.append(f"[{rid}] FAIL: {r.get('reason', '')[:200]}")
    note_parts.append(f"all_pass={outcome.get('all_pass', False)}")

    return GradeResult(
        task_id=task.task_id,
        score=float(outcome.get("score", 0)),
        max_score=1.0,
        grading_type="llm_judge",
        breakdown=breakdown,
        notes=" | ".join(note_parts),
        extra=_judge_extra(outcome),
    )


# In-container judge timeout (s). Generous: the judge call retries with backoff
# and may convert office files via LibreOffice before the network call.
JUDGE_EXEC_TIMEOUT = 3600
# Where the judge package + IO files land inside the container.
_CONTAINER_JUDGE_PKG_ROOT = "/opt/lcjudge"
_CONTAINER_SOLUTION_DIR = "/workspace/solution"
_CONTAINER_INPUT_ROOT = "/workspace/input"
_CONTAINER_INPUTS_JSON = "/tmp/lcjudge_inputs.json"
_CONTAINER_OUT_JSON = "/tmp/lcjudge_out.json"


def run_incontainer_judge(container, task: Task, transcript, verbose: bool = False):
    """Run grade_one INSIDE the live agent container; return the outcome dict.

    Called by lib_docker.execute_task_in_docker after the workspace snapshot and
    before container teardown (solution/ is copied in only now, after the agent
    finished — the agent never sees it). The judge reads /workspace/input LIVE
    in the container (path_map is the identity map: virtual == real inside the
    container) and /workspace/solution (copied here). Returns None when the
    task is not judge-graded; an {"error": ...} dict on any failure.

    """
    if task.grading_type not in ("llm_judge", "hybrid"):
        return None

    fm = task.frontmatter or {}
    rubrics_list = fm.get("rubrics") or []
    file_paths = fm.get("rubric_file_paths") or []
    if not rubrics_list:
        return {"error": "No rubrics found in task frontmatter", "system_prompt": "",
                "user_prompt": "", "image_count": 0, "pdf_count": 0,
                "skipped_judge": False, "missing_files": [], "all_pass": False,
                "result_json": None, "judge_raw_response": ""}

    model_response = _extract_model_response_from_messages(transcript)

    # Copy the judge-only solution tree into the container now (post-agent).
    # `docker cp <dir> <container>:/workspace/solution` with a non-existent dest
    # creates /workspace/solution with the source's CONTENTS (no extra nesting).
    if task.file_path is not None:
        solution_host = task.file_path.resolve().parent.parent / "assets" / task.task_id / "solution"
        if solution_host.is_dir():
            container.copy_to(solution_host, _CONTAINER_SOLUTION_DIR)
            # docker cp lands files root-owned, but the judge runs as node (1000)
            # and the PDF conversion writes a .trans/ dir next to the source, so
            # node must own the solution tree.
            container.exec(["chown", "-R", "1000:1000", _CONTAINER_SOLUTION_DIR], user="0")

    # Copy the judge package in (not baked into the image, so judge edits need no
    # rebuild). The pinned deps ARE in the image (docker/judge-requirements.txt).
    container.exec(["mkdir", "-p", _CONTAINER_JUDGE_PKG_ROOT], user="0")
    container.copy_to(_REPO_ROOT / "judge", f"{_CONTAINER_JUDGE_PKG_ROOT}/judge")

    # Identity path_map: inside the container the virtual roots ARE the real dirs.
    path_map = {
        "/workspace/input": _CONTAINER_INPUT_ROOT,
        "/workspace/solution": _CONTAINER_SOLUTION_DIR,
    }

    # JUDGE_MODEL from .env (if present) is the source of truth for the judge
    # model id recorded in the payload; the container env also carries it.
    host_env = _load_openclaw_env()
    judge_model_id = host_env.get("JUDGE_MODEL") or None

    payload = {
        "instruction": task.prompt,
        "model_response": model_response,
        "file_paths": file_paths,
        "rubrics_list": rubrics_list,
        "path_map": path_map,
        "use_code_exec": False,
        "model_name": judge_model_id,
    }

    import tempfile
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tf:
        json.dump(payload, tf, ensure_ascii=False)
        inputs_host = Path(tf.name)
    try:
        container.copy_to(inputs_host, _CONTAINER_INPUTS_JSON)
    finally:
        inputs_host.unlink(missing_ok=True)
    # docker cp preserves the host temp file's 0600/root perms; the judge runs as
    # node (1000), so make the inputs readable by it.
    container.exec(["chown", "1000:1000", _CONTAINER_INPUTS_JSON], user="0")

    cmd = (
        f"PYTHONPATH={_CONTAINER_JUDGE_PKG_ROOT} python3 -m judge._container_entry "
        f"{_CONTAINER_INPUTS_JSON} {_CONTAINER_OUT_JSON}"
    )
    proc = container.exec(["sh", "-c", cmd], timeout=JUDGE_EXEC_TIMEOUT)
    if proc.returncode != 0:
        return {"error": f"in-container judge exited {proc.returncode}: "
                         f"{(proc.stderr or proc.stdout or '')[:500]}",
                "system_prompt": "", "user_prompt": "", "image_count": 0,
                "pdf_count": 0, "skipped_judge": False, "missing_files": [],
                "all_pass": False, "result_json": None, "judge_raw_response": ""}

    with tempfile.TemporaryDirectory() as td:
        out_host = Path(td) / "out.json"
        container.copy_from(_CONTAINER_OUT_JSON, out_host)
        if not out_host.exists():
            return {"error": "in-container judge produced no output JSON",
                    "system_prompt": "", "user_prompt": "", "image_count": 0,
                    "pdf_count": 0, "skipped_judge": False, "missing_files": [],
                    "all_pass": False, "result_json": None, "judge_raw_response": ""}
        try:
            outcome = json.loads(out_host.read_text(encoding="utf-8"))
        except (ValueError, OSError) as exc:
            return {"error": f"could not parse in-container judge output: {exc}",
                    "system_prompt": "", "user_prompt": "", "image_count": 0,
                    "pdf_count": 0, "skipped_judge": False, "missing_files": [],
                    "all_pass": False, "result_json": None, "judge_raw_response": ""}

    if verbose:
        logger.info(
            "   [VERBOSE] in-container judge: score=%s all_pass=%s skipped=%s",
            outcome.get("score"), outcome.get("all_pass"), outcome.get("skipped_judge"),
        )
    return outcome


def _extract_model_response_from_messages(transcript: List[Dict[str, Any]]) -> str:
    """Extract the agent's final text response from the run transcript.
    
    """
    messages = _openclaw_transcript_to_messages(transcript or [])
    try:
        parts: List[str] = []
        for msg in messages:
            if msg.get("role") == "assistant" and "content" in msg:
                content = msg["content"]
                if content is None:
                    continue
                if not isinstance(content, str):
                    raise AssertionError("non-string assistant content")
                content = content.split("</think>")[-1].split("</longcat_think>")[-1].strip()
                if content:
                    parts.append(content)
            if msg.get("role") == "user" and "content" in msg:
                uc = msg["content"]
                if isinstance(uc, str) and "Read HEARTBEAT.md" in uc:
                    break
        return "\n".join(parts)
    except AssertionError:
        # Defensive: a non-string content slipped through; fall back to empty.
        logger.warning("extract_model_response assertion failed; using empty response")
        return ""


def _judge_extra(outcome: Dict[str, Any]) -> Dict[str, Any]:
    """Side-channel payload for judge_prompt.json.

    `outcome` is the in-container judge outcome dict (asdict of GradeOutcome).
    """
    return {
        "system_prompt": outcome.get("system_prompt", ""),
        "user_prompt": outcome.get("user_prompt", ""),
        "image_count": outcome.get("image_count", 0),
        "pdf_count": outcome.get("pdf_count", 0),
        "skipped_judge": outcome.get("skipped_judge", False),
        "missing_files": outcome.get("missing_files", []),
        "all_pass": outcome.get("all_pass", False),
        "result_json": outcome.get("result_json"),
        "judge_raw_response": outcome.get("judge_raw_response", ""),
    }



def _combine_grades(task: Task, auto_result: GradeResult, llm_result: GradeResult) -> GradeResult:
    weights = task.grading_weights or {"automated": 0.5, "llm_judge": 0.5}
    auto_weight = float(weights.get("automated", 0.5))
    llm_weight = float(weights.get("llm_judge", 0.5))
    total_weight = auto_weight + llm_weight
    if total_weight <= 0:
        auto_weight = llm_weight = 0.5
        total_weight = 1.0
    score_simple = (
        auto_result.score * auto_weight + llm_result.score * llm_weight
    ) / total_weight

    # Default (penalized): zero out LLM contribution when auto_score <= threshold
    llm_adj = 0.0 if auto_result.score < AUTO_PENALTY_THRESHOLD else llm_result.score
    score = (auto_result.score * auto_weight + llm_adj * llm_weight) / total_weight

    breakdown = {
        **{f"automated.{k}": v for k, v in auto_result.breakdown.items()},
        **{f"llm_judge.{k}": v for k, v in llm_result.breakdown.items()},
    }
    notes = " | ".join(filter(None, [auto_result.notes, llm_result.notes]))
    return GradeResult(
        task_id=task.task_id,
        score=score,
        score_simple=score_simple,
        max_score=1.0,
        grading_type="hybrid",
        breakdown=breakdown,
        notes=notes,
    )


def _extract_grading_code(task: Task) -> str:
    if not task.automated_checks:
        return ""
    # Match until ``` at line start (code block end), not ``` inside the code
    match = re.search(r"```python\s*\n(.*?)\n\s*```", task.automated_checks, re.DOTALL)
    if not match:
        return ""
    return match.group(1)


def _average_scores(scores: Dict[str, Any]) -> float:
    values = [float(v) for v in scores.values() if isinstance(v, (int, float))]
    if not values:
        return 0.0
    return sum(values) / len(values)


def strict_accuracy_stats(means: List[float]) -> Tuple[float, int]:
    """Strict accuracy (满分率): fraction of tasks with mean score == 1.0.

    Returns (rate in [0, 1], count of perfect tasks). Empty input -> (0.0, 0).
    """
    n = len(means)
    if n == 0:
        return 0.0, 0
    perfect = sum(1 for m in means if float(m) >= 1.0 - 1e-9)
    return perfect / n, perfect


def _pass_at_k(n: int, c: int, k: int) -> float:
    """Unbiased pass@k: prob at least 1 of k sampled runs is perfect."""
    if n < k:
        return 0.0
    if c >= n:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def _pass_pow_k(n: int, c: int, k: int) -> float:
    """pass^k: prob all k sampled runs are perfect."""
    if n < k:
        return 0.0
    return comb(c, k) / comb(n, k)


def pass_k_stats(grades_by_task_id: Dict[str, Any], runs_per_task: int) -> Dict[str, Any]:
    """Return pass@k and pass^k (macro avg and task count) for k=1..runs_per_task."""
    result: Dict[str, Any] = {}
    for k in range(1, runs_per_task + 1):
        at_vals: List[float] = []
        pow_vals: List[float] = []
        for g in grades_by_task_id.values():
            runs = g.get("runs", [])
            n = len(runs)
            c = sum(1 for r in runs if r.get("score", 0) >= 1.0 - 1e-9)
            at_vals.append(_pass_at_k(n, c, k))
            pow_vals.append(_pass_pow_k(n, c, k))
        result[f"pass@{k}"] = round(sum(at_vals) / len(at_vals), 4) if at_vals else 0.0
        result[f"pass^{k}"] = round(sum(pow_vals) / len(pow_vals), 4) if pow_vals else 0.0
        result[f"pass@{k}_count"] = sum(1 for v in at_vals if v >= 1.0 - 1e-9)
        result[f"pass^{k}_count"] = sum(1 for v in pow_vals if v >= 1.0 - 1e-9)
    return result


def _normalize_score_dict(scores: Dict[str, Any]) -> Dict[str, float]:
    normalized: Dict[str, float] = {}
    for key, value in scores.items():
        try:
            normalized[str(key)] = float(value)
        except (TypeError, ValueError):
            continue
    return normalized


def _format_grading_criteria(task: Task) -> str:
    if not task.grading_criteria:
        return ""
    return "\n".join(f"- {criterion}" for criterion in task.grading_criteria)


def _summarize_transcript(transcript: List[Dict[str, Any]]) -> str:
    summary_parts: List[str] = []
    for event in transcript:
        if event.get("type") != "message":
            continue
        msg = event.get("message", {})
        role = msg.get("role")
        if role == "assistant":
            for item in msg.get("content", []):
                if item.get("type") == "toolCall":
                    summary_parts.append(
                        f"Tool: {item.get('name')}({json.dumps(item.get('arguments', {}))})"
                    )
        elif role == "toolResult":
            content = msg.get("content", [])
            if content:
                result_preview = str(content[0])[:200]
                summary_parts.append(f"Result: {result_preview}")
        elif role == "user":
            content = msg.get("content", [])
            if content:
                summary_parts.append(f"User: {content[0]}")
    return "\n".join(summary_parts)


def _build_judge_prompt(task: Task, transcript_summary: str, rubric: str) -> str:
    return (
        "You are a grading function. Your ONLY job is to output a single JSON object.\n\n"
        "CRITICAL RULES:\n"
        "- Do NOT use any tools (no Read, Write, exec, or any other tool calls)\n"
        "- Do NOT create files or run commands\n"
        "- Do NOT write any prose, explanation, or commentary outside the JSON\n"
        "- Respond with ONLY a JSON object — nothing else\n\n"
        "Be a strict evaluator. Reserve 1.0 for genuinely excellent performance. "
        "An average acceptable completion should score around 0.6-0.7. "
        "Deduct points for unnecessary steps, verbose output, and inefficient tool usage.\n\n"
        "## Task\n"
        f"{task.prompt}\n\n"
        "## Expected Behavior\n"
        f"{task.expected_behavior}\n\n"
        "## Agent Transcript (summarized)\n"
        f"{transcript_summary}\n\n"
        "## Grading Rubric\n"
        f"{rubric}\n\n"
        "Score each criterion from 0.0 to 1.0.\n\n"
        "Respond with ONLY this JSON structure (no markdown, no code fences, no extra text):\n"
        '{"scores": {"criterion_name": 0.0}, "total": 0.0, "notes": "brief justification"}'
    )


def _ensure_judge_agent(judge_agent_prefix: str, judge_model: str, skill_dir: Path) -> str:
    model_slug = slugify_model(judge_model)
    agent_id = f"{judge_agent_prefix}-{model_slug}"
    workspace = Path("/tmp/forte/judge/workspace")
    ensure_agent_exists(agent_id, judge_model, workspace)
    return agent_id


def _parse_judge_response(transcript: List[Dict[str, Any]]) -> Dict[str, Any]:
    content_chunks: List[str] = []
    for event in transcript:
        if event.get("type") != "message":
            continue
        msg = event.get("message", {})
        if msg.get("role") != "assistant":
            continue
        for item in msg.get("content", []):
            if item.get("type") == "text":
                content_chunks.append(item.get("text", ""))
    raw_text = "\n".join(content_chunks).strip()
    if not raw_text:
        return {}

    # First, try to extract JSON from code blocks (```json ... ```)
    code_block_match = re.search(r"```json\s*(.*?)\s*```", raw_text, re.DOTALL)
    if code_block_match:
        try:
            parsed = json.loads(code_block_match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    # Find all potential JSON objects by looking for balanced braces
    # We'll extract chunks that start with { and try to parse them
    json_candidates: List[str] = []
    brace_depth = 0
    current_json = []
    for char in raw_text:
        if char == "{":
            if brace_depth == 0:
                current_json = []
            brace_depth += 1

        if brace_depth > 0:
            current_json.append(char)

        if char == "}":
            brace_depth -= 1
            if brace_depth == 0 and current_json:
                json_candidates.append("".join(current_json))

    # Try parsing from the last JSON object backwards (most recent response)
    for candidate in reversed(json_candidates):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and "scores" in parsed:
                # Prefer JSON that has the expected structure
                return parsed
        except json.JSONDecodeError:
            continue

    # Try any valid JSON dict
    for candidate in reversed(json_candidates):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    # Fallback: try to extract numeric scores from prose responses.
    # Models sometimes return "Total: 0.72" or "Overall score: 0.65" instead of JSON.
    score_pattern = re.search(
        r"(?:total|overall|final)\s*(?:score)?[:\s]*(0\.\d+|1\.0+)",
        raw_text,
        re.IGNORECASE,
    )
    if score_pattern:
        try:
            total = float(score_pattern.group(1))
            if 0.0 <= total <= 1.0:
                logger.warning(
                    "Fell back to regex score extraction from prose (total=%.2f)", total
                )
                return {"scores": {}, "total": total, "notes": "Score extracted from prose (JSON parse failed)"}
        except ValueError:
            pass

    logger.warning("Failed to parse judge JSON response")
    return {}

def _parse_judge_text_response(raw_text: str) -> Dict[str, Any]:
    """Parse a JSON grading response from raw LLM text output.

    Handles markdown code fences, extra prose around JSON, and fallback
    regex extraction for non-JSON responses.
    """
    raw_text = raw_text.strip()
    if not raw_text:
        return {}

    # Try code block first (```json ... ```)
    code_block_match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw_text, re.DOTALL)
    if code_block_match:
        try:
            parsed = json.loads(code_block_match.group(1))
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

    # Find balanced-brace JSON objects
    json_candidates: List[str] = []
    brace_depth = 0
    current_json: List[str] = []
    for char in raw_text:
        if char == "{":
            if brace_depth == 0:
                current_json = []
            brace_depth += 1
        if brace_depth > 0:
            current_json.append(char)
        if char == "}":
            brace_depth -= 1
            if brace_depth == 0 and current_json:
                json_candidates.append("".join(current_json))

    # Prefer JSON with expected "scores" key
    for candidate in reversed(json_candidates):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict) and "scores" in parsed:
                return parsed
        except json.JSONDecodeError:
            continue

    # Any valid JSON dict
    for candidate in reversed(json_candidates):
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    # Fallback: regex for numeric total from prose
    score_pattern = re.search(
        r"(?:total|overall|final)\s*(?:score)?[:\s]*(0\.\d+|1\.0+)",
        raw_text,
        re.IGNORECASE,
    )
    if score_pattern:
        try:
            total = float(score_pattern.group(1))
            if 0.0 <= total <= 1.0:
                logger.warning(
                    "Fell back to regex score extraction from prose (total=%.2f)", total
                )
                return {
                    "scores": {},
                    "total": total,
                    "notes": "Score extracted from prose (JSON parse failed)",
                }
        except ValueError:
            pass

    logger.warning("Failed to parse judge text response as JSON")
    return {}



def _normalize_judge_response(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize judge response to expected format with 'scores', 'total', and 'notes'.
    
    Handles various response formats:
    - {"scores": {...}, "total": 0.9, "notes": "..."}  (expected)
    - {"criteria_scores": {...}, ...}  (Claude sometimes uses this)
    - {"score": 0.9, "justification": "..."}  (simplified format)
    """
    result: Dict[str, Any] = {"scores": {}, "total": None, "notes": ""}
    
    # Extract scores from various keys
    if "scores" in parsed:
        scores_data = parsed["scores"]
        if isinstance(scores_data, dict):
            # Handle nested structure: {"criterion": {"score": 0.9, "weight": 0.3}}
            for key, value in scores_data.items():
                if isinstance(value, dict) and "score" in value:
                    result["scores"][key] = float(value["score"]) if isinstance(value["score"], (int, float, str)) else value["score"]
                elif isinstance(value, (int, float)):
                    result["scores"][key] = value
    elif "criteria_scores" in parsed:
        # Handle Claude's alternate format
        criteria = parsed["criteria_scores"]
        if isinstance(criteria, dict):
            for key, value in criteria.items():
                if isinstance(value, dict) and "score" in value:
                    result["scores"][key] = value["score"]
                elif isinstance(value, (int, float)):
                    result["scores"][key] = value
    
    # Extract total score
    if "total" in parsed and parsed["total"] is not None:
        result["total"] = float(parsed["total"]) if isinstance(parsed["total"], (int, float)) else None
    elif "score" in parsed and isinstance(parsed["score"], (int, float)):
        result["total"] = float(parsed["score"])
    elif result["scores"]:
        # Calculate average if we have individual scores but no total
        values = [v for v in result["scores"].values() if isinstance(v, (int, float))]
        if values:
            result["total"] = sum(values) / len(values)
    
    # Extract notes/justification
    if "notes" in parsed:
        result["notes"] = str(parsed["notes"])
    elif "justification" in parsed:
        result["notes"] = str(parsed["justification"])
    elif "reasoning" in parsed:
        result["notes"] = str(parsed["reasoning"])
    
    return result
