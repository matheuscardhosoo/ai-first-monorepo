---
spec_id: "SPEC-002"
epic_id: "EPIC-002"
title: "Technical Architecture: Resilient Context Router & Standalone Evaluation Module"
status: "tech_approved" # tech_grilling | tech_approved | superseded
architect: "Staff System Architect"
created_at: "2026-11-06T22:32:00Z"
target_package: "packages/context-router, packages/agent-evals"
---

# SPEC-002: Resilient Context Router & Standalone Evaluation Module

## 1. Technical Requirements & Architecture

### 1.1 Auto-Reindexing & Stale Cache Prevention
- **Incremental Index Synchronization (`sync_index`):**
  - Compare file modification timestamps (`st_mtime`) of `AGENTS.md` files with SQLite chunk timestamps.
  - Granularly re-parse and re-embed only modified/added files in `<5ms`.
  - On-demand staleness check executed automatically at start of `search_context` calls.
- **Lightweight File Watcher (`watcher.py` / CLI `watch`):**
  - Standalone polling daemon checking `AGENTS.md` mtimes with debouncing. Zero external library dependencies.
- **Git Pre-commit Hook:**
  - Shell script in `.ai/scripts/pre-commit-hook.sh` and `.git/hooks/pre-commit`.
  - Automatically indexes modified `AGENTS.md` files, stages index artifacts, and executes accuracy gatekeeper.

### 1.2 "Always-On" Root Governance Pinning
- Root `AGENTS.md` overview & architectural invariants are unconditionally pinned to the top of `synthesized_context` on every search call.
- Top governance rules include:
  - Monorepo Topology & Boundary Invariants (unidirectional import rules, encapsulation).
  - Dual-Grilling SDLC State Machine (`product_approved` -> `tech_approved` -> plan locks).
  - Multi-Agent Concurrency & `make check-locks`.
  - Polyglot execution and Anti-Flailing circuit breaker.
- Include structured `root_governance` object in search response dictionary.

### 1.3 Cross-Domain Dependency Resolution
- Add `depends_on` metadata field to `INDEX.json` and SQLite `domains` schema.
- Extract `depends_on` from frontmatter in localized `AGENTS.md` files, with markdown section parsing fallback.
- In `engine.search()`:
  - For each retrieved domain, resolve its dependencies.
  - Automatically append dependency summaries and public contracts to `synthesized_context`.
  - Include structured `dependencies` array in search response dictionary.

### 1.4 Ephemeral Artifact SDLC Support
- Add `scan_session_artifacts` in `indexer.py`:
  - Detect `intent.md`, `spec.md`, and `plan.md` in the working directory / active session.
  - Also inspect `docs/plans/` for active `in_progress` execution plans.
  - Extract status, active tasks, locked files, and goals.
- In `engine.search()`:
  - Seamlessly append active session context to `synthesized_context`.
  - Include structured `session_artifacts` array in search response dictionary.

### 1.5 Standalone Evaluation Module (`packages/agent-evals`)
- **Decoupled Architecture:** Pure evaluation package under `packages/agent-evals`.
- **A/B Benchmark (`agent_evals.benchmark`):**
  - Approach A: "Raw Filesystem Traversal" (recursive directory crawling and keyword grep).
  - Approach B: "Hybrid Context Router" (`search_context`).
- **Core Metrics Tracked:**
  - Token Reduction Rate: `(Raw Tokens - Router Tokens) / Raw Tokens * 100`
  - First-Pass Retrieval Accuracy: Top-1 and Top-K ground truth matches.
  - Latency / Cycle Time: Duration comparison and speedup multiplier.
  - Prompt Performance & Assistant Time Savings: Dollar savings and estimated engineering hours saved.
- **Gatekeeper Enforcer (`agent_evals.gatekeeper`):**
  - CLI threshold enforcer configured for pre-commit hook and CI pipelines.
  - Fails commit / build if retrieval accuracy drops below threshold (e.g. 100%).
