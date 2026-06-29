"""
AI Search Agent - Main Entry Point
Workflow-based Search Agent System

Usage:
    python main.py

Architecture:
    This system uses a fixed workflow pipeline. Every query passes through
    the same sequence of nodes in order:
    QueryAnalysis -> SearchPlan -> SearchExecution -> ResultRanking -> SummaryGeneration

Business Logic Highlights:
    - Query rewrite with semantic drift detection (fallback to original if drift detected)
    - News queries use time-restricted web search (date_restrict_days)
    - Search results quality filtering with graceful degradation fallback
    - Multi-source quota balancing to prevent single-source dominance
    - Summary truncation at sentence boundaries (not mid-word)
"""

import logging
import sys

from config import WorkflowConfig
from workflow import SearchWorkflow


def setup_logging(config: WorkflowConfig):
    """Configure logging based on config settings"""
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.log_file, encoding="utf-8"),
        ],
    )


def print_results(state):
    """Print the search results in a formatted way"""
    print("\n" + "=" * 70)
    print("AI Search Agent - Workflow Architecture")
    print("=" * 70)

    print(f"\n[Query] {state.original_query}")
    print(f"[Intent] {state.intent}")
    print(f"[Rewritten Query] {state.rewritten_query}")
    print(f"[Rewrite Accepted] {state.rewrite_accepted}")
    print(f"[Tools Used] {', '.join(state.selected_tools)}")
    print(f"[Raw Results] {len(state.raw_results)}  "
          f"[After Quality Filter] {len(state.filtered_results)}  "
          f"[After Ranking] {len(state.ranked_results)}")

    print(f"\n{'─' * 70}")
    print("[Answer]" + (" [TRUNCATED]" if state.answer_truncated else ""))
    print(state.final_answer)

    if state.citations:
        print(f"\n{'─' * 70}")
        print("[Citations]")
        for cite in state.citations:
            print(f"  [{cite['index']}] {cite['title']} ({cite['source']})")
            print(f"      URL: {cite['url']}")

    print(f"\n{'─' * 70}")
    print("[Execution Log]")
    for log_entry in state.execution_log:
        status_icon = "OK" if log_entry["status"] == "success" else "FAIL"
        print(f"  [{status_icon}] {log_entry['node']} - {log_entry.get('elapsed_time', 0):.3f}s")

    print(f"\n[Total Time] {state.total_time:.3f}s")
    print("=" * 70)


def main():
    """Main function - run the search workflow"""
    config = WorkflowConfig()

    setup_logging(config)

    logger = logging.getLogger(__name__)
    logger.info("Starting AI Search Agent (Workflow Architecture)")

    workflow = SearchWorkflow(config)

    test_queries = [
        "What is the difference between React and Vue.js?",
        "Latest advances in large language models 2024",
        "How to implement a binary search tree in Python?",
        "Breaking news about AI regulation today",   # 新闻类，触发时间限制逻辑
    ]

    for query in test_queries:
        state = workflow.run(query)
        print_results(state)
        print("\n")


if __name__ == "__main__":
    main()
