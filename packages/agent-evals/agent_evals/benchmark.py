"""
A/B Performance Benchmarking Orchestrator.
Executes the predefined benchmark intents across both Raw Filesystem Traversal
and Hybrid Context Router, recording granular per-query metrics and aggregate statistics.
"""

from typing import List, Dict, Any, Optional

from .datasets import BENCHMARK_INTENTS, BenchmarkItem
from .raw_traversal import simulate_raw_traversal
from .router_traversal import evaluate_router_traversal
from .metrics import calculate_eval_metrics, EvalSummary


class BenchmarkRunResult:
    """Encapsulates the complete result of a benchmark run."""

    def __init__(
        self,
        records: List[Dict[str, Any]],
        summary: EvalSummary,
    ):
        self.records = records
        self.summary = summary

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "records": self.records,
        }


def run_ab_benchmark(
    repo_root: str,
    items: Optional[List[BenchmarkItem]] = None,
    top_k: int = 3,
    accuracy_threshold: float = 0.90,
) -> BenchmarkRunResult:
    """
    Execute full A/B benchmark comparing Raw Traversal vs Hybrid Context Router.
    """
    benchmark_items = items or BENCHMARK_INTENTS
    records: List[Dict[str, Any]] = []

    for item in benchmark_items:
        raw_res = simulate_raw_traversal(item.intent, repo_root=repo_root, top_k=top_k)
        router_res = evaluate_router_traversal(item.intent, repo_root=repo_root, top_k=top_k)

        is_top1_hit = (
            router_res["primary_domain"] == item.expected_domain
            or router_res["primary_domain"] in item.acceptable_domains
        )
        is_top_k_hit = (
            item.expected_domain in router_res["matched_domains"]
            or any(acc in router_res["matched_domains"] for acc in item.acceptable_domains)
        )

        tok_reduction = (
            ((raw_res["context_tokens"] - router_res["context_tokens"]) / raw_res["context_tokens"] * 100.0)
            if raw_res["context_tokens"] > 0
            else 0.0
        )

        records.append(
            {
                "item_id": item.item_id,
                "intent": item.intent,
                "category": item.category,
                "expected_domain": item.expected_domain,
                "acceptable_domains": item.acceptable_domains,
                "raw": raw_res,
                "router": router_res,
                "is_top1_hit": is_top1_hit,
                "is_top_k_hit": is_top_k_hit,
                "token_reduction_pct": round(tok_reduction, 2),
                "speedup_factor": round(
                    (raw_res["duration_ms"] / router_res["duration_ms"])
                    if router_res["duration_ms"] > 0
                    else 1.0,
                    1,
                ),
            }
        )

    summary = calculate_eval_metrics(records, accuracy_threshold=accuracy_threshold)
    return BenchmarkRunResult(records=records, summary=summary)
