# Anthropic Claude Code Configuration (CLAUDE.md)

> **CANONICAL SPECIFICATION:** This repository follows the universal multi-agent standard defined in [AGENTS.md](file:///Users/matheus/Code/side-projects/ai-first-monorepo/AGENTS.md). Refer to `AGENTS.md` for complete architecture, state machines, and protocols.

## Quick Reference for Claude Code

### The Dual-Grilling State Machine
1. **Moment 1 (Product Grilling):** Skill 01 (`01-business-discovery.md`) -> Output: `docs/epics/EPIC-[id].md` (`status: product_grilling` -> Human approval -> `status: product_approved`).
2. **Moment 2 (Tech Grilling):** Skill 02 (`02-technical-design.md`) -> Output: `docs/specs/SPEC-[id].md` (`status: tech_grilling` -> Human approval -> `status: tech_approved`).
3. **Execution:** Skill 03 (`03-development-execution.md`) -> Acquires locks in `docs/plans/PLAN-[id].md`.

### The 7 SDLC Skills
- `01-business-discovery.md`: Product Manager (Zero tech discussion permitted).
- `02-technical-design.md`: Staff Architect (Failure modes, monorepo boundaries).
- `03-development-execution.md`: Senior Engineer (Safe execution, locks, TDD).
- `04-test-validation.md`: QA Lead (Unit tests mocked, E2E in apps).
- `05-code-review-governance.md`: Gatekeeper (Dual-alignment audit, security).
- `06-maintenance-observability.md`: SRE (Reproduction test first, RCA 5-whys, memory loop).
- `07-continuous-evaluator.md`: Quality Architect (Code debt audit against `.ai/skills/00-architecture-standards.md`).

### Common Commands
- Audit file locks: `make check-locks`
- Run linting: `make lint`
- Run type-checks: `make type-check`
- Run all tests: `make test`
- Run domain test: `make test-domain DOMAIN=packages/[name]`
- Build all: `make build`
- Context pack: `make context DOMAIN=packages/[name]`
- Token budget check: `make context-budget DOMAIN=packages/[name]`

### Cost Optimization Guidelines
- Refer to [`.ai/cost-optimization.md`](file:///Users/matheus/Code/side-projects/ai-first-monorepo/.ai/cost-optimization.md).
- Keep conversations scoped to a single SDLC phase.
- Enforce the 2-attempt anti-flailing limit on test fixes.
- Use Sonnet/Opus for Discovery & Architecture; use Haiku for routine execution and test writing.

All communications, commit messages, and documentation must be in English.
