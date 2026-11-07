# ADR 0002: Hybrid Context Discovery and Routing for Distributed AGENTS.md

## Status
Accepted

## Context
In this AI-first monorepo, localized `AGENTS.md` files are distributed across apps and packages (`apps/*/AGENTS.md`, `packages/*/AGENTS.md`, and root `./AGENTS.md`). These artifacts serve as the authoritative boundaries, contracts, and invariants for each autonomous domain.

However, raw filesystem traversal presents significant friction for autonomous coding agents:
1. **Context Window Exhaustion:** An agent recursively crawling directories and opening files consumes thousands of tokens before writing a single line of code, blowing token budgets and saturating prompt caches.
2. **High Latency & Flailing:** Shell commands like `find`, `ls -R`, and recursive greps produce multi-step agent flailing, leading to lost focus and hallucinations.
3. **Semantic Mismatch:** High-level developer intents (e.g., *"Implement auth middleware"* or *"Postgres connection pool"*) rarely match literal directory paths unless guided by semantic mapping.

## Options Considered

### Option A: Raw Filesystem Crawling & Grep
- **Pros:** Zero implementation cost, no index files to maintain.
- **Cons:** High token consumption, slow multi-turn tool loops, fragile against renamed directories, zero semantic capability.

### Option B: Heavy External Vector Database (ChromaDB / Milvus / Qdrant / Pinecone)
- **Pros:** Full neural embeddings, dense semantic clustering.
- **Cons:** Heavy runtime dependency footprint (C++ compilers, binary wheels, daemon processes, multi-hundred MB model weights), network dependencies or container lifecycles, unsuitable for rapid local CLI execution and lightweight CI runners.

### Option C: Pure Static Topological Tree (`INDEX.json` / `MAP.md` only)
- **Pros:** Zero-dependency, deterministic, O(1) lookup when the domain is already known.
- **Cons:** Cannot map vague, colloquial, or cross-cutting user intents to target domains without manual agent reasoning over the entire tree.

### Option D: Two-Tier Hybrid Architecture (Structural Tree + Embedded SQLite FTS5 BM25 + Dense Semantic Vector Index) — **SELECTED**
- **Tier 1 (Structural):** Pre-compiled `INDEX.json` and `MAP.md` providing an O(1) domain hierarchy tree and responsibility matrix.
- **Tier 2 (Hybrid Retrieval):** Embedded SQLite database combining FTS5 (BM25 lexical ranking) with dense local subword n-gram vector cosine similarity (<15ms latency, zero external pip dependencies).
- **Extensible Embeddings:** Zero-friction local deterministic embedder by default, with automatic plug-and-play upgrade to neural models (`fastembed`, `sentence-transformers`) if installed.
- **Agent Tooling:** Standardized `search_context(intent, top_k=3)` callable function, CLI utility, root Makefile targets, and Model Context Protocol (MCP) server interface.

## Decision
We adopt **Option D (Two-Tier Hybrid Architecture)**. The subsystem is implemented in `packages/context-router`:

1. **Topological Tree Map:**
   The scanner compiles root `INDEX.json` (machine-readable) and `MAP.md` (agent-readable markdown table and ASCII hierarchy tree).
2. **Lexical + Dense Semantic Engine:**
   Stored in `.ai/cache/context_index.db`. Search calculates a composite score:
   $$\text{Score} = 0.40 \times S_{\text{semantic}} + 0.35 \times S_{\text{bm25}} + 0.15 \times S_{\text{domain\_boost}} + 0.10 \times S_{\text{title\_boost}}$$
3. **Pluggable & Zero-Dependency Execution:**
   The default vectorizer uses subword character n-grams and token hashing in pure Python 3 standard library (`sqlite3`, `math`, `hashlib`, `re`). It executes in ~2ms with 0 third-party packages required.
4. **Agentic Interface:**
   - Python: `search_context(intent, top_k=3)`
   - CLI: `make search-context INTENT="<task>"` or `python3 .ai/scripts/context-router.py search "<task>"`
   - MCP Server: Registered in `.ai/mcp/servers.json` (`context-router`) for direct agent tool calling.
5. **Generic Specification Consolidation:**
   Legacy tool-specific files (`CLAUDE.md`) are merged into the generic root `AGENTS.md` and symlinked, ensuring a single canonical source of truth.

## Consequences

### Positive
- **Instantaneous Local Retrieval:** Typical query latency is 1.5ms to 3ms, executing completely offline and in-process.
- **Massive Token Reductions:** Agents load only the synthesized domain rules and excerpts (~250 tokens) instead of parsing entire repositories (~25,000+ tokens), achieving >90% prompt cost savings.
- **Universal Tooling:** Compatible with Google Antigravity, Anthropic Claude Code, Cursor, Windsurf, and terminal CLI.
- **Zero Native Build Failures:** Standard library fallback ensures it runs out of the box on macOS, Linux, and CI without compilation steps.

### Negative & Mitigations
- **Index Drift:** Adding new `AGENTS.md` files requires an index update.
  - *Mitigation:* `make index-context` executes in <35ms; the engine also automatically detects missing indices and builds them on the first query.

## Compliance & Enforcement
- All autonomous agents must use `search_context` or `MAP.md` rather than performing unguided filesystem searches.
- Skill 05 (Code Review) and Skill 07 (Continuous Evaluator) verify that newly created apps and packages supply a localized `AGENTS.md` and that `make index-context` is run.
