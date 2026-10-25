# Knowledge Base: Lessons Learned & AI Memory Loop

This document serves as the long-term memory store for AI agents operating in this repository. When bugs are diagnosed (Skill 06 - Maintenance) or technical debt is identified (Skill 07 - Continuous Evaluator), systemic insights are committed here to prevent repeated mistakes.

## Anti-Patterns & Corrective Rules

### 1. Multi-Agent Concurrency & Locks
- **Anti-Pattern:** Modifying files across domains without an active entry in `docs/plans/`.
- **Rule:** Never touch code files in `apps/` or `packages/` unless a plan with status `in_progress` lists the exact files under `locked_files`.

### 2. Polyglot Monorepo Boundaries
- **Anti-Pattern:** Tight coupling between apps and packages (e.g., an app directly importing unexported internal modules of a package).
- **Rule:** Packages must expose explicit public contracts (APIs, types, client SDKs). Apps interact only via defined contracts.

### 3. State & Side Effects
- **Anti-Pattern:** Unbounded global state, unhandled promise rejections, missing database transaction rollbacks.
- **Rule:** Use dependency injection and isolated execution contexts. Every database write must be covered by a rollback strategy.

---

## Resolved Incident Summaries (RCA History)
<!-- Appended automatically by Skill 06 upon completing 04-bug-rca.md -->
