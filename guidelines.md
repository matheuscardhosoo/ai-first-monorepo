# AI Master Context & Monorepo Guidelines (guidelines.md)

> **USAGE IN WEB CHATS (Gemini, Claude, ChatGPT):** Paste or upload this file into the first message of any web-based AI session. It establishes the "Institutional Memory" and rules for this monorepo without requiring IDE-level integration.

---

## 1. Monorepo Architecture & Invariants

```
.
├── apps/               # Deployable services, web frontends, and API gateways
├── packages/           # Reusable business domains, public contracts, and core utilities
├── docs/               # Living specifications and multi-agent coordination registries
│   ├── epics/          # Business initiatives (Skill 01)
│   ├── specs/          # Technical specifications (Skill 02)
│   ├── plans/          # Active execution plans & file locks (Skill 03)
│   ├── adr/            # Architecture Decision Records
│   ├── knowledge/      # Long-term AI memory and lessons learned
│   ├── rca/            # Incident root cause analyses (Skill 06)
│   └── evals/          # Tech debt & code health reports (Skill 07)
└── .ai/                # Agent skills, prompt templates, and MCP configs
```

### Invariants
1. **Unidirectional Dependency:** `apps/` may import from `packages/`. `packages/` must **NEVER** import from `apps/`.
2. **Encapsulated Contracts:** Packages interact only through declared public exports (`index.ts`, `api.go`, `__init__.py`). Deep internal imports are forbidden.
3. **English Only:** All code, comments, documentation, and commit messages must be in English.

---

## 2. The Dual-Grilling SDLC State Machine

Before writing code, two separate grilling and human approval moments are mandatory:

1. **Moment 1: Business Discovery & Product Grilling (Skill 01)**
   - *Role:* Senior Product Manager.
   - *Anti-Contamination Rule:* Strictly no technical details (no DBs, frameworks, APIs). Focus 100% on the problem, user journey, and measurable outcomes.
   - *Deliverable:* `docs/epics/EPIC-[id].md` (`status: product_grilling` $\rightarrow$ Human PO sign-off $\rightarrow$ `status: product_approved`).

2. **Moment 2: Technical Design & Architecture Grilling (Skill 02)**
   - *Role:* Staff Architect.
   - *Traceability Rule:* Every component must trace back to an approved Epic. Stress-test failure modes, scalability, security, and monorepo boundaries.
   - *Deliverable:* `docs/specs/SPEC-[epic_id]-[domain].md` (`status: tech_grilling` $\rightarrow$ Human Lead Architect sign-off $\rightarrow$ `status: tech_approved`).

3. **Moment 3: Safe Execution & File Locking (Skill 03)**
   - *Pre-flight:* Verify Epic is `product_approved` and Spec is `tech_approved`.
   - *Lock Protocol:* Declare all files in `docs/plans/PLAN-[epic_id]-[seq].md` under `locked_files`. Run `make check-locks`. Never modify files locked by parallel agents.

---

## 3. The 7 SDLC Roles & Skills

| Phase | Skill File | Role | Mandatory Output |
| :--- | :--- | :--- | :--- |
| **01. Discovery** | `.ai/skills/01-business-discovery.md` | Senior Product Manager | `docs/epics/EPIC-[id].md` |
| **02. Architecture**| `.ai/skills/02-technical-design.md` | Staff Architect | `docs/specs/SPEC-[id].md` |
| **03. Execution** | `.ai/skills/03-development-execution.md`| Senior Engineer | `docs/plans/PLAN-[id].md` + Code |
| **04. Testing** | `.ai/skills/04-test-validation.md` | QA Automation Lead | Unit & Integration Tests |
| **05. Governance**| `.ai/skills/05-code-review-governance.md`| Principal Gatekeeper | PR Audit / Lock Release |
| **06. Maintenance**| `.ai/skills/06-maintenance-observability.md`| Principal SRE | `docs/rca/INC-[id].md` |
| **07. Evaluation**| `.ai/skills/07-continuous-evaluator.md` | Quality Architect | `docs/evals/EVAL-[id].md` |

---

## 4. Polyglot Command Interface

All agents and humans use the root `Makefile` targets:

```bash
make help                           # List available commands
make check-locks                    # Audit docs/plans/ for lock collisions
make lint                           # Run linters across all domains
make type-check                     # Run type checkers across all domains
make test                           # Run test suites across all domains
make test-domain DOMAIN=packages/auth # Run tests only for a specific domain
make build                          # Build all apps and packages
make clean                          # Clean caches and temporary files
make tree                           # Visualize directory structure
make context DOMAIN=packages/auth   # Pack domain files into prompt context
make context-budget DOMAIN=docs     # Audit token count & budget
```

---

## 5. Cost Optimization Rules for Web Chat Sessions

1. **One Phase per Chat:** Do not execute the entire lifecycle in one long conversation. Close or refresh the session after generating an approved artifact.
2. **Context Budgeting:** Never copy the whole repo into the chat. Use `make context DOMAIN=<target>` to package only relevant files.
3. **Model Selection:** Use reasoning models (Pro/Sonnet) for Discovery (01) and Architecture (02); switch to fast/cheap models (Flash/Haiku) for Code Execution (03) and Testing (04).
4. **Anti-Flailing Limit:** Stop after 2 failed fix attempts on a bug and re-evaluate requirements.

