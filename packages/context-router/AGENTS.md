---
domain: "packages/context-router"
depends_on:
  - "packages/common"
---

# Context Router Domain Specification (packages/context-router/AGENTS.md)

This document is the localized context artifact for the `@monorepo/context-router` package.

## 1. Domain Responsibility
The `packages/context-router` package provides the discovery, indexing, and hybrid retrieval engine for all distributed `AGENTS.md` context files across the monorepo:
- Topological repository scanning and generation of `INDEX.json` and `MAP.md`.
- Semantic chunking of markdown context artifacts with token estimation.
- Hybrid search engine combining SQLite FTS5 BM25 full-text search with dense local vector cosine similarity.
- Agentic retrieval tools exposed via Python API, CLI, and Model Context Protocol (MCP) server.

## 2. Public API Contract
The package exposes the following functions:
- `search_context(intent: str, top_k: int = 3, domain_filter: str = None) -> dict`: Perform hybrid search and retrieve synthesized context.
- `get_topological_map() -> str`: Return formatted markdown map of all domains and their responsibilities.
- `get_domain_context(domain: str) -> str`: Retrieve the raw localized `AGENTS.md` content for a specific domain.
- `build_index(repo_root: str = None) -> dict`: Re-scan and re-index all distributed `AGENTS.md` files.

## 3. Invariants & Governance
1. **Zero Mandatory External Dependencies:** The core embedder and search engine must run purely on Python 3 standard library (`sqlite3`, `math`, `json`, `hashlib`, `re`).
2. **Sub-15ms Latency:** Search queries must complete in under 15ms locally to prevent blocking agent workflows.
3. **Deterministic Output:** Results must be stably ranked and reproducible for identical queries.
4. **Isolated Memory / Storage:** Cache databases and generated indices must reside in `.ai/cache/` or designated root artifacts (`INDEX.json`, `MAP.md`).
