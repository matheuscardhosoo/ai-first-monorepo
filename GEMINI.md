# Google Gemini Antigravity Configuration (GEMINI.md)

> **CANONICAL SPECIFICATION:** This repository follows the universal multi-agent standard defined in [AGENTS.md](file:///Users/matheus/Code/side-projects/ai-first-monorepo/AGENTS.md). Refer to `AGENTS.md` for complete architecture, state machines, and protocols.

## Quick Reference for Gemini Antigravity

- **Master Specification:** [AGENTS.md](file:///Users/matheus/Code/side-projects/ai-first-monorepo/AGENTS.md)
- **Architecture Standards:** [.ai/skills/00-architecture-standards.md](file:///Users/matheus/Code/side-projects/ai-first-monorepo/.ai/skills/00-architecture-standards.md)
- **Living Registries:**
  - Epics: `docs/epics/`
  - System Specs: `docs/specs/`
  - Execution Plans & Locks: `docs/plans/`
  - Architecture Decisions: `docs/adr/`
  - Knowledge Base & Memory: `docs/knowledge/`

### Key Guardrails
1. **Dual Grilling Gate:** Verify `product_approved` on Epics before starting Tech Design, and `tech_approved` on Specs before writing code.
2. **Lock Audit:** Always execute `make check-locks` before acquiring file locks in `docs/plans/`.
3. **Polyglot Dispatch:** Use `make test-domain DOMAIN=[path]` for targeted validation.
4. **Cost Optimization:** Follow [`.ai/cost-optimization.md`](file:///Users/matheus/Code/side-projects/ai-first-monorepo/.ai/cost-optimization.md). Route lightweight tasks (code execution, tests, subagents) to Gemini Flash, reserving Gemini Pro for Discovery and Architecture Grilling. Isolate sessions per phase.
