#!/usr/bin/env python3
"""FORTE runner: drives docker containers per (model, task, run).

    python scripts/benchmark.py --model your-gateway/claude-sonnet-4.6 --dataset ./data --concurrency 10
"""

import argparse
import json
import logging
import os
import statistics
import subprocess
import shutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from concurrent.futures import Future, ThreadPoolExecutor, wait, FIRST_COMPLETED

from lib_agent import slugify_model, THINKING_LEVELS, validate_thinking_level
from lib_anomalies import detect_anomalies
from lib_docker import execute_task_in_docker, cleanup_containers, DEFAULT_IMAGE
from lib_grading import (
    GradeResult,
    grade_task,
    pass_k_stats,
    _load_openclaw_env,
    _openclaw_transcript_to_messages,
)
from lib_tasks import Task, TaskLoader


MAX_RUN_ATTEMPTS = 3
# Configure logging (file handler added later once model/dataset are known)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("benchmark")

# Docker workspace snapshots are restricted to this directory for safety
_WORKSPACE_SNAPSHOT_ROOT = Path("/tmp/forte").resolve()

_OPENCLAW_PROVIDER_APIS = {
    "openai-completions",
    "openai-responses",
    "openai-chatgpt-responses",
    "anthropic-messages",
    "google-generative-ai",
    "google-vertex",
    "github-copilot",
    "bedrock-converse-stream",
    "ollama",
    "azure-openai-responses",
}


@dataclass
class ModelCtx:
    """Per-model batch state.

    A single benchmark invocation can drive several models in one shared
    concurrency pool (the global flat work-pool). Each model still owns its own
    output dir, resume state, and aggregation — that per-model state lives here,
    keyed by ``model_slug`` in the ``ctxs`` map, so the scheduler can route a
    finished (model, task, run) back to the right bucket.
    """

    model_id: str
    model_slug: str
    thinking_level: Optional[str]
    batch_dir: Path
    output_path: Path
    execution_results: Dict[str, List[tuple]] = field(default_factory=dict)
    results: List[Dict[str, Any]] = field(default_factory=list)
    grades_by_task: Dict[str, Dict[str, Any]] = field(default_factory=dict)


def _write_json(path: Path, obj: Any) -> None:
    """Write JSON to disk, tolerant of lone surrogates in model output.

    Agent transcripts occasionally carry an unpaired UTF-16 surrogate (e.g.
    ``\\ud83d`` — half of an emoji whose low-surrogate was lost mid-stream).
    ``json.dumps(ensure_ascii=False)`` happily emits it, but UTF-8 encoding then
    raises ``UnicodeEncodeError: surrogates not allowed`` and — under the
    ``set -e`` batch wrapper — would kill the entire run. We encode with
    ``surrogatepass`` and decode back with ``replace`` so the bad code unit
    becomes U+FFFD instead of crashing the write.
    """
    text = json.dumps(obj, indent=2, ensure_ascii=False)
    data = text.encode("utf-8", "surrogatepass").decode("utf-8", "replace").encode("utf-8")
    path.write_bytes(data)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="FORTE Runner")
    parser.add_argument(
        "--model",
        required=False,
        help=(
            "Model identifier (e.g. dashscope/qwen3.6-plus). If omitted, "
            "uses agents.defaults.model.primary from openclaw_config/openclaw.json. "
            "Accepts a comma-separated list to run several models in one shared "
            "concurrency pool, e.g. 'your-gateway/claude-sonnet-4.6."
        ),
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="./data",
        help=(
            "Path to a dataset directory containing tasks/ (one .md per task) "
            "and assets/<task_id>/{input,solution[,skills]}/. Defaults to ./data."
        ),
    )
    parser.add_argument(
        "--output-dir",
        default="results",
        help="Results directory"
    )
    parser.add_argument(
        "--task",
        type=str,
        default=None,
        help="Single task ID shorthand; sets --suite=TASK_ID",
    )
    parser.add_argument(
        "--suite",
        default="all",
        help='Tasks to run: "all", "automated-only", or comma-separated task IDs',
    )
    parser.add_argument(
        "--concurrency",
        "-c",
        type=int,
        default=1,
        help="Max concurrent Docker containers"
    )
    parser.add_argument(
        "--docker-image",
        default=DEFAULT_IMAGE, 
        help="Docker image (default: %s)" % DEFAULT_IMAGE
    )
    parser.add_argument(
        "--timeout-multiplier",
        type=float,
        default=1.0,
        help="Scale all task timeouts"
    )
    parser.add_argument(
        "--runs",
        type=int,
        default=3,
        help="Number of runs per task for averaging"
    )
    parser.add_argument(
        "--judge",
        default=None,
        help="Judge model identifier (default: anthropic/claude-opus-4.5)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Verbose logging"
    )
    parser.add_argument(
        "--no-grade",
        action="store_true",
        help="Skip grading, only execute"
    )
    parser.add_argument(
        "--thinking",
        type=str,
        default=None,
        help=(
            f"Thinking level to use (e.g. 'low', 'medium', 'high'). "
            f"Valid levels: {', '.join(THINKING_LEVELS)}. "
            "If not specified, runs without an explicit thinking level."
        ),
    )
    parser.add_argument(
        "--no-resume",
        action="store_true",
        help="Force a fresh batch even if a resumable run exists in --output-dir",
    )
    parser.add_argument(
        "--rerun-anomalous",
        action="store_true",
        help="With resume: rerun all previously anomalous runs (WARNING + ERROR level).",
    )
    parser.add_argument(
        "--rerun-error",
        action="store_true",
        help=(
            "With resume: rerun only runs with ERROR-level anomalies (score-impacting failures "
            "such as timeout, crash, empty transcript). Use --rerun-anomalous to also rerun "
            "WARNING-only anomalies (e.g. transient rate limits that did not affect the score)."
        ),
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="Remove all leftover Docker containers and exit",
    )
    parser.add_argument(
        "--log-file",
        default="benchmark.log",
        help="Path to log file (default: benchmark.log)",
    )
    parser.add_argument(
        "--simple-scoring",
        action="store_true",
        help=(
            "Use simple weighted average for hybrid tasks instead of the default penalized scoring "
            "(default: auto≤0.75 → LLM contribution zeroed out)"
        ),
    )
    return parser.parse_args()


