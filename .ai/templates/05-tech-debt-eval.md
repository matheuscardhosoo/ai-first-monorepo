---
eval_id: "EVAL-[000]"
eval_date: "YYYY-MM-DD"
evaluator_agent: "[Agent Identifier]"
target_domain: "packages/[package-name]" # or apps/[app-name]
health_score: 85 # 0 - 100
status: "pending_review" # pending_review | approved | rejected | epic_created
approved_by: ""
---

# Continuous Evaluation & Technical Debt Report: [Target Domain]

## 1. Context & Scope

This evaluation audits the code quality, architectural compliance, and AI smells within `[target_domain]` against:
- Canonical Architecture: `.ai/skills/00-architecture-standards.md`
- Active System Specs: `docs/specs/`
- Historical ADRs: `docs/adr/`

## 2. Health Score Breakdown

- **Architecture Compliance (40 pts):** [Score / 40]
- **Test Coverage & Isolation (30 pts):** [Score / 30]
- **Code Cleanliness & Type Strictness (20 pts):** [Score / 20]
- **Dependency Hygiene & Decoupling (10 pts):** [Score / 10]
- **Total Health Score:** [Sum / 100]

## 3. Identified Technical Debt & AI Smells

### A. Architectural Drift
- **Violation:** [e.g., Domain package directly imports an application gateway module]
- **Severity:** High
- **Remediation:** Invert dependency using interface contract in `packages/contracts`.

### B. AI-Generated Smells
- **Violation:** [e.g., Duplicated defensive null checks or unused helper functions]
- **Severity:** Medium
- **Remediation:** Remove redundant branches and enforce strict compiler types.

### C. Test Coverage Gaps
- **Violation:** [e.g., Edge cases from EPIC-002 lack automated unit test assertions]
- **Severity:** Medium
- **Remediation:** Add isolated mock unit tests in `packages/[target_domain]/tests/`.

## 4. Human Approval Gate & Next Steps

_Autonomous agents MUST NOT refactor code based solely on an evaluation report. A human code owner must approve the proposed changes to spawn an Epic._

- [ ] Approved by Domain Owner: @[owner]
- **Follow-up Epic ID:** `EPIC-[new-id]` (if approved)
