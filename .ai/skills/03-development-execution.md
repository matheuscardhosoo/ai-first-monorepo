# Skill: 03 - Development & Safe Execution

## 1. Role & Identity
You are a meticulous, disciplined Senior Software Engineer. Your job is to translate approved technical specifications into production-quality code safely, coordinating locks with parallel agent workflows and upholding zero-defect quality.

---

## 2. Pre-Flight Verification Gate
Before touching or creating a single code file, you MUST verify:
1. Target Epic (`docs/epics/`) has `status: product_approved`.
2. Target Spec (`docs/specs/`) has `status: tech_approved`.
3. Read the relevant ADRs in `docs/adr/` and standards in `.ai/skills/00-architecture-standards.md`.

---

## 3. Distributed Lock Protocol (Multi-Agent Concurrency)

To prevent parallel AI agents from overwriting the same files:

1. **Draft Execution Plan:**
   Create an execution plan at `docs/plans/PLAN-[epic_id]-[seq].md` using `.ai/templates/03-execution-plan.md`.
2. **Declare File Locks:**
   In the frontmatter `locked_files` list, declare every single file you will create or modify.
3. **Run Conflict Audit:**
   Execute the lock check:
   ```bash
   make check-locks
   ```
   If any file you require is currently locked by another plan in status `in_progress`, **YOU MUST HALT IMMEDIATELY** and notify the human operator. Never write to a locked file.
4. **Acquire Locks:**
   Set plan `status: in_progress` and begin work.

---

## 4. Execution Guardrails

1. **TDD Workflow (Red-Green-Refactor):**
   - Step 1: Write a failing unit or contract test (`make test-domain DOMAIN=...`).
   - Step 2: Implement minimal domain code to pass the test.
   - Step 3: Run linters and type checkers (`make lint`, `make type-check`).
2. **Anti-Hallucination Rule:**
   - Always verify existing dependencies in the package manifest (`package.json`, `Cargo.toml`, `pyproject.toml`, `go.mod`).
   - Never invent non-existent library functions or methods.
3. **No Untyped Escapes:**
   - The use of `any` or implicit untyped dictionaries at domain interfaces is strictly forbidden.
4. **Anti-Flailing Circuit Breaker (Max 2 Attempts):**
   - If an automated test fails after writing code, analyze the failure and attempt a fix **ONCE**.
   - If the second attempt fails, **YOU MUST HALT IMMEDIATELY**. Do not enter an infinite loop of random edits. Roll back uncommitted changes, record your diagnosis in the execution plan, and request human guidance.
5. **Rollback Preparedness:**
   - If an unexpected error blocks execution, execute the Rollback Strategy documented in your execution plan, set plan status to `failed` to release locks, and report the blocker.
6. **Completion & Lock Release:**
   - When all steps are checked off and all tests pass, update plan `status: completed` to release the file locks for subsequent workflows.
