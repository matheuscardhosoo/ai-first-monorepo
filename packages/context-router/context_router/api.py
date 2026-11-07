"""
Public API Interface for Context Discovery and Retrieval.
Exposes clean callable functions for AI Agents, MCP Tools, and automated workflows.
Supports always-on root governance, cross-domain dependencies, ephemeral SDLC session
tracking, and auto-reindexing synchronization.
"""

import os
from typing import Dict, Any, Optional, List

from .engine import ContextSearchEngine
from .indexer import scan_session_artifacts


def _find_repo_root(start_dir: Optional[str] = None) -> str:
    """Traverse upwards to locate monorepo root marked by AGENTS.md or Makefile."""
    curr = os.path.abspath(start_dir or os.getcwd())
    while True:
        if os.path.exists(os.path.join(curr, "AGENTS.md")) and os.path.exists(os.path.join(curr, "Makefile")):
            return curr
        parent = os.path.dirname(curr)
        if parent == curr:
            return os.path.abspath(start_dir or os.getcwd())
        curr = parent


def search_context(
    intent: str,
    top_k: int = 3,
    domain_filter: Optional[str] = None,
    repo_root: Optional[str] = None,
    include_session: bool = True,
    session_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Search the monorepo context index using hybrid search (semantic + FTS5 BM25).
    Guarantees always-on root governance, cross-domain dependency resolution, and
    ephemeral SDLC session state injection.

    Args:
        intent: Natural language task description (e.g. "Implement auth middleware")
        top_k: Number of most relevant sections to retrieve (default: 3)
        domain_filter: Optional domain prefix to scope search (e.g. "packages/auth")
        repo_root: Optional path to monorepo root (auto-detected if omitted)
        include_session: Whether to track and append active ephemeral session artifacts (plan.md, etc.)
        session_dir: Optional directory containing active session artifacts (defaults to repo root / cwd)

    Returns:
        Dictionary containing matched chunks, primary recommended domain, root governance,
        cross-domain dependencies, active session artifacts, and synthesized markdown prompt context.
    """
    root = repo_root or _find_repo_root()
    engine = ContextSearchEngine(repo_root=root)

    if not engine.is_indexed():
        engine.build_index()

    return engine.search(
        query=intent,
        top_k=top_k,
        domain_filter=domain_filter,
        include_session=include_session,
        session_dir=session_dir,
    )


def sync_index(repo_root: Optional[str] = None, force: bool = False) -> Dict[str, Any]:
    """
    Auto-reindexing: Check file modification timestamps and granularly update
    only modified, added, or deleted AGENTS.md files in SQLite and INDEX.json/MAP.md.
    """
    root = repo_root or _find_repo_root()
    engine = ContextSearchEngine(repo_root=root)
    return engine.sync_index(force=force)


def get_active_session_artifacts(
    work_dir: Optional[str] = None,
    repo_root: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Retrieve active ephemeral SDLC session artifacts (intent.md, spec.md, plan.md,
    and active in_progress plans from docs/plans/).
    """
    root = repo_root or _find_repo_root()
    return scan_session_artifacts(work_dir=work_dir, repo_root=root)


def get_topological_map(repo_root: Optional[str] = None) -> str:
    """
    Retrieve the monorepo topological map (MAP.md) describing domain hierarchy and responsibilities.
    """
    root = repo_root or _find_repo_root()
    map_path = os.path.join(root, "MAP.md")
    if os.path.exists(map_path):
        with open(map_path, "r", encoding="utf-8") as f:
            return f.read()

    engine = ContextSearchEngine(repo_root=root)
    engine.build_index()

    if os.path.exists(map_path):
        with open(map_path, "r", encoding="utf-8") as f:
            return f.read()
    return "MAP.md not found. Run index_context first."


def get_domain_context(domain: str, repo_root: Optional[str] = None) -> str:
    """
    Directly retrieve the complete localized AGENTS.md for a specific domain.

    Args:
        domain: Domain path, e.g. "packages/auth", "apps/api-gateway", or "root"
    """
    root = repo_root or _find_repo_root()
    target_domain = domain.strip().strip("/")

    if target_domain in ("root", "", "."):
        path = os.path.join(root, "AGENTS.md")
    else:
        path = os.path.join(root, target_domain, "AGENTS.md")

    if not os.path.exists(path):
        raise FileNotFoundError(f"No AGENTS.md found for domain '{domain}' at '{path}'")

    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def build_index(repo_root: Optional[str] = None) -> Dict[str, Any]:
    """
    Re-scan repository and perform a complete rebuild of topological artifacts and vector database.
    """
    root = repo_root or _find_repo_root()
    engine = ContextSearchEngine(repo_root=root)
    return engine.build_index()
