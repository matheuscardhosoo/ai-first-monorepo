"""
Hybrid Context Router Evaluator Wrapper.
Invokes the optimized hybrid context retrieval pipeline and packages standardized
performance metrics for A/B benchmarking.
"""

import sys
import os
import time
from typing import Dict, Any, Optional

# Ensure context-router package is importable
repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
context_router_path = os.path.join(repo_root, "packages", "context-router")
if context_router_path not in sys.path:
    sys.path.insert(0, context_router_path)

from context_router.api import search_context


def evaluate_router_traversal(
    intent: str,
    repo_root: str,
    top_k: int = 3,
) -> Dict[str, Any]:
    """
    Execute Hybrid Context Router retrieval and measure exact latency and token consumption.
    """
    start_time = time.time()
    res = search_context(
        intent=intent,
        top_k=top_k,
        repo_root=repo_root,
        include_session=True,
    )
    duration_ms = (time.time() - start_time) * 1000.0

    matched_domains = [r["domain"] for r in res.get("results", [])]
    primary_domain = res.get("primary_domain", "root")

    synth_context = res.get("synthesized_context", "")
    context_tokens = max(1, len(synth_context) // 4)

    return {
        "engine": "hybrid_context_router",
        "query": intent,
        "primary_domain": primary_domain,
        "matched_domains": matched_domains,
        "results_count": len(res.get("results", [])),
        "context_tokens": context_tokens,
        "duration_ms": round(duration_ms, 2),
        "confidence_score": res["results"][0]["score"] if res.get("results") else 0.0,
        "has_root_governance": "root_governance" in res,
        "dependencies_count": len(res.get("dependencies", [])),
        "synthesized_context": synth_context,
    }
