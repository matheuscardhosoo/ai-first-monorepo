# Architecture Standards & Monorepo Governance

This document defines the canonical architectural standards for this monorepo. All AI agents and human engineers must adhere to these rules across all phases of the SDLC.

---

## 1. Monorepo Topology & Boundaries

```
root/
├── apps/         # Deployable end-user applications (APIs, Web SPAs, Microservices, CLIs)
├── packages/     # Reusable business domains, shared libraries, and core primitives
├── docs/         # Living documentation, Epics, Specs, Plans, ADRs, and Knowledge Base
└── .ai/          # Agent skills, prompt templates, and automation configurations
```

### Dependency Rules
1. **Unidirectional Flow:** `apps/` may import from `packages/`. `packages/` must **NEVER** import from `apps/`.
2. **Package Isolation:** `packages/` may depend on other utility packages only via explicit interfaces and declared dependencies. Circular dependencies between packages are strictly forbidden.
3. **Public Contract Encapsulation:** Every package must expose a designated public API (e.g. `index.ts`, `mod.rs`, `__init__.py`, `api.go`). Consumers must never import deeply nested internal package modules.

---

## 2. Polyglot Engineering Standards

1. **Independent Toolchains:** Each app or package encapsulates its own dependency management, linting, and testing harness (e.g. `package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod`).
2. **Unified Root Orchestration:** Every app and package must integrate with the root `Makefile` targets (`lint`, `test`, `build`, `type-check`).
3. **Contract-First Communication:** Cross-service or inter-language communication must use strongly-typed contracts (OpenAPI, Protocol Buffers, or JSON Schema) stored in `packages/contracts` or documented in `docs/specs/`.

---

## 3. Code Quality & Design Principles

1. **Pure Core, Imperative Shell:** Core business logic in `packages/` should be functional and deterministic, decoupled from I/O, databases, and network transports.
2. **No Implicit / Untyped State:** Untyped variables (e.g., `any` in TypeScript, untyped `dict` in Python, empty `interface{}` in Go) are strictly prohibited in domain boundaries.
3. **Dependency Injection:** Database connections, HTTP clients, and external SDKs must be injected via constructors or parameters, facilitating isolated unit testing with mocks.
4. **Idempotency & Resilience:** All background jobs, webhooks, and asynchronous workers must be idempotent and incorporate retry policies with exponential backoff.

---

## 4. Testing Hierarchy & Guardrails

| Test Type | Scope | Environment | Mocking Rule |
| :--- | :--- | :--- | :--- |
| **Unit Tests** | `packages/` | In-memory | **Mandatory 100% Mocking** of DB, network, file I/O |
| **Contract Tests** | API Boundaries | In-memory / Stubs | Validate schemas against specs |
| **Integration Tests** | `apps/` endpoints | Containerized test runner | Test realistic service workflows |
| **E2E Tests** | Full App Flows | Headless runner | Validate critical path acceptance criteria |

---

## 5. AI Agent Anti-Hallucination Guardrails

1. **Package Verification:** Never import a third-party library without verifying its existence in the package manifest (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`).
2. **Signature Verification:** Never guess method signatures. Read source code or type definitions before invoking internal helpers.
3. **Traceability:** Every new class, function, or data model must trace directly to an approved specification in `docs/specs/`.
