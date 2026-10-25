# Execution Plans & File Locks Directory

This directory is the **active registry** for multi-agent coordination. Before any agent modifies files, it registers its active file locks here using Skill 03 (`03-development-execution.md`).

## Naming Convention
- Files must be named `PLAN-[epic_id]-[seq].md` (e.g. `PLAN-EPIC-001-01.md`).
- Must strictly follow `.ai/templates/03-execution-plan.md`.

## Lifecycle States
- `pending`: Plan drafted, locks not yet acquired.
- `in_progress`: Locks actively acquired. No other agent may write to any file in `locked_files`.
- `completed`: Implementation and tests validated. Locks released.
- `failed` / `rolled_back`: Plan aborted. Locks released.
