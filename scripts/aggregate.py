#!/usr/bin/env python3
"""Aggregate FORTE results across models and tasks.

Scans `<results-dir>/<model_slug>/<task_id>[_run_N]/grading.json`, recomputes
the three leaderboard metrics directly from the per-run grading files, and
prints a model x metrics table to the terminal.

The three reported metrics match the website leaderboard:

  Avg@k   — macro average over tasks of (mean per-run score over k runs).
            Tells you the expected score of a random run.
  Pass@k  — macro average over tasks of the unbiased pass@k probability
            (Chen et al., HumanEval). Probability that at least one of k
            sampled runs is fully correct.
  Pass^k  — macro average over tasks of the probability that ALL k sampled
            runs are fully correct. Measures consistency.

For a task with n runs and c perfect runs (score == 1.0):
  pass@k = 1 - C(n-c, k) / C(n, k)         (0 if n < k)
  pass^k = C(c, k) / C(n, k)               (0 if n < k)

Dropped runs (those resubmitted by benchmark.py's run-level retry whose
final attempt still couldn't be settled) are excluded from n and c.

Usage:
  python scripts/aggregate.py
  python scripts/aggregate.py --results-dir ./results --k 3
  python scripts/aggregate.py --model your-gateway-claude-sonnet-4-6
  python scripts/aggregate.py --tasks Finance-018,Legal-020
  python scripts/aggregate.py --per-task        # one row per (model, task)
  python scripts/aggregate.py --json            # machine-readable output
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from math import comb
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


RUN_DIR_PATTERN = re.compile(r"^(?P<task>.+?)(?:_run_(?P<run>\d+))?$")


def _load_grading(grading_path: Path) -> Optional[Dict[str, Any]]:
    try:
        with grading_path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return None


def _collect_model_runs(model_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Return {task_id: [grading_dict, ...]} for one model's results directory.

    Dropped runs (grading_dict["run_dropped"] truthy) are skipped — they
    represent attempts that benchmark.py's outer retry couldn't settle and
    are not counted toward the task denominator.
    """
    out: Dict[str, List[Dict[str, Any]]] = {}
    if not model_dir.is_dir():
        return out
    for entry in sorted(model_dir.iterdir()):
        if not entry.is_dir():
            continue
        m = RUN_DIR_PATTERN.match(entry.name)
        if not m:
            continue
        task_id = m.group("task")
        grading = _load_grading(entry / "grading.json")
        if grading is None:
            continue
        if grading.get("run_dropped"):
            continue
        out.setdefault(task_id, []).append(grading)
    return out


def _score(run: Dict[str, Any]) -> float:
    """Per-run score in [0, 1]. Treats missing/non-numeric as 0."""
    try:
        return float(run.get("score", 0.0))
    except (TypeError, ValueError):
        return 0.0


def _is_perfect(run: Dict[str, Any]) -> bool:
    return _score(run) >= 1.0 - 1e-9


def _pass_at_k(n: int, c: int, k: int) -> float:
    if n < k:
        return 0.0
    if c >= n:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)


def _pass_pow_k(n: int, c: int, k: int) -> float:
    if n < k:
        return 0.0
    return comb(c, k) / comb(n, k)


def _per_task_stats(runs: List[Dict[str, Any]], k: int) -> Dict[str, float]:
    n = len(runs)
    if n == 0:
        return {"n": 0, "c": 0, "avg": 0.0, "pass_at_k": 0.0, "pass_pow_k": 0.0}
    c = sum(1 for r in runs if _is_perfect(r))
    scores = [_score(r) for r in runs]
    return {
        "n": n,
        "c": c,
        "avg": sum(scores) / n,
        "pass_at_k": _pass_at_k(n, c, k),
        "pass_pow_k": _pass_pow_k(n, c, k),
    }