def _default_model_from_openclaw_config(config_path: Path) -> Optional[str]:
    """Read the default agent model from openclaw_config/openclaw.json."""
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        logger.warning("Could not parse %s while resolving default model: %s", config_path, exc)
        return None

    primary = (
        config.get("agents", {})
        .get("defaults", {})
        .get("model", {})
        .get("primary")
    )
    if isinstance(primary, str) and primary.strip():
        return primary.strip()
    return None


def _load_openclaw_config(config_path: Path) -> Optional[Dict[str, Any]]:
    try:
        return json.loads(config_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except json.JSONDecodeError as exc:
        logger.error("Could not parse %s: %s", config_path, exc)
        sys.exit(2)


def _preflight_openclaw_config(config_path: Path, model_ids: List[str]) -> None:
    """Fail fast for OpenClaw config issues that would otherwise repeat per run."""
    config = _load_openclaw_config(config_path)
    if config is None:
        logger.error("OpenClaw config not found: %s", config_path)
        sys.exit(2)

    providers = config.get("models", {}).get("providers", {})
    if not isinstance(providers, dict):
        logger.error("OpenClaw config is invalid: models.providers must be an object.")
        sys.exit(2)

    errors: List[str] = []
    for provider_name, provider_cfg in providers.items():
        if not isinstance(provider_cfg, dict):
            errors.append(f"models.providers.{provider_name} must be an object")
            continue
        api = provider_cfg.get("api")
        if api not in _OPENCLAW_PROVIDER_APIS:
            allowed = ", ".join(sorted(_OPENCLAW_PROVIDER_APIS))
            errors.append(
                f"models.providers.{provider_name}.api={api!r} is invalid; "
                f"use one of: {allowed}"
            )

    for model_id in model_ids:
        if "/" not in model_id:
            continue
        provider_name, model_ref = model_id.split("/", 1)
        provider_cfg = providers.get(provider_name)
        if not isinstance(provider_cfg, dict):
            continue
        registered = {
            m.get("id")
            for m in provider_cfg.get("models", [])
            if isinstance(m, dict) and isinstance(m.get("id"), str)
        }
        if registered and model_ref not in registered:
            errors.append(
                f"model {model_id!r} is not registered in "
                f"models.providers.{provider_name}.models[]"
            )

    if errors:
        logger.error("OpenClaw config preflight failed:")
        for err in errors:
            logger.error("  - %s", err)
        sys.exit(2)


def _select_task_ids(tasks: List[Task], suite: str) -> Optional[List[str]]:
    """Select task IDs based on suite specification.

    Args:
        tasks: List of all available tasks
        suite: Suite specification ("all", "automated-only", or comma-separated task IDs)

    Returns:
        None for all tasks, or list of task IDs to run
    """
    if suite == "all":
        return None
    if suite == "automated-only":
        return [t.task_id for t in tasks if t.grading_type == "automated"]
    return [tid.strip() for tid in suite.split(",") if tid.strip()]


def _load_existing_results(
    batch_dir: Path,
    tasks_to_run: List["Task"],
    runs_per_task: int,
    thinking_level: Optional[str],
    rerun_anomalous: bool,
    rerun_error: bool,
    model_slug: str,
    simple_scoring: bool = False,
) -> tuple:
    """Load previously completed run results from grading.json files.

    Args:
        batch_dir: Directory containing previous batch results
        tasks_to_run: List of tasks to execute
        runs_per_task: Number of runs per task
        thinking_level: Thinking level for this run (None = default)
        rerun_anomalous: Whether to rerun all anomalous runs (WARNING + ERROR level)
        rerun_error: Whether to rerun only ERROR-level (score-impacting) anomalous runs
        model_slug: Slugified model identifier

    Returns:
        Tuple of (execution_results, results, grades_by_task, skipped_count).
        Runs that are missing or flagged for rerun are omitted so work_items picks them up.
    """
    execution_results: Dict[str, List[tuple]] = {t.task_id: [] for t in tasks_to_run}
    results: List[Dict[str, Any]] = []
    grades_by_task: Dict[str, Dict[str, Any]] = {}
    skipped_count = 0

    for task in tasks_to_run:
        task_id = task.task_id
        for run_idx in range(runs_per_task):
            folder = _subfolder_name(task_id, run_idx, runs_per_task)
            task_dir = batch_dir / folder
            grading_file = task_dir / "grading.json"

            if not grading_file.exists():
                continue

            try:
                grading_data = json.loads(grading_file.read_text(encoding="utf-8"))
            except Exception:
                logger.warning("Could not read %s — will rerun", grading_file)
                continue

            anomalies = grading_data.get("anomalies", {})
            # --rerun-anomalous: rerun all anomalous runs (WARNING + ERROR)
            if rerun_anomalous and anomalies.get("is_anomalous", False):
                logger.info(
                    "   [resume] %s [%s] run %d is anomalous — will rerun",
                    task_id,
                    thinking_level or "default",
                    run_idx + 1,
                )
                continue
            # --rerun-error: rerun only ERROR-level (score-impacting) runs
            # Compat: old grading.json files use "has_critical", new ones use "has_error"
            has_error = anomalies.get("has_error", anomalies.get("has_critical", False))
            if rerun_error and has_error:
                logger.info(
                    "   [resume] %s [%s] run %d has ERROR anomaly — will rerun",
                    task_id,
                    thinking_level or "default",
                    run_idx + 1,
                )
                continue

            # Reconstruct execution result from saved data
            execution = grading_data.get("execution", {})
            transcript: List[Any] = []
            transcript_file = task_dir / "openclaw_trace.json"
            if transcript_file.exists():
                try:
                    transcript = json.loads(transcript_file.read_text(encoding="utf-8"))
                except Exception:
                    pass

            mock_result: Dict[str, Any] = {
                "agent_id": f"bench-{model_slug}",
                "task_id": task_id,
                "thinking_level": thinking_level,
                "status": execution.get("status", "success"),
                "transcript": transcript,
                "usage": {},
                "workspace": "",
                "exit_code": execution.get("exit_code"),
                "timed_out": execution.get("timed_out", False),
                "prompt_error_retries": execution.get("prompt_error_retries", 0),
                "gateway_prompt_error": execution.get("gateway_prompt_error", False),
                "execution_time": execution.get("execution_time", 0.0),
                "stdout": "",
                "stderr": "",
                "_anomalies": anomalies,
            }

            mock_grade = GradeResult(
                task_id=grading_data["task_id"],
                score=grading_data["score"],
                score_simple=grading_data.get("score_simple"),
                max_score=grading_data.get("max_score", 1.0),
                grading_type=grading_data["grading_type"],
                breakdown=grading_data.get("breakdown", {}),
                notes=grading_data.get("notes", ""),
            )

            execution_results[task_id].append((run_idx, mock_result, mock_grade))
            results.append(mock_result)
            skipped_count += 1

        # Pre-aggregate if all runs for this task are loaded
        task_runs = execution_results[task_id]
        if len(task_runs) == runs_per_task:
            task_grades = [g for _, _, g in task_runs]
            if simple_scoring:
                scores = [g.score_simple if g.score_simple is not None else g.score for g in task_grades]
            else:
                scores = [g.score for g in task_grades]
            grades_by_task[task_id] = {
                "task_id": task_id,
                "thinking_level": thinking_level,
                "runs": [g.to_dict() for g in task_grades],
                "mean": statistics.mean(scores),
                "std": statistics.stdev(scores) if len(scores) > 1 else 0.0,
                "min": min(scores),
                "max": max(scores),
            }

    return execution_results, results, grades_by_task, skipped_count


def _get_git_version(root: Path) -> str:
    """Get short git commit hash for benchmark version tracking."""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2,
            check=False,
            cwd=root,
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        return ""


def _compute_efficiency(
    task_entries: List[Dict[str, Any]],
    grades_by_task_id: Dict[str, Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute efficiency metrics: token usage, cost, and score-per-resource ratios."""
    total_input = total_output = total_tok = total_reqs = 0
    total_cost = total_time = 0.0
    per_task = []

    for entry in task_entries:
        usage = entry.get("usage", {})
        tid = entry["task_id"]
        score = float(grades_by_task_id.get(tid, {}).get("mean", 0.0))
        inp = int(usage.get("input_tokens", 0))
        out = int(usage.get("output_tokens", 0))
        tot = int(usage.get("total_tokens", 0))
        cost = float(usage.get("cost_usd", 0.0) or 0.0)
        reqs = int(usage.get("request_count", 0))
        exec_time = float(entry.get("execution_time", 0.0) or 0.0)

        total_input += inp
        total_output += out
        total_tok += tot
        total_cost += cost
        total_reqs += reqs
        total_time += exec_time
        per_task.append(
            {
                "task_id": tid,
                "score": round(score, 4),
                "total_tokens": tot,
                "cost_usd": round(cost, 6),
                "tokens_per_score_point": round(tot / score, 1) if score > 0 else None,
            }
        )

    all_scores = [float(g.get("mean", 0.0)) for g in grades_by_task_id.values()]
    total_score = sum(all_scores)
    n = len(all_scores)

    return {
        "total_tokens": total_tok,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "total_cost_usd": round(total_cost, 6),
        "total_requests": total_reqs,
        "total_execution_time_seconds": round(total_time, 2),
        "tokens_per_task": round(total_tok / n, 1) if n else 0,
        "cost_per_task_usd": round(total_cost / n, 6) if n else 0,
        "score_per_1k_tokens": (
            round(total_score / (total_tok / 1000), 6) if total_tok > 0 else None
        ),
        "score_per_dollar": round(total_score / total_cost, 4) if total_cost > 0 else None,
        "per_task": per_task,
    }


def _write_anomaly_report(
    batch_dir: Path,
    execution_results: Dict[str, List[tuple]],
    model: str,
    thinking_level: Optional[str] = None,
) -> None:
    """Aggregate per-run anomaly data into a batch-level anomaly_report.json."""
    import datetime

    type_counts: Dict[str, int] = {}
    total_runs = 0
    anomalous_runs = 0
    error_runs = 0
    task_entries = []

    for task_id, runs in execution_results.items():
        task_anomalous = 0
        task_error = 0
        run_anomalies = []
        for run_idx, result, grade in sorted(runs, key=lambda x: x[0]):
            anomalies = result.get("_anomalies", {})
            items = anomalies.get("items", [])
            is_anom = anomalies.get("is_anomalous", False)
            # Compat: old grading.json files use "has_critical", new ones use "has_error"
            has_err = anomalies.get("has_error", anomalies.get("has_critical", False))
            total_runs += 1
            if is_anom:
                anomalous_runs += 1
                task_anomalous += 1
            if has_err:
                error_runs += 1
                task_error += 1
            for item in items:
                type_counts[item["id"]] = type_counts.get(item["id"], 0) + 1
            run_anomalies.append(
                {
                    "run_index": run_idx + 1,
                    "is_anomalous": is_anom,
                    "has_error": has_err,
                    "items": items,
                }
            )
        task_entries.append(
            {
                "task_id": task_id,
                "thinking_level": thinking_level,
                "total_runs": len(runs),
                "anomalous_runs": task_anomalous,
                "error_runs": task_error,
                "has_any_clean_run": task_anomalous < len(runs),
                "run_anomalies": run_anomalies,
            }
        )

    report = {
        "model": model,
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "total_runs": total_runs,
        "anomalous_runs": anomalous_runs,
        "error_runs": error_runs,
        "anomaly_type_counts": dict(sorted(type_counts.items(), key=lambda x: -x[1])),
        "tasks": sorted(task_entries, key=lambda t: (t["task_id"], t.get("thinking_level", ""))),
    }
    out = batch_dir / "anomaly_report.json"
    _write_json(out, report)
    logger.info(
        "📋 Anomaly report: %d/%d runs anomalous (%d error) → %s",
        anomalous_runs,
        total_runs,
        error_runs,
        out,
    )


def _subfolder_name(task_id: str, run_idx: int, runs_per_task: int) -> str:
    """Generate subfolder name for a task run: task_id[_run_N]."""
    parts = [task_id]
    if runs_per_task > 1:
        parts.append(f"run_{run_idx + 1}")
    return "_".join(parts)


def main():
    """Main entry point for the benchmark script."""

    logger.info("🦞🦀🦐 FORTE - OpenClaw Benchmarking")

    args = _parse_args()
    code_dir = Path(__file__).parent.parent

    # Attach file handler now that we know the log path
    log_file = Path(args.log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logging.getLogger().addHandler(file_handler)

    if args.task:
        args.suite = args.task

    # Register cleanup handlers for abnormal exits (Ctrl+C, SIGTERM)
    import atexit
    import signal

    def _cleanup_on_exit(*_args):
        logger.info("🧹 Cleaning up Docker containers...")
        cleanup_containers()

    atexit.register(_cleanup_on_exit)
    signal.signal(signal.SIGINT, lambda *a: (cleanup_containers(), sys.exit(130)))
    signal.signal(signal.SIGTERM, lambda *a: (cleanup_containers(), sys.exit(143)))

    # Handle --cleanup: remove orphan containers and exit
    if args.cleanup:
        n = cleanup_containers()
        logger.info("Cleanup done. Removed %d container(s).", n)
        return

    if not args.model:
        default_model = _default_model_from_openclaw_config(
            code_dir / "openclaw_config" / "openclaw.json"
        )
        if default_model:
            args.model = default_model
            logger.info("No --model supplied; using default model from openclaw_config/openclaw.json")
        else:
            logger.error(
                "--model is required unless openclaw_config/openclaw.json sets "
                "agents.defaults.model.primary."
            )
            sys.exit(2)

    model_ids = [m.strip() for m in args.model.split(",") if m.strip()]
    if not model_ids:
        logger.error("--model is required (unless using --cleanup)")
        sys.exit(2)
    _preflight_openclaw_config(code_dir / "openclaw_config" / "openclaw.json", model_ids)

    # --dataset is a path to a directory containing tasks/ and assets/.
    # Accepts absolute or repo-relative paths; defaults to ./data.
    dataset_path = Path(args.dataset)
    if not dataset_path.is_absolute():
        dataset_path = (code_dir / dataset_path).resolve()
    tasks_dir = dataset_path / "tasks"
    assets_dir = dataset_path / "assets"
    if not tasks_dir.exists():
        logger.error("Tasks directory not found: %s", tasks_dir)
        sys.exit(1)
    if not assets_dir.exists():
        logger.warning("Assets directory not found: %s — continuing without assets", assets_dir)

    # Load tasks
    loader = TaskLoader(tasks_dir)
    all_tasks = loader.load_all_tasks()
    logger.info("Loaded %d tasks from %s", len(all_tasks), tasks_dir)

    task_ids = _select_task_ids(all_tasks, args.suite)
    tasks_to_run = all_tasks if task_ids is None else [t for t in all_tasks if t.task_id in task_ids]
    if not tasks_to_run:
        logger.error("No tasks matched suite '%s'", args.suite)
        sys.exit(1)

    tasks_by_id = {t.task_id: t for t in tasks_to_run}
    # --model accepts a comma-separated list; all models share one concurrency
    # pool (the global flat work-pool). A single model is just a length-1 list,
    # so single-model callers behave exactly as before.
    runs_per_task = max(1, args.runs)
    concurrency = max(1, args.concurrency)

    # Pre-flight: fail fast if LLM judge credentials are missing (model-independent)
    if not args.no_grade:
        judge_tasks = [t for t in tasks_to_run if t.grading_type in ("llm_judge", "hybrid")]
        if judge_tasks:
            host_env = _load_openclaw_env()
            judge_base_url = os.environ.get("JUDGE_BASE_URL") or host_env.get("JUDGE_BASE_URL")
            judge_api_key = os.environ.get("JUDGE_API_KEY") or host_env.get("JUDGE_API_KEY")
            if not judge_base_url or not judge_api_key:
                logger.error(
                    "❌ %d task(s) require an LLM judge (%s) but JUDGE_BASE_URL / JUDGE_API_KEY "
                    "are not set. Add them to openclaw_config/.env or set as environment variables.",
                    len(judge_tasks),
                    ", ".join(t.task_id for t in judge_tasks[:3])
                    + (" ..." if len(judge_tasks) > 3 else ""),
                )
                sys.exit(1)

    # Build batch output directory before execution (for incremental writes)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Per-model setup: validate thinking level, resolve batch dir, detect resume.
    # Each model owns its own output dir + resume state; the scheduler routes a
    # finished (model, task, run) back to the matching ctx by model_slug.
    ctxs: Dict[str, ModelCtx] = {}
    for model_id in model_ids:
        m_slug = slugify_model(model_id)

        m_thinking: Optional[str] = None
        if args.thinking:
            m_thinking = validate_thinking_level(args.thinking.strip(), model_id)
            if m_thinking is None:
                logger.error(
                    "Invalid or incompatible thinking level '%s' for model '%s'. Valid levels: %s",
                    args.thinking,
                    model_id,
                    ", ".join(THINKING_LEVELS),
                )
                sys.exit(2)

        m_batch_dir = output_dir / (f"{m_slug}_{m_thinking}" if m_thinking else m_slug)
        ctx = ModelCtx(
            model_id=model_id,
            model_slug=m_slug,
            thinking_level=m_thinking,
            batch_dir=m_batch_dir,
            output_path=m_batch_dir / "summary.json",
        )

        resumable = not args.no_resume and m_batch_dir.is_dir()
        if resumable:
            logger.info("▶️  Resuming %s from %s", model_id, m_batch_dir)
            (
                ctx.execution_results,
                ctx.results,
                ctx.grades_by_task,
                skipped,
            ) = _load_existing_results(
                m_batch_dir,
                tasks_to_run,
                runs_per_task,
                m_thinking,
                args.rerun_anomalous,
                args.rerun_error,
                m_slug,
                simple_scoring=args.simple_scoring,
            )
            logger.info("   [%s] Skipping %d already-completed run(s)", model_id, skipped)
        else:
            m_batch_dir.mkdir(parents=True, exist_ok=True)
            ctx.execution_results = {t.task_id: [] for t in tasks_to_run}
            ctx.results = []
            ctx.grades_by_task = {}

        ctxs[m_slug] = ctx

    logger.info(
        "🐳 Batch run: %d model(s) × %d tasks × %d runs = %d total, concurrency=%d (shared pool), image=%s",
        len(model_ids),
        len(tasks_to_run),
        runs_per_task,
        len(model_ids) * len(tasks_to_run) * runs_per_task,
        concurrency,
        args.docker_image,
    )
    if args.thinking:
        logger.info("🧠 Thinking level: %s", args.thinking)

    # Build the global flat work list: (model_slug, task, run_index) across ALL
    # models, skipping already-completed runs per model. One exec pool consumes
    # this, so container count stays = concurrency regardless of model count.
    work_items = [
        (slug, task, run_idx)
        for slug, ctx in ctxs.items()
        for task in tasks_to_run
        for run_idx in range(runs_per_task)
        if run_idx not in {r[0] for r in ctx.execution_results.get(task.task_id, [])}
    ]
    if not args.no_resume and not work_items:
        logger.info("✅ All runs already complete — nothing to do.")

    # Concurrent Docker execution; grade each task immediately when it completes
    def _write_summary(ctx: ModelCtx, elapsed: float) -> None:
        grades_by_task = ctx.grades_by_task
        task_entries = [
            {
                "task_id": r["task_id"],
                "thinking_level": r.get("thinking_level"),
                "status": r["status"],
                "timed_out": r["timed_out"],
                "execution_time": r["execution_time"],
                "transcript_length": len(r["transcript"]),
                "usage": r.get("usage", {}),
                "workspace": r["workspace"],
                "grading": grades_by_task[r["task_id"]],
                "frontmatter": tasks_by_id[r["task_id"]].frontmatter,
            }
            for r in ctx.results
            if r["task_id"] in grades_by_task
        ]
        efficiency = _compute_efficiency(
            task_entries,
            {task_id: {"mean": g["mean"]} for task_id, g in grades_by_task.items()},
        )
        all_means = [g["mean"] for g in grades_by_task.values()]
        mean_score = statistics.mean(all_means) if all_means else 0.0
        pk = pass_k_stats(grades_by_task, runs_per_task)

        aggregate = {
            "model": ctx.model_id,
            "benchmark_version": _get_git_version(code_dir),
            "timestamp": time.time(),
            "suite": args.suite,
            "runs_per_task": runs_per_task,
            "thinking_level": ctx.thinking_level,
            "concurrency": concurrency,
            "batch_wall_clock_seconds": round(elapsed, 2),
            "tasks_total": len(tasks_to_run),
            "tasks_completed": len(grades_by_task),
            "scoring": "simple" if args.simple_scoring else "penalized",
            "mean_score": round(mean_score, 4),
            **pk,
            "tasks": task_entries,
            "efficiency": efficiency,
        }
        _write_json(ctx.output_path, aggregate)

    attempts_by_run: Dict[tuple, int] = {}
    settled_by_task: Dict[tuple, int] = {}

    def _run_one(item):
        slug, task, run_idx = item
        ctx = ctxs[slug]
        result = execute_task_in_docker(
            task=task,
            model_id=ctx.model_id,
            run_id=str(run_idx + 1),
            skill_dir=code_dir,
            timeout_multiplier=args.timeout_multiplier,
            image=args.docker_image,
            verbose=args.verbose,
            asset_dirs=[assets_dir],
            thinking_level=ctx.thinking_level,
        )
        result["_model_slug"] = slug
        return result

    batch_start = time.time()
    total_runs = len(model_ids) * len(tasks_to_run) * runs_per_task
    skipped_runs = total_runs - len(work_items)

    class _Progress:
        """Minimal stdlib progress reporter — replaces tqdm.

        Single-line carriage-return update; final newline on close. We don't
        try to draw a bar, just a tick + counters + postfix.
        """
        def __init__(self, total: int, initial: int = 0, desc: str = "") -> None:
            self.total = total
            self.done = initial
            self.desc = desc
            self.postfix = ""

        def update(self, n: int = 1) -> None:
            self.done += n
            self._render()

        def set_postfix(self, d: Dict[str, Any]) -> None:
            self.postfix = " ".join(f"{k}={v}" for k, v in d.items())
            self._render()

        def _render(self) -> None:
            line = f"\r{self.desc} {self.done}/{self.total}"
            if self.postfix:
                line += f"  {self.postfix}"
            sys.stdout.write(line + " ")
            sys.stdout.flush()

        def close(self) -> None:
            sys.stdout.write("\n")
            sys.stdout.flush()

    pbar = _Progress(total=total_runs, initial=skipped_runs, desc="evaluating")

    def _process_grade(slug: str, task, run_idx: int, result: dict, grade: GradeResult) -> None:
        """Handle post-grade processing: anomalies, retry-or-settle, file writes, progress.

        Outcomes per call:
          - has_error + attempts < MAX_RUN_ATTEMPTS → resubmit a fresh attempt
            (no pbar, no aggregation; original _run_N/ will be overwritten).
          - has_error + attempts exhausted → DROP this run from the task's
            denominator; still write audit files with run_dropped=true and
            increment the task's settled counter.
          - otherwise (kept) → normal path: append to execution_results,
            increment settled counter.
        Aggregation fires once settled count == runs_per_task.
        """
        ctx = ctxs[slug]
        thinking_level = ctx.thinking_level
        anomalies = detect_anomalies(
            {**result, "transcript_length": len(result["transcript"])},
            grade.notes,
        )
        result["_anomalies"] = anomalies

        for anom_item in anomalies["items"]:
            msg = "   [anomaly] %s/%s [%s] run %d — %s: %s"
            anom_args = (
                ctx.model_id,
                task.task_id,
                thinking_level or "default",
                run_idx + 1,
                anom_item["id"],
                anom_item["description"],
            )
            if anom_item["severity"] == "error":
                logger.error(msg, *anom_args)
            else:
                logger.warning(msg, *anom_args)

        run_key = (slug, task.task_id, run_idx)
        task_key = (slug, task.task_id)
        attempts = attempts_by_run.get(run_key, 1)

        anom_ids = {a["id"] for a in anomalies["items"]}
        # The 40-minute wall-clock cap is a hard task budget: hitting it means
        # the agent had its chance and didn't finish. Treat as a real failure
        # (score=0, KEPT in the task's denominator). Don't burn 2 more reruns
        # on a task that is too big for this model.
        hit_wallclock = "TASK_TIMED_OUT" in anom_ids
        retryable_error = anomalies["has_error"] and not hit_wallclock

        # Branch 1: non-timeout infra failure with attempts left → resubmit a
        # fresh attempt. Don't write files, don't update pbar, don't aggregate.
        # The retried attempt's _process_grade call will eventually overwrite
        # the same _run_N/ directory.
        if retryable_error and attempts < MAX_RUN_ATTEMPTS:
            next_attempt = attempts + 1
            attempts_by_run[run_key] = next_attempt
            logger.warning(
                "🔁 %s/%s run %d/%d — infra failure (attempt %d/%d); rerunning",
                ctx.model_id, task.task_id, run_idx + 1, runs_per_task,
                attempts, MAX_RUN_ATTEMPTS,
            )
            f = exec_pool.submit(_run_one, (slug, task, run_idx))
            exec_futures[f] = (slug, task, run_idx)
            pending.add(f)
            return

        # A wall-clock timeout is KEPT as a real 0; only exhausted-retry infra
        # failures get dropped from the denominator.
        run_dropped = retryable_error  # only true if has_error AND not timeout AND attempts exhausted

        pct = grade.score / grade.max_score * 100 if grade.max_score > 0 else 0
        if run_dropped:
            emoji = "🗑️"
            anom_tag = " [DROPPED:retries_exhausted]"
        elif hit_wallclock:
            emoji = "⏰"
            anom_tag = " [WALLCLOCK_TIMEOUT:kept_as_fail]"
        else:
            emoji = "⚠️" if anomalies["is_anomalous"] else "✅"
            anom_tag = " [ANOMALY]" if anomalies["is_anomalous"] else ""
        logger.info(
            "🐳 %s %s/%s (run %d/%d, attempts %d/%d)%s — %s, %.1fs → %.2f/%.2f (%.0f%%) [%s]%s",
            emoji, ctx.model_id, task.task_id, run_idx + 1, runs_per_task,
            attempts, MAX_RUN_ATTEMPTS,
            f" [{thinking_level}]" if args.thinking else "",
            result["status"], result["execution_time"],
            grade.score, grade.max_score, pct, grade.grading_type, anom_tag,
        )

        task_dir = ctx.batch_dir / _subfolder_name(task.task_id, run_idx, runs_per_task)
        task_dir.mkdir(parents=True, exist_ok=True)
        # Two views of the same conversation:
        #   openclaw_trace.json — raw openclaw event stream; preserves
        #     customType / stopReason / toolCall metadata that lib_anomalies
        #     rules rely on. DO NOT change to the OpenAI view.
        #   openai_messages.json — flattened {role, content} chat-completions
        #     view; the one humans / external trace tools read.
        _write_json(task_dir / "openclaw_trace.json", result["transcript"])
        _write_json(
            task_dir / "openai_messages.json",
            _openclaw_transcript_to_messages(result["transcript"]),
        )
        grading_data = {
            **grade.to_dict(),
            "thinking_level": thinking_level,
            "anomalies": anomalies,
            "attempts": attempts,
            "max_attempts": MAX_RUN_ATTEMPTS,
            "run_dropped": run_dropped,
            "execution": {
                "status": result["status"],
                "execution_time": result["execution_time"],
                "exit_code": result.get("exit_code"),
                "timed_out": result.get("timed_out", False),
                "prompt_error_retries": result.get("prompt_error_retries", 0),
                "gateway_prompt_error": result.get("gateway_prompt_error", False),
                "transcript_length": len(result["transcript"]),
            },
        }
        _write_json(task_dir / "grading.json", grading_data)
        # Persist the rendered judge inputs (system prompt, user prompt,
        # image/pdf manifest, per-rubric results) for diff analysis.
        if grade.extra:
            _write_json(task_dir / "judge_prompt.json", grade.extra)
        ws_raw = (result.get("workspace") or "").strip()
        if ws_raw:
            ws_src = Path(ws_raw).resolve()
            ws_dst = (task_dir / "workspace").resolve()
            if not ws_src.is_dir():
                logger.warning("Skipping workspace copy for %s: not a directory: %s", task.task_id, ws_src)
            elif not ws_src.is_relative_to(_WORKSPACE_SNAPSHOT_ROOT):
                logger.warning(
                    "Skipping workspace copy for %s: outside snapshot root %s: %s",
                    task.task_id, _WORKSPACE_SNAPSHOT_ROOT, ws_src,
                )
            elif ws_dst == ws_src or ws_dst.is_relative_to(ws_src):
                logger.warning(
                    "Skipping workspace copy for %s: destination inside source tree (%s in %s)",
                    task.task_id, ws_dst, ws_src,
                )
            else:
                if ws_dst.exists():
                    shutil.rmtree(ws_dst)
                shutil.copytree(ws_src, ws_dst, symlinks=True)

        # Only kept (non-dropped) runs feed task-level aggregation. Dropped runs
        # leave only an audit trail under _run_N/.
        if not run_dropped:
            ctx.execution_results[task.task_id].append((run_idx, result, grade))
            ctx.results.append(result)

        settled_by_task[task_key] = settled_by_task.get(task_key, 0) + 1

        if settled_by_task[task_key] == runs_per_task:
            task_runs_kept = sorted(ctx.execution_results.get(task.task_id, []), key=lambda x: x[0])
            kept_grades = [g for _, _, g in task_runs_kept]
            if kept_grades:
                scores = [
                    g.score_simple if g.score_simple is not None else g.score
                    for g in kept_grades
                ] if args.simple_scoring else [g.score for g in kept_grades]
                mean_score = statistics.mean(scores)
                std_score = statistics.stdev(scores) if len(scores) > 1 else 0.0
                min_score = min(scores)
                max_score = max(scores)
            else:
                # All runs dropped → task floor is 0 per spec.
                scores = []
                mean_score = 0.0
                std_score = 0.0
                min_score = 0.0
                max_score = 0.0
                logger.error(
                    "💀 %s/%s — all %d runs exhausted retries; task floor mean=0",
                    ctx.model_id, task.task_id, runs_per_task,
                )
            ctx.grades_by_task[task.task_id] = {
                "task_id": task.task_id,
                "thinking_level": thinking_level,
                "runs": [g.to_dict() for g in kept_grades],
                "runs_kept": len(kept_grades),
                "runs_dropped": runs_per_task - len(kept_grades),
                "mean": mean_score,
                "std": std_score,
                "min": min_score,
                "max": max_score,
            }
            _write_summary(ctx, elapsed=time.time() - batch_start)

            curr_means = [g["mean"] for g in ctx.grades_by_task.values()]
            curr_avg = statistics.mean(curr_means)
            logger.info(
                "   📈 [%s] avg: %.4f | progress %d/%d",
                ctx.model_id, curr_avg, len(ctx.grades_by_task), len(tasks_to_run),
            )
            pbar.set_postfix({
                "mean": f"{curr_avg:.3f}",
                "done": f"{len(ctx.grades_by_task)}/{len(tasks_to_run)}",
            })

        pbar.update(1)

    # exec_futures: future → (slug, task, run_idx)
    # grade_futures: future → (slug, task, run_idx, result)
    exec_futures: Dict[Future, tuple] = {}
    grade_futures: Dict[Future, tuple] = {}

    with ThreadPoolExecutor(max_workers=concurrency) as exec_pool, \
     ThreadPoolExecutor(max_workers=concurrency) as grade_pool:

        for item in work_items:
            f = exec_pool.submit(_run_one, item)
            exec_futures[f] = item

        pending: set = set(exec_futures)

        while pending:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)

            for f in done:
                if f in exec_futures:
                    slug, task, run_idx = exec_futures.pop(f)
                    ctx = ctxs[slug]
                    try:
                        result = f.result()
                    except Exception as exc:
                        logger.warning(
                            "Execution failed for %s/%s run %d: %s",
                            ctx.model_id, task.task_id, run_idx + 1, exc,
                        )
                        result = {
                            "agent_id": f"bench-{slug}",
                            "task_id": task.task_id,
                            "thinking_level": ctx.thinking_level,
                            "status": "error",
                            "transcript": [],
                            "usage": {},
                            "workspace": "",
                            "exit_code": -1,
                            "timed_out": False,
                            "execution_time": 0.0,
                            "stdout": "",
                            "stderr": str(exc),
                            "_model_slug": slug,
                        }
                    result["thinking_level"] = ctx.thinking_level

                    if args.no_grade:
                        _process_grade(slug, task, run_idx, result, GradeResult(
                            task_id=task.task_id,
                            score=0.0,
                            max_score=1.0,
                            grading_type=task.grading_type,
                            breakdown={},
                            notes="Grading skipped (--no-grade)",
                        ))
                    else:
                        gf = grade_pool.submit(
                            grade_task,
                            task=task,
                            execution_result=result,
                            skill_dir=code_dir,
                            verbose=args.verbose,
                        )
                        grade_futures[gf] = (slug, task, run_idx, result)
                        pending.add(gf)

                else:  # grade future
                    slug, task, run_idx, result = grade_futures.pop(f)
                    try:
                        grade = f.result()
                    except Exception as exc:
                        logger.warning(
                            "Grading failed for %s/%s: %s",
                            ctxs[slug].model_id, task.task_id, exc,
                        )
                        grade = GradeResult(
                            task_id=task.task_id,
                            score=0.0,
                            max_score=1.0,
                            grading_type=task.grading_type,
                            breakdown={},
                            notes=f"Grading failed: {exc}",
                        )
                    _process_grade(slug, task, run_idx, result, grade)

    pbar.close()
    batch_exec_time = time.time() - batch_start
    logger.info("⏱️  All executions finished in %.1fs (wall clock)", batch_exec_time)

    scoring_label = "simple avg" if args.simple_scoring else "penalized (auto≤0.75→llm=0)"

    # Finalize each model independently: write its summary + anomaly report and
    # emit a per-model SUMMARY block.
    for slug, ctx in ctxs.items():
        _write_summary(ctx, elapsed=batch_exec_time)
        logger.info("📄 Results saved to %s", ctx.batch_dir)
        _write_anomaly_report(
            ctx.batch_dir, ctx.execution_results, ctx.model_id, ctx.thinking_level
        )

        all_means = [g["mean"] for g in ctx.grades_by_task.values()]
        mean_score = statistics.mean(all_means) if all_means else 0.0
        pk = pass_k_stats(ctx.grades_by_task, runs_per_task)
        k = runs_per_task
        pass_at_k = pk.get(f"pass@{k}", 0.0)
        pass_pow_k = pk.get(f"pass^{k}", 0.0)

        logger.info("\n%s", "=" * 70)
        logger.info("📊 SUMMARY — %s", ctx.model_id)
        logger.info(
            "   Tasks: %d | Runs/task: %d | Concurrency: %d (shared across %d model(s))",
            len(tasks_to_run),
            runs_per_task,
            concurrency,
            len(model_ids),
        )
        if args.thinking:
            logger.info("   Thinking level: %s", ctx.thinking_level)
        logger.info("   Avg@%d:  %.4f   [%s]", k, mean_score, scoring_label)
        logger.info("   Pass@%d: %.4f", k, pass_at_k)
        logger.info("   Pass^%d: %.4f", k, pass_pow_k)
        logger.info("   Wall clock: %.1fs", batch_exec_time)
        logger.info("%s", "=" * 70)


if __name__ == "__main__":
    main()
