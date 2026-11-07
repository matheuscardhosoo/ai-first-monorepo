---
epic_id: "EPIC-002"
title: "Context Router Resilience, Root Governance, Dynamic SDLC Context & Standalone Evals"
status: "product_approved" # product_grilling | product_approved | closed
owner: "Staff Product Manager"
created_at: "2026-11-06T22:30:00Z"
target_release: "v1.2.0"
priority: "P0"
---

# EPIC-002: Context Router Resilience, Root Governance & Standalone Evals

## 1. Executive Summary & Problem Statement
The hybrid context router successfully provides sub-3ms retrieval and token savings for localized `AGENTS.md` discovery. However, production agentic workflows have revealed four critical SDLC operational failure modes:
1. **Cache Drift / Stale Index:** Changes to `AGENTS.md` require manual `make index-context`, leading to stale retrieval if forgotten.
2. **Missing Global Guardrails:** Subdomain queries omit root architectural rules (unidirectional import rules, dual-grilling approvals, file lock requirements), risking invariant violations.
3. **Implicit Dependencies:** If an agent touches `apps/api-gateway`, it misses the public contracts of `packages/common` or `packages/auth`, requiring secondary queries.
4. **Disconnection from Active Sessions:** The agent cannot access active session files (`intent.md`, `spec.md`, `plan.md`), causing state desynchronization.

Additionally, engineering leadership requires an automated, decoupled evaluation module (`packages/agent-evals`) to benchmark context router performance against raw filesystem traversal across sprints and enforce accuracy gates in pre-commit and CI.

## 2. Business Objectives & Success Criteria
- **Zero Stale Cache Incidents:** Automatic reindexing on `AGENTS.md` changes via file watcher, pre-commit hook, and on-demand staleness check.
- **100% Root Governance Invariant Coverage:** All queries unconditionally prepend root governance rules.
- **Cross-Domain Contract Visibility:** Automatic dependency context enrichment for any retrieved domain.
- **Seamless SDLC Session Awareness:** Active `plan.md`, `spec.md`, and `intent.md` artifacts seamlessly retrievable alongside domain rules.
- **Benchmark Suite & Quality Gate:** Standalone A/B evaluation suite tracking Token Reduction Rate (>85%), First-Pass Retrieval Accuracy (100%), and Latency (<15ms), enforced in Git pre-commit.

## 3. Scope Boundaries
- **In Scope:**
  - `packages/context-router`: auto-reindexing/sync, file watcher, root governance pinning, `depends_on` schema & dependency resolution, ephemeral session artifact tracking.
  - `packages/agent-evals`: standalone decoupled A/B benchmarking module, metric calculation, pre-commit gatekeeper, and documentation.
  - Monorepo tooling: updated root `Makefile`, git hooks, and updated `AGENTS.md` files.
- **Out of Scope:**
  - Modification of application business logic in `apps/*`.