def _aggregate_model(
    model_runs: Dict[str, List[Dict[str, Any]]],
    task_filter: Optional[List[str]],
    k: int,
) -> Dict[str, Any]:
    task_ids = sorted(model_runs.keys())
    if task_filter:
        wanted = set(task_filter)
        task_ids = [t for t in task_ids if t in wanted]

    per_task: Dict[str, Dict[str, float]] = {}
    for tid in task_ids:
        per_task[tid] = _per_task_stats(model_runs[tid], k)

    if per_task:
        avg = sum(s["avg"] for s in per_task.values()) / len(per_task)
        pak = sum(s["pass_at_k"] for s in per_task.values()) / len(per_task)
        ppk = sum(s["pass_pow_k"] for s in per_task.values()) / len(per_task)
    else:
        avg = pak = ppk = 0.0

    return {
        "tasks": per_task,
        "task_count": len(per_task),
        "avg_at_k": avg,
        "pass_at_k": pak,
        "pass_pow_k": ppk,
    }


def _model_dirs(results_dir: Path, model_filter: Optional[List[str]]) -> List[Path]:
    if not results_dir.is_dir():
        return []
    dirs = sorted(p for p in results_dir.iterdir() if p.is_dir())
    if model_filter:
        wanted = set(model_filter)
        dirs = [d for d in dirs if d.name in wanted]
    return dirs


def _fmt_pct(x: float) -> str:
    return f"{x * 100:6.2f}"


def _print_summary_table(
    rows: List[Tuple[str, Dict[str, Any]]],
    k: int,
    runs_dir_label: str,
) -> None:
    if not rows:
        print(f"No model results found under {runs_dir_label}.")
        return
    model_w = max(len("Model"), max(len(name) for name, _ in rows))
    header = (
        f"{'Model'.ljust(model_w)}  "
        f"{'Tasks':>5}  "
        f"{'Avg@' + str(k):>7}  "
        f"{'Pass@' + str(k):>8}  "
        f"{'Pass^' + str(k):>8}"
    )
    sep = "-" * len(header)
    print(sep)
    print(header)
    print(sep)
    # Sort by Avg@k descending (matches website ordering).
    rows_sorted = sorted(rows, key=lambda r: r[1]["avg_at_k"], reverse=True)
    for name, agg in rows_sorted:
        print(
            f"{name.ljust(model_w)}  "
            f"{agg['task_count']:>5}  "
            f"{_fmt_pct(agg['avg_at_k']):>7}  "
            f"{_fmt_pct(agg['pass_at_k']):>8}  "
            f"{_fmt_pct(agg['pass_pow_k']):>8}"
        )
    print(sep)
    print("Numbers are percentages (0-100). Higher is better.")
    print(
        f"Avg@{k}   = mean per-run score, averaged across tasks "
        f"(expected score of a random run)."
    )
    print(
        f"Pass@{k}  = prob. at least 1 of {k} runs is fully correct, "
        f"averaged across tasks."
    )
    print(
        f"Pass^{k}  = prob. ALL {k} runs are fully correct, "
        f"averaged across tasks (consistency)."
    )


def _print_per_task_table(
    rows: List[Tuple[str, Dict[str, Any]]],
    k: int,
) -> None:
    if not rows:
        return
    all_tasks: List[str] = []
    seen = set()
    for _, agg in rows:
        for tid in agg["tasks"].keys():
            if tid not in seen:
                seen.add(tid)
                all_tasks.append(tid)
    all_tasks.sort()
    if not all_tasks:
        return
    task_w = max(len("Task"), max(len(t) for t in all_tasks))
    model_w = max(len("Model"), max(len(name) for name, _ in rows))
    header = (
        f"{'Model'.ljust(model_w)}  "
        f"{'Task'.ljust(task_w)}  "
        f"{'n':>2}  "
        f"{'pass':>4}  "
        f"{'Avg@' + str(k):>7}  "
        f"{'Pass@' + str(k):>8}  "
        f"{'Pass^' + str(k):>8}"
    )
    sep = "-" * len(header)
    print("\nPer-task breakdown:")
    print(sep)
    print(header)
    print(sep)
    for name, agg in sorted(rows, key=lambda r: r[0]):
        for tid in all_tasks:
            s = agg["tasks"].get(tid)
            if s is None:
                print(
                    f"{name.ljust(model_w)}  "
                    f"{tid.ljust(task_w)}  "
                    f"{'-':>2}  {'-':>4}  {'-':>7}  {'-':>8}  {'-':>8}"
                )
                continue
            print(
                f"{name.ljust(model_w)}  "
                f"{tid.ljust(task_w)}  "
                f"{int(s['n']):>2}  "
                f"{int(s['c']):>4}  "
                f"{_fmt_pct(s['avg']):>7}  "
                f"{_fmt_pct(s['pass_at_k']):>8}  "
                f"{_fmt_pct(s['pass_pow_k']):>8}"
            )
    print(sep)


