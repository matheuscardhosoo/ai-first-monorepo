---
incident_id: "INC-[000]"
date: "YYYY-MM-DD"
severity: "high" # low | medium | high | critical
status: "investigating" # investigating | reproduced | resolved
affected_services:
  - "apps/[app-name]"
  - "packages/[package-name]"
resolved: false
resolved_by: ""
---

# Root Cause Analysis (RCA): [Incident Title]

## 1. Incident Symptom & Impact

- **Observed Behavior:** [What broke? Provide error message, stack trace, or unintended state]
- **User / Business Impact:** [How were end users or business processes affected?]
- **First Detected:** [Timestamp or CI Run URL]

## 2. Five-Whys Investigation

1. **Why did the failure occur?**
   - Answer: [Immediate technical fault]
2. **Why did that fault happen?**
   - Answer: [Direct trigger or invalid input state]
3. **Why was that invalid input state possible?**
   - Answer: [Missing validation, improper boundary contract, or unexpected edge case]
4. **Why was this edge case not caught prior to deployment?**
   - Answer: [Test coverage gap or untested failure mode during Tech Grilling]
5. **Why was the test coverage or failure mode missing?**
   - Answer: [Root architectural or process reason]

## 3. The Verifiable Fix

### Reproduction Test (Mandatory)
A dedicated test was written that reproduced the bug before fixing it:
- **Test File:** `packages/[domain]/tests/...`
- **Test Command:** `make test-domain DOMAIN=packages/[domain]`

### Code Remediation
- **Files Modified:** [List files changed]
- **Fix Summary:** [Describe architectural change made to eliminate root cause]

## 4. AI-Native Memory Loop & Prevention

_To ensure AI agents never repeat this mistake across the monorepo:_

- [ ] Added prevention guideline to `docs/knowledge/lessons-learned.md`.
- [ ] If architectural drift occurred, updated `.ai/skills/00-architecture-standards.md`.
- [ ] Added regression test to CI suite.
