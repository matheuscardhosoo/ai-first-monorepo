---
plan_id: "PLAN-[epic_id]-[00]"
epic_id: "EPIC-[000]"
spec_id: "SPEC-[000]"
status: "pending" # pending | in_progress | completed | failed | rolled_back
agent_id: "[Agent Identifier, e.g., gemini-worker-01]"
created_at: "YYYY-MM-DDTHH:MM:SSZ"
locked_files:
  - path: "packages/domain/src/index.ts"
    mode: "exclusive" # exclusive | shared-read
    acquired_at: "YYYY-MM-DDTHH:MM:SSZ"
---

# Execution Plan: [Short Title]

## 1. Pre-Flight Verification Gate

Before setting status to `in_progress` or modifying any code:
- [ ] Associated Epic (`docs/epics/[epic_id].md`) is in `product_approved` status.
- [ ] Associated Spec (`docs/specs/[spec_id].md`) is in `tech_approved` status.
- [ ] Active lock check passes: Run `make check-locks` to guarantee zero lock collisions in `docs/plans/`.
- [ ] Target repository dependencies are verified.

## 2. Distributed Resource Locks

The following files will be exclusively modified during this plan:

| File Path | Lock Mode | Rationale |
| :--- | :--- | :--- |
| `packages/[domain]/src/...` | Exclusive Write | Implementing new contract method |
| `packages/[domain]/tests/...` | Exclusive Write | Adding unit and edge case tests |

## 3. Step-by-Step Implementation Sequence

_Execute in small, verifiable atomic steps. Update checkboxes and validate before moving forward._

- [ ] **Step 1: Test Scaffold (TDD Red Phase)**
  - **Action:** Write failing unit test reproducing the spec contract requirements.
  - **Verification:** Run `make test-domain DOMAIN=packages/[domain]` (Expect failure).

- [ ] **Step 2: Core Domain Implementation (TDD Green Phase)**
  - **Action:** Implement minimum necessary code in `packages/[domain]` to satisfy test.
  - **Verification:** Run `make test-domain DOMAIN=packages/[domain]` (Expect pass).

- [ ] **Step 3: Quality & Contract Verification**
  - **Action:** Run domain lint and type checks.
  - **Verification:** Run `make lint` and `make type-check`.

- [ ] **Step 4: Integration & E2E Validation**
  - **Action:** Connect calling application flow in `apps/[app]`.
  - **Verification:** Run full acceptance test suite.

## 4. Rollback Strategy & Commands

If any step fails or tests cannot pass, execute the following to return the codebase to a clean state:

```bash
# Discard uncommitted working changes in locked files
git checkout -- packages/[domain] apps/[app]

# Clean build artifacts
make clean

# Set plan status in this file to: failed or rolled_back to release file locks
```