def _emit_json(rows: List[Tuple[str, Dict[str, Any]]], k: int) -> None:
    out = {
        "k": k,
        "models": [
            {
                "model": name,
                "task_count": agg["task_count"],
                f"avg_at_{k}": round(agg["avg_at_k"], 4),
                f"pass_at_{k}": round(agg["pass_at_k"], 4),
                f"pass_pow_{k}": round(agg["pass_pow_k"], 4),
                "tasks": {
                    tid: {
                        "n": int(s["n"]),
                        "c": int(s["c"]),
                        f"avg_at_{k}": round(s["avg"], 4),
                        f"pass_at_{k}": round(s["pass_at_k"], 4),
                        f"pass_pow_{k}": round(s["pass_pow_k"], 4),
                    }
                    for tid, s in agg["tasks"].items()
                },
            }
            for name, agg in sorted(rows, key=lambda r: r[1]["avg_at_k"], reverse=True)
        ],
    }
    print(json.dumps(out, indent=2, ensure_ascii=False))


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Aggregate FORTE results: Avg@k / Pass@k / Pass^k "
            "per model, recomputed from per-run grading.json files."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument(
        "--results-dir", default="./results",
        help="Directory containing <model_slug>/<task_id>[_run_N]/ subdirs (default: ./results).",
    )
    p.add_argument(
        "--model", action="append", default=None,
        help="Model slug to include (matches directory name under results-dir). Repeatable.",
    )
    p.add_argument(
        "--tasks", default=None,
        help="Comma-separated task ids to restrict to.",
    )
    p.add_argument(
        "--k", type=int, default=3,
        help="k for Avg@k / Pass@k / Pass^k (default: 3, matching the leaderboard).",
    )
    p.add_argument(
        "--per-task", action="store_true",
        help="Also print a per-(model, task) breakdown after the summary table.",
    )
    p.add_argument(
        "--json", action="store_true",
        help="Emit machine-readable JSON instead of a terminal table.",
    )
    return p.parse_args()


def main() -> int:
    args = _parse_args()
    results_dir = Path(args.results_dir).resolve()

    task_filter: Optional[List[str]] = None
    if args.tasks:
        task_filter = [t.strip() for t in args.tasks.split(",") if t.strip()]

    model_paths = _model_dirs(results_dir, args.model)
    if not model_paths:
        print(f"No model directories found under {results_dir}.", file=sys.stderr)
        if args.model:
            print(
                f"Looked for: {', '.join(args.model)}. "
                f"Existing: {', '.join(p.name for p in sorted(results_dir.iterdir()) if p.is_dir()) if results_dir.is_dir() else '(none)'}",
                file=sys.stderr,
            )
        return 1

    rows: List[Tuple[str, Dict[str, Any]]] = []
    for mp in model_paths:
        runs = _collect_model_runs(mp)
        agg = _aggregate_model(runs, task_filter, args.k)
        rows.append((mp.name, agg))

    if args.json:
        _emit_json(rows, args.k)
        return 0

    _print_summary_table(rows, args.k, runs_dir_label=str(results_dir))
    if args.per_task:
        _print_per_task_table(rows, args.k)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
