---
epic_id: "EPIC-[000]"
title: "[Epic Title]"
status: "draft" # draft | product_grilling | product_approved | in_execution | completed | cancelled
owner: "[User or Product Owner]"
priority: "high" # low | medium | high | critical
target_completion_date: "YYYY-MM-DD"
affected_domains:
  - "apps/[app-name]"
  - "packages/[package-name]"
dependencies: [] # List other EPIC_IDs that must be completed first
product_approved_by: "" # Human PO GitHub handle or name
product_approved_at: "" # Timestamp (e.g., 2026-10-25T18:00:00Z)
---

# Epic: [Epic Title]

> **ANTI-CONTAMINATION NOTICE:** This document focuses strictly on business intent, user experience, and measurable outcomes. Technical implementation details (frameworks, databases, protocols) are strictly prohibited here and belong in the System Design Spec.

## 1. Business Context & Problem Statement

[Describe the user pain point or business opportunity. Why is this important right now? What happens to the business or users if we DO NOT build this?]

## 2. Target Personas & User Journeys

- **Primary Persona:** [e.g., Enterprise Admin, End Consumer, Developer]
- **Current Journey:** [How the user solves this today, including friction points]
- **Proposed Journey:** [The desired future state and experience]

## 3. Scope Boundaries & MVP Slicing

### In Scope (MVP)
- [Feature A: Core requirement]
- [Feature B: Essential edge case handling]

### Out of Scope (Explicitly Deferred)
- [Non-essential feature deferred to phase 2]
- [Advanced automation deferred to future epic]

## 4. Monorepo Impact Map (Domain Isolation)

*Identify affected workspaces and subdomains early to prevent parallel agent collisions.*

- **Apps Affected:**
  - `apps/[app-name]`
- **Packages Affected:**
  - `packages/[package-name]`
- **New Bounded Contexts / Services:**
  - `[e.g., packages/payments-core]`
- **Key Files & Directories to Lock Later:**
  - `[e.g., packages/auth/src/contracts/]`

## 5. Open Questions & Assumptions

- **Question 1:** [Open business inquiry to resolve with stakeholders]
- **Assumption 1:** [Core premise assumed true for this version]

## 6. Acceptance Criteria (BDD Scenarios)

### Scenario 1: Happy Path
- **Given** [pre-condition, e.g., an authenticated user with an active subscription]
- **When** [user action, e.g., they submit the transfer request]
- **Then** [expected result, e.g., the funds are debited and a confirmation is received]

### Scenario 2: Error / Edge Case
- **Given** [pre-condition, e.g., the account balance is insufficient]
- **When** [user action, e.g., they attempt to transfer funds exceeding the balance]
- **Then** [expected result, e.g., an actionable error message is displayed and no funds are deducted]

## 7. Definition of Done & Success Metrics

- [ ] Metric 1: [e.g., "Checkout abandonment rate drops by 15%"]
- [ ] Metric 2: [e.g., "End-to-end task completion time is under 45 seconds"]
- [ ] All BDD acceptance criteria validated by end-to-end or integration tests.
- [ ] Technical Design Spec (`docs/specs/SPEC-[epic_id].md`) created and `tech_approved`.

## 8. Product Sign-Off Gate

_Transitioning status from `product_grilling` to `product_approved` requires explicit human review._

- [ ] Reviewed and approved by Product Owner: @[owner]
- Approval Notes: [Optional human remarks]
