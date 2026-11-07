#!/usr/bin/env bash
# ==============================================================================
# AI-First Monorepo Git Pre-Commit Hook
# 1. Audits active multi-agent file locks (docs/plans/).
# 2. Automatically reindexes SQLite & INDEX.json if any AGENTS.md was modified.
# 3. Enforces the AI Agent Context Retrieval Quality Gatekeeper (>=90% accuracy).
# ==============================================================================

set -e

REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
cd "$REPO_ROOT"

echo "=== [AI-First Pre-Commit Hook] Validating Commit Invariants ==="

# 1. Audit active execution plans and file locks
echo "[1/3] Auditing active multi-agent file locks..."
make check-locks

# 2. Check for modified AGENTS.md files and auto-sync context index
CHANGED_AGENTS=$(git diff --cached --name-only | grep -E "(^|/)AGENTS\.md$" || true)
if [ -n "$CHANGED_AGENTS" ]; then
    echo "[2/3] AGENTS.md modification detected in staged files:"
    echo "$CHANGED_AGENTS"
    echo "Triggering granular re-index..."
    PYTHONPATH="packages/context-router:$PYTHONPATH" python3 packages/context-router/context_router/cli.py sync
    # Auto-stage regenerated artifacts
    git add INDEX.json MAP.md .ai/cache/context_index.db 2>/dev/null || true
    echo "Topological artifacts updated and re-staged."
else
    echo "[2/3] No staged AGENTS.md modifications detected. Context index is clean."
fi

# 3. Run Agent Retrieval Quality Gatekeeper
echo "[3/3] Enforcing AI Retrieval Accuracy Gatekeeper..."
PYTHONPATH="packages/agent-evals:packages/context-router:$PYTHONPATH" python3 packages/agent-evals/agent_evals/gatekeeper.py --threshold 0.90

echo "=== [AI-First Pre-Commit Hook] All Invariant Gates Passed! ==="
exit 0
