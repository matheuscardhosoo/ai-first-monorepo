"""
Raw Filesystem Traversal Simulator.
Simulates a traditional, naive autonomous agent crawling the repository filesystem,
scanning every directory, reading file contents into memory, and running regex grep
to locate domain instructions.
"""

import os
import re
import time
from typing import Dict, Any, List, Optional

IGNORE_DIRS = {
    ".git",
    "node_modules",
    "target",
    "dist",
    "build",
    ".turbo",
    ".cache",
    ".pytest_cache",
    "__pycache__",
    ".ai/cache",
}


def simulate_raw_traversal(
    intent: str,
    repo_root: str,
    top_k: int = 3,
) -> Dict[str, Any]:
    """
    Simulate naive raw filesystem traversal: recursively scans all files in monorepo,
    accumulating file contents and scoring by raw keyword count.
    """
    start_time = time.time()
    tokens_in_query = [t.lower() for t in re.findall(r"\w+", intent) if len(t) > 2]

    scanned_files_count = 0
    scanned_bytes = 0
    raw_context_accumulated = []
    domain_scores: Dict[str, int] = {}
    domain_files: Dict[str, str] = {}

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [
            d for d in dirs
            if d not in IGNORE_DIRS and not any(root.endswith(os.sep + ign) for ign in IGNORE_DIRS)
        ]

        for fname in files:
            # Traditional agents inspect markdown, specs, package manifests, or read AGENTS.md
            if fname.endswith((".md", ".json", ".ts", ".py", ".go")):
                fpath = os.path.join(root, fname)
                try:
                    stat = os.stat(fpath)
                    scanned_files_count += 1
                    scanned_bytes += stat.st_size

                    # Naive agent reads file into context window
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()

                    raw_context_accumulated.append(content[:1500])

                    # Heuristic keyword match to identify target domain
                    rel_p = os.path.relpath(fpath, repo_root).replace(os.sep, "/")
                    dir_name = os.path.dirname(rel_p)
                    dom = "root" if dir_name in ("", ".") else dir_name

                    content_lower = content.lower()
                    score = sum(content_lower.count(t) for t in tokens_in_query)
                    if score > 0:
                        domain_scores[dom] = domain_scores.get(dom, 0) + score
                        if dom not in domain_files:
                            domain_files[dom] = rel_p

                except Exception:
                    pass

    # Sort domains by hit count
    ranked_domains = sorted(domain_scores.items(), key=lambda x: x[1], reverse=True)
    top_matches = [d for d, _ in ranked_domains[:top_k]]
    primary_domain = top_matches[0] if top_matches else "unknown"

    # Naive agent passes huge raw dump into prompt
    joined_raw_context = "\n---\n".join(raw_context_accumulated[:15])
    total_tokens_est = max(1, len(joined_raw_context) // 4)

    duration_ms = (time.time() - start_time) * 1000.0

    return {
        "engine": "raw_traversal",
        "query": intent,
        "primary_domain": primary_domain,
        "matched_domains": top_matches,
        "scanned_files": scanned_files_count,
        "scanned_bytes": scanned_bytes,
        "context_tokens": total_tokens_est,
        "duration_ms": round(duration_ms, 2),
        "raw_context": joined_raw_context[:2000],
    }
