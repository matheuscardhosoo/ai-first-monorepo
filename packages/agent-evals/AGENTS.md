---
domain: "packages/agent-evals"
depends_on:
  - "packages/context-router"
  - "packages/common"
---

# Agent Evaluations Domain Specification (packages/agent-evals/AGENTS.md)

This document is the localized context artifact for the `@monorepo/agent-evals` package. All agents working within `packages/agent-evals` must adhere to these domain rules and boundaries.

## 1. Domain Responsibility
The `packages/agent-evals` package is a standalone, decoupled testing and benchmarking suite designed to measure, evaluate, and gate the AI agent routing and context retrieval performance:
- Automated A/B performance benchmarking comparing naive "Raw Filesystem Traversal" vs. "Hybrid Context Router".
- Metric evaluation tracking:
  1. Token Reduction Rate (% context size reduction).
  2. First-Pass Retrieval Accuracy (Top-1 and Top-K ground truth resolution).
  3. Latency & Cycle Time (speedup factor).
  4. Prompt Performance Metrics & Sprint Engineering Time/Cost Savings (Google Cloud SDLC framework).
- Pre-commit and CI Gatekeeper enforcing configurable pass-rate thresholds (e.g. >=90% retrieval accuracy).
- Self-tuning feedback data enabling AI agents to adjust hybrid search scoring weights over time.

## 2. Invariants & Governance
1. **Zero Production Coupling:** Evaluation logic must remain strictly decoupled from application runtime code (`apps/*`).
2. **Deterministic Benchmarking:** Predefined benchmark datasets must cover all core monorepo domains with clear ground truth targets.
3. **CI Gate Enforcement:** Any change that moves or modifies `AGENTS.md` and causes retrieval accuracy to drop below the threshold must fail pre-commit and CI.
4. **Lightweight Execution:** The eval suite must run without external dependencies in <500ms for pre-commit checks.
