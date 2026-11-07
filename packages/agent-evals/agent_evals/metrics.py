"""
Evaluation Metrics Engine for AI Agent Context Retrieval.
Implements Token Reduction Rate, First-Pass Retrieval Accuracy, Latency Comparisons,
and Google Cloud AI-in-SDLC Developer Productivity & Prompt Performance Metrics.
"""

from typing import List, Dict, Any


class EvalSummary:
    """Aggregated evaluation summary containing concrete performance indicators."""

    def __init__(
        self,
        total_queries: int,
        top1_accuracy_pct: float,
        top_k_accuracy_pct: float,
        avg_raw_tokens: float,
        avg_router_tokens: float,
        token_reduction_rate_pct: float,
        avg_raw_latency_ms: float,
        avg_router_latency_ms: float,
        latency_speedup_factor: float,
        dollars_saved_per_1k_queries: float,
        hours_saved_per_sprint: float,
        passed_threshold: bool,
    ):
        self.total_queries = total_queries
        self.top1_accuracy_pct = top1_accuracy_pct
        self.top_k_accuracy_pct = top_k_accuracy_pct
        self.avg_raw_tokens = avg_raw_tokens
        self.avg_router_tokens = avg_router_tokens
        self.token_reduction_rate_pct = token_reduction_rate_pct
        self.avg_raw_latency_ms = avg_raw_latency_ms
        self.avg_router_latency_ms = avg_router_latency_ms
        self.latency_speedup_factor = latency_speedup_factor
        self.dollars_saved_per_1k_queries = dollars_saved_per_1k_queries
        self.hours_saved_per_sprint = hours_saved_per_sprint
        self.passed_threshold = passed_threshold

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_queries": self.total_queries,
            "top1_accuracy_pct": round(self.top1_accuracy_pct, 2),
            "top_k_accuracy_pct": round(self.top_k_accuracy_pct, 2),
            "avg_raw_tokens": round(self.avg_raw_tokens, 1),
            "avg_router_tokens": round(self.avg_router_tokens, 1),
            "token_reduction_rate_pct": round(self.token_reduction_rate_pct, 2),
            "avg_raw_latency_ms": round(self.avg_raw_latency_ms, 2),
            "avg_router_latency_ms": round(self.avg_router_latency_ms, 2),
            "latency_speedup_factor": round(self.latency_speedup_factor, 1),
            "dollars_saved_per_1k_queries": round(self.dollars_saved_per_1k_queries, 2),
            "hours_saved_per_sprint": round(self.hours_saved_per_sprint, 2),
            "passed_threshold": self.passed_threshold,
        }


def calculate_eval_metrics(
    eval_records: List[Dict[str, Any]],
    accuracy_threshold: float = 0.90,
) -> EvalSummary:
    """
    Calculate comparative metrics across benchmark evaluation records.
    """
    total = len(eval_records)
    if total == 0:
        return EvalSummary(
            total_queries=0,
            top1_accuracy_pct=0.0,
            top_k_accuracy_pct=0.0,
            avg_raw_tokens=0.0,
            avg_router_tokens=0.0,
            token_reduction_rate_pct=0.0,
            avg_raw_latency_ms=0.0,
            avg_router_latency_ms=0.0,
            latency_speedup_factor=0.0,
            dollars_saved_per_1k_queries=0.0,
            hours_saved_per_sprint=0.0,
            passed_threshold=False,
        )

    top1_hits = 0
    top_k_hits = 0
    total_raw_tokens = 0
    total_router_tokens = 0
    total_raw_latency = 0.0
    total_router_latency = 0.0

    for rec in eval_records:
        expected = rec["expected_domain"]
        acceptable = rec["acceptable_domains"]

        router_primary = rec["router"]["primary_domain"]
        router_matched = rec["router"]["matched_domains"]

        # First-pass accuracy check
        if router_primary == expected or router_primary in acceptable:
            top1_hits += 1

        if expected in router_matched or any(acc in router_matched for acc in acceptable):
            top_k_hits += 1

        # Token metrics
        total_raw_tokens += rec["raw"]["context_tokens"]
        total_router_tokens += rec["router"]["context_tokens"]

        # Latency metrics
        total_raw_latency += rec["raw"]["duration_ms"]
        total_router_latency += rec["router"]["duration_ms"]

    avg_raw_tok = total_raw_tokens / total
    avg_router_tok = total_router_tokens / total
    tok_reduction_pct = (
        ((avg_raw_tok - avg_router_tok) / avg_raw_tok * 100.0) if avg_raw_tok > 0 else 0.0
    )

    avg_raw_lat = total_raw_latency / total
    avg_router_lat = total_router_latency / total
    speedup = (avg_raw_lat / avg_router_lat) if avg_router_lat > 0 else 1.0

    top1_pct = (top1_hits / total) * 100.0
    top_k_pct = (top_k_hits / total) * 100.0

    # Prompt Performance & SDLC Productivity Metrics:
    # 1. Cost savings: Assuming $3.00 per 1M input tokens ($0.003 per 1k tokens)
    tokens_saved_per_query = max(0.0, avg_raw_tok - avg_router_tok)
    dollars_saved_per_1k = (tokens_saved_per_query * 1000 / 1_000_000) * 3.00

    # 2. Engineering time savings:
    # Avoiding recursive multi-turn filesystem search loops saves ~2 minutes of agent flailing / reasoning per task.
    # Assuming an active engineering squad performs ~200 agent tasks/sprint:
    tasks_per_sprint = 200
    minutes_saved_per_task = 2.0
    hours_saved_per_sprint = (tasks_per_sprint * minutes_saved_per_task) / 60.0

    passed = (top1_pct / 100.0) >= accuracy_threshold

    return EvalSummary(
        total_queries=total,
        top1_accuracy_pct=top1_pct,
        top_k_accuracy_pct=top_k_pct,
        avg_raw_tokens=avg_raw_tok,
        avg_router_tokens=avg_router_tok,
        token_reduction_rate_pct=tok_reduction_pct,
        avg_raw_latency_ms=avg_raw_lat,
        avg_router_latency_ms=avg_router_lat,
        latency_speedup_factor=speedup,
        dollars_saved_per_1k_queries=dollars_saved_per_1k,
        hours_saved_per_sprint=hours_saved_per_sprint,
        passed_threshold=passed,
    )
