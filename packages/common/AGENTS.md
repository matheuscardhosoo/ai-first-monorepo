---
domain: "packages/common"
depends_on: []
---

# Common Domain Specification (packages/common/AGENTS.md)

This document is the localized context artifact for the `@monorepo/common` package.

## 1. Domain Responsibility
The `packages/common` package provides pure, cross-cutting primitives, shared utilities, and foundational types:
- Base application error classes (`AppError`, `ValidationError`, `NotFoundError`, `UnauthorizedError`).
- Structured JSON logging wrapper with correlation ID propagation.
- String, date, and UUID utility functions.
- Common HTTP status constants and response envelope builders.

## 2. Invariants & Governance
1. **Pure & Deterministic:** Common utilities should be pure functions whenever possible.
2. **Zero Inbound Dependencies:** `packages/common` must have **zero monorepo internal dependencies**. It cannot import from `packages/*` or `apps/*`.
3. **No Heavy Third-Party Bloat:** Avoid adding massive npm/pip packages to `common` to keep compilation and agent context lean.
