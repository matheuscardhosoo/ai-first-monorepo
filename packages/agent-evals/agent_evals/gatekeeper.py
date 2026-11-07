"""
Lightweight Quality Gatekeeper for Pre-commit Hooks and CI Pipelines.
Enforces that localized AGENTS.md relocations or modifications do not break the AI
agent's ability to discover and retrieve the correct domain context.
"""

import sys
import os
import argparse
from typing import Optional

# Ensure sibling packages are importable
current_dir = os.path.dirname(os.path.abspath(__file__))
pkg_root = os.path.dirname(current_dir)
repo_root = os.path.dirname(os.path.dirname(pkg_root))

context_router_path = os.path.join(repo_root, "packages", "context-router")
if context_router_path not in sys.path:
    sys.path.insert(0, context_router_path)

from context_router.api import search_context
from agent_evals.datasets import BENCHMARK_INTENTS


def run_gatekeeper(
    repo_root: str,
    threshold: float = 0.90,
    top_k: int = 3,
) -> int:
    """
    Run lightweight retrieval validation across benchmark intents.
    Returns 0 if pass-rate meets or exceeds threshold, 1 if below.
    """
    total = len(BENCHMARK_INTENTS)
    passed_count = 0
    failures = []

    for item in BENCHMARK_INTENTS:
        res = search_context(intent=item.intent, top_k=top_k, repo_root=repo_root)
        primary = res.get("primary_domain")
        matched = [r["domain"] for r in res.get("results", [])]

        is_hit = (
            primary == item.expected_domain
            or primary in item.acceptable_domains
            or item.expected_domain in matched
        )

        if is_hit:
            passed_count += 1
        else:
            failures.append(
                {
                    "item_id": item.item_id,
                    "intent": item.intent,
                    "expected": item.expected_domain,
                    "primary": primary,
                    "matched": matched,
                }
            )

    accuracy = (passed_count / total) if total > 0 else 0.0

    if accuracy >= threshold:
        print(f"[EVAL GATEKEEPER PASS] Retrieval accuracy: {accuracy * 100:.1f}% ({passed_count}/{total} benchmark queries verified).")
        return 0
    else:
        print("=" * 70, file=sys.stderr)
        print(f"[EVAL GATEKEEPER FAILURE] Retrieval accuracy dropped below threshold!", file=sys.stderr)
        print(f"Required threshold: {threshold * 100:.1f}% | Actual accuracy: {accuracy * 100:.1f}%", file=sys.stderr)
        print("=" * 70, file=sys.stderr)
        for f in failures:
            print(f"- Query: '{f['intent']}'", file=sys.stderr)
            print(f"    Expected: `{f['expected']}` | Resolved: `{f['primary']}` (candidates: {f['matched']})", file=sys.stderr)
        print("\nAction Required: Check if an AGENTS.md was moved, renamed, or corrupted.", file=sys.stderr)
        print("Commit rejected by AI-First SDLC Policy (Claude AI-Native SDLC Playbook).", file=sys.stderr)
        return 1


def main(args: Optional[list] = None):
    parser = argparse.ArgumentParser(description="AI Agent Retrieval Quality Gatekeeper")
    parser.add_argument("--threshold", type=float, default=0.90, help="Minimum acceptable accuracy rate (default: 0.90)")
    parser.add_argument("--strict", action="store_true", help="Enforce 100% first-pass accuracy threshold")
    parser.add_argument("--root", type=str, default=None, help="Monorepo root path")

    parsed = parser.parse_args(args)
    threshold = 1.0 if parsed.strict else parsed.threshold
    target_root = parsed.root or repo_root

    exit_code = run_gatekeeper(repo_root=target_root, threshold=threshold)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
