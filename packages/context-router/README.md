# Context Router (`@monorepo/context-router`)

The Context Router is the discovery and retrieval layer for distributed `AGENTS.md` context files in this monorepo. It replaces raw filesystem crawling with a two-tier hybrid search strategy:
1. **Tree-Based Topological Routing:** Automatically maps the entire monorepo into `INDEX.json` and `MAP.md`.
2. **Semantic & Lexical Hybrid Search:** Uses SQLite FTS5 BM25 + dense local subword vector cosine similarity (<15ms latency, zero external pip dependencies).

## Usage

### 1. Terminal / CLI
```bash
# Re-index all AGENTS.md files
make index-context
# or
python3 .ai/scripts/context-router.py index

# Search for relevant domain context
make search-context INTENT="Implement auth middleware"
# or
python3 .ai/scripts/context-router.py search "Implement auth middleware" --top-k 3
```

### 2. Python API
```python
from context_router import search_context, get_topological_map

# Retrieve synthesized context for a task
result = search_context("Implement auth middleware", top_k=3)
print(result["synthesized_context"])
```

### 3. Model Context Protocol (MCP) Server
Registered in `.ai/mcp/servers.json`. AI agents (Claude Code, Antigravity, Cursor) can call:
- `search_context(intent: string, top_k: int, domain: string)`
- `get_topological_map()`
- `get_domain_context(domain: string)`
