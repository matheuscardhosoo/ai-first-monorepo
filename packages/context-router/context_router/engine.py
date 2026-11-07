"""
Hybrid Search Engine for Distributed AGENTS.md Context Artifacts.
Combines SQLite FTS5 full-text BM25 search with dense local vector similarity,
hierarchical domain boosting, always-on root governance, cross-domain dependency
resolution, and active ephemeral SDLC session artifact tracking.
"""

import os
import re
import json
import sqlite3
import time
from typing import List, Dict, Any, Optional, Set, Tuple

from .embeddings import (
    BaseEmbeddingEngine,
    get_embedding_engine,
    pack_vector,
    unpack_vector,
    tokenize_text,
)
from .indexer import (
    RepositoryContextScanner,
    ContextChunk,
    parse_agents_file,
    scan_session_artifacts,
    IGNORE_DIRS,
)

DEFAULT_DB_REL_PATH = os.path.join(".ai", "cache", "context_index.db")


class ContextSearchEngine:
    """Hybrid SQLite FTS5 + Dense Vector retrieval engine with dynamic SDLC resilience."""

    def __init__(self, repo_root: str, db_path: Optional[str] = None):
        self.repo_root = os.path.abspath(repo_root)
        self.db_path = db_path or os.path.join(self.repo_root, DEFAULT_DB_REL_PATH)
        self.embedder: BaseEmbeddingEngine = get_embedding_engine()
        self._ensure_db()

    def _get_connection(self) -> sqlite3.Connection:
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_db(self):
        """Create tables and virtual FTS5 tables if they don't exist."""
        with self._get_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS metadata (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS domains (
                    domain TEXT PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    depends_on_json TEXT NOT NULL,
                    keywords_json TEXT NOT NULL,
                    mtime REAL NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS chunks (
                    chunk_id TEXT PRIMARY KEY,
                    domain TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    section_title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    keywords_json TEXT NOT NULL,
                    token_count INTEGER NOT NULL,
                    vector BLOB NOT NULL,
                    mtime REAL NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
                    chunk_id UNINDEXED,
                    domain,
                    file_path,
                    section_title,
                    content,
                    summary,
                    keywords,
                    tokenize='porter unicode61'
                );
                """
            )
            conn.commit()

    def is_indexed(self) -> bool:
        """Check if index contains indexed chunks."""
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM chunks;")
                row = cursor.fetchone()
                return row is not None and row[0] > 0
        except Exception:
            return False

    def build_index(self) -> Dict[str, Any]:
        """
        Scan repository, write INDEX.json and MAP.md, and index all chunks into SQLite.
        """
        start_time = time.time()
        scanner = RepositoryContextScanner(self.repo_root)
        scanned_files = scanner.scan()

        artifacts = scanner.write_artifacts(scanned_files)

        total_chunks = 0
        total_tokens = 0

        with self._get_connection() as conn:
            conn.execute("DELETE FROM chunks;")
            conn.execute("DELETE FROM chunks_fts;")
            conn.execute("DELETE FROM domains;")

            for item in scanned_files:
                domain = item["domain"]
                conn.execute(
                    """
                    INSERT OR REPLACE INTO domains (
                        domain, file_path, title, summary, depends_on_json, keywords_json, mtime
                    ) VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        domain,
                        item["path"],
                        item["title"],
                        item["summary"],
                        json.dumps(item.get("depends_on", [])),
                        json.dumps(item["keywords"]),
                        item["mtime"],
                    ),
                )

                for chunk in item["chunks"]:
                    vec = self.embedder.embed_text(chunk.content, title=chunk.section_title)
                    vec_blob = pack_vector(vec)

                    conn.execute(
                        """
                        INSERT INTO chunks (
                            chunk_id, domain, file_path, section_title, content,
                            summary, keywords_json, token_count, vector, mtime
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            chunk.chunk_id,
                            chunk.domain,
                            chunk.file_path,
                            chunk.section_title,
                            chunk.content,
                            chunk.summary,
                            json.dumps(chunk.keywords),
                            chunk.token_count,
                            vec_blob,
                            chunk.mtime,
                        ),
                    )

                    keywords_str = " ".join(chunk.keywords)
                    conn.execute(
                        """
                        INSERT INTO chunks_fts (
                            chunk_id, domain, file_path, section_title, content, summary, keywords
                        ) VALUES (?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            chunk.chunk_id,
                            chunk.domain,
                            chunk.file_path,
                            chunk.section_title,
                            chunk.content,
                            chunk.summary,
                            keywords_str,
                        ),
                    )

                    total_chunks += 1
                    total_tokens += chunk.token_count

            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            conn.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES ('last_indexed_at', ?);",
                (now_iso,),
            )
            conn.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES ('total_domains', ?);",
                (str(len(scanned_files)),),
            )
            conn.execute(
                "INSERT OR REPLACE INTO metadata (key, value) VALUES ('total_chunks', ?);",
                (str(total_chunks),),
            )
            conn.commit()

        duration_ms = (time.time() - start_time) * 1000.0

        return {
            "status": "success",
            "domains_indexed": len(scanned_files),
            "chunks_indexed": total_chunks,
            "total_tokens_estimated": total_tokens,
            "artifacts_generated": artifacts,
            "duration_ms": round(duration_ms, 2),
        }

    def sync_index(self, force: bool = False) -> Dict[str, Any]:
        """
        Auto-Reindexing: Checks file modification timestamps and granularly updates
        only modified, added, or deleted AGENTS.md files in SQLite and INDEX.json/MAP.md.
        """
        start_time = time.time()

        if not self.is_indexed() or force:
            return self.build_index()

        # 1. Discover all AGENTS.md files on disk
        disk_files: Dict[str, Tuple[str, float]] = {}  # domain -> (abs_path, mtime)
        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [
                d
                for d in dirs
                if d not in IGNORE_DIRS
                and not any(root.endswith(os.sep + ign) for ign in IGNORE_DIRS)
            ]
            if "AGENTS.md" in files:
                fpath = os.path.join(root, "AGENTS.md")
                rel = os.path.relpath(fpath, self.repo_root).replace(os.sep, "/")
                dir_name = os.path.dirname(rel)
                dom = "root" if dir_name in ("", ".") else dir_name
                disk_files[dom] = (fpath, os.stat(fpath).st_mtime)

        # 2. Get recorded domain mtimes from database
        db_domains: Dict[str, float] = {}
        with self._get_connection() as conn:
            cur = conn.execute("SELECT domain, mtime FROM domains;")
            for r in cur.fetchall():
                db_domains[r["domain"]] = float(r["mtime"])

        # 3. Identify differences
        modified_domains: Set[str] = set()
        added_domains: Set[str] = set()
        removed_domains: Set[str] = set(db_domains.keys()) - set(disk_files.keys())

        for dom, (fpath, mtime) in disk_files.items():
            if dom not in db_domains:
                added_domains.add(dom)
            elif abs(mtime - db_domains[dom]) > 0.001:
                modified_domains.add(dom)

        if not modified_domains and not added_domains and not removed_domains:
            return {
                "status": "up_to_date",
                "checked_domains": len(disk_files),
                "duration_ms": round((time.time() - start_time) * 1000.0, 2),
            }

        # 4. Perform granular updates
        changed_domains = modified_domains.union(added_domains)
        with self._get_connection() as conn:
            # Handle removed domains
            for dom in removed_domains:
                conn.execute("DELETE FROM chunks WHERE domain = ?;", (dom,))
                conn.execute("DELETE FROM chunks_fts WHERE domain = ?;", (dom,))
                conn.execute("DELETE FROM domains WHERE domain = ?;", (dom,))

            # Handle modified and added domains
            for dom in changed_domains:
                fpath, _ = disk_files[dom]
                parsed = parse_agents_file(fpath, self.repo_root)

                # Delete old records
                conn.execute("DELETE FROM chunks WHERE domain = ?;", (dom,))
                conn.execute("DELETE FROM chunks_fts WHERE domain = ?;", (dom,))
                conn.execute("DELETE FROM domains WHERE domain = ?;", (dom,))

                # Insert updated domain record
                conn.execute(
                    """
                    INSERT INTO domains (
                        domain, file_path, title, summary, depends_on_json, keywords_json, mtime
                    ) VALUES (?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        dom,
                        parsed["path"],
                        parsed["title"],
                        parsed["summary"],
                        json.dumps(parsed.get("depends_on", [])),
                        json.dumps(parsed["keywords"]),
                        parsed["mtime"],
                    ),
                )

                # Insert updated chunks
                for chunk in parsed["chunks"]:
                    vec = self.embedder.embed_text(chunk.content, title=chunk.section_title)
                    vec_blob = pack_vector(vec)

                    conn.execute(
                        """
                        INSERT INTO chunks (
                            chunk_id, domain, file_path, section_title, content,
                            summary, keywords_json, token_count, vector, mtime
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            chunk.chunk_id,
                            chunk.domain,
                            chunk.file_path,
                            chunk.section_title,
                            chunk.content,
                            chunk.summary,
                            json.dumps(chunk.keywords),
                            chunk.token_count,
                            vec_blob,
                            chunk.mtime,
                        ),
                    )

                    keywords_str = " ".join(chunk.keywords)
                    conn.execute(
                        """
                        INSERT INTO chunks_fts (
                            chunk_id, domain, file_path, section_title, content, summary, keywords
                        ) VALUES (?, ?, ?, ?, ?, ?, ?);
                        """,
                        (
                            chunk.chunk_id,
                            chunk.domain,
                            chunk.file_path,
                            chunk.section_title,
                            chunk.content,
                            chunk.summary,
                            keywords_str,
                        ),
                    )

            # Update metadata
            now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            conn.execute("INSERT OR REPLACE INTO metadata (key, value) VALUES ('last_indexed_at', ?);", (now_iso,))
            conn.commit()

        # 5. Regenerate INDEX.json and MAP.md
        scanner = RepositoryContextScanner(self.repo_root)
        scanned_files = scanner.scan()
        artifacts = scanner.write_artifacts(scanned_files)

        duration_ms = (time.time() - start_time) * 1000.0

        return {
            "status": "updated",
            "modified_domains": sorted(list(modified_domains)),
            "added_domains": sorted(list(added_domains)),
            "removed_domains": sorted(list(removed_domains)),
            "artifacts_updated": artifacts,
            "duration_ms": round(duration_ms, 2),
        }

    def _sanitize_fts_query(self, query: str) -> str:
        """Sanitize query string into valid FTS5 boolean match expression."""
        tokens = tokenize_text(query)
        if not tokens:
            return ""
        terms = [f'"{re.sub(r"[^a-zA-Z0-9]", "", t)}"*' for t in tokens if len(t) > 1]
        return " OR ".join(terms)

    def _get_root_governance(self) -> Dict[str, Any]:
        """
        Retrieve Universal Root Governance and monorepo architectural invariants
        directly from the root AGENTS.md document.
        """
        root_agents_path = os.path.join(self.repo_root, "AGENTS.md")
        root_summary = (
            "Canonical Source of Truth (SOT) defining monorepo topology, dual-grilling SDLC state "
            "machines, multi-agent file locks, and polyglot command guardrails."
        )

        invariants = [
            "Unidirectional Dependency: apps/ may import from packages/; packages/ must NEVER import from apps/.",
            "Encapsulation: Packages interact only via declared public contracts; deep internal imports are prohibited.",
            "No Circular Dependencies: Circular imports between packages will be rejected.",
            "Dual-Grilling SDLC: PO gate (product_approved) before tech design; Lead Architect gate (tech_approved) before code.",
            "Concurrency & Lock Engine: Audit locks with 'make check-locks' before modifying files; halt on conflict.",
            "Cost & Execution Guardrails: Anti-flailing circuit breaker (max 2 test fix attempts); bounded tool execution; strict typing.",
        ]

        if os.path.exists(root_agents_path):
            with open(root_agents_path, "r", encoding="utf-8") as f:
                root_text = f.read()
            match = re.search(r"## 1\.\s+Core Architecture & Monorepo Topology\s*\n(.*?)(?=\n## 2\.|\Z)", root_text, re.DOTALL)
            if match:
                inv_text = match.group(1).strip()
                parsed_invariants = [
                    re.sub(r"^\d+\.\s+", "", l).strip()
                    for l in inv_text.splitlines()
                    if re.match(r"^\d+\.\s+\*\*", l)
                ]
                if parsed_invariants:
                    invariants = parsed_invariants

        return {
            "source": "AGENTS.md",
            "title": "Universal AI Agent Specification",
            "summary": root_summary,
            "invariants": invariants,
        }

    def _get_domain_dependencies(self, domains: List[str]) -> List[Dict[str, Any]]:
        """
        Resolve cross-domain dependencies for retrieved domains, returning their summaries
        and public API contracts.
        """
        dependencies: List[Dict[str, Any]] = []
        retrieved_set = set(domains)
        resolved_deps: Set[str] = set()

        with self._get_connection() as conn:
            for dom in domains:
                cur = conn.execute("SELECT depends_on_json FROM domains WHERE domain = ?;", (dom,))
                row = cur.fetchone()
                if not row or not row["depends_on_json"]:
                    continue

                try:
                    deps_list = json.loads(row["depends_on_json"])
                except Exception:
                    deps_list = []

                for dep in deps_list:
                    if dep in retrieved_set or dep in resolved_deps or dep in ("root", ""):
                        continue

                    resolved_deps.add(dep)

                    # Retrieve dependency metadata and contract chunk
                    cur_dep = conn.execute("SELECT * FROM domains WHERE domain = ?;", (dep,))
                    dep_row = cur_dep.fetchone()
                    if not dep_row:
                        continue

                    # Retrieve public contract or overview chunk if available
                    cur_chunk = conn.execute(
                        """
                        SELECT section_title, content, summary FROM chunks
                        WHERE domain = ? AND (section_title LIKE '%Contract%' OR section_title LIKE '%Overview%')
                        ORDER BY section_title LIKE '%Contract%' DESC
                        LIMIT 1;
                        """,
                        (dep,),
                    )
                    chunk_row = cur_chunk.fetchone()
                    excerpt = chunk_row["summary"] if chunk_row else dep_row["summary"]
                    contract_title = chunk_row["section_title"] if chunk_row else "Overview"

                    dependencies.append(
                        {
                            "domain": dep,
                            "required_by": dom,
                            "file_path": dep_row["file_path"],
                            "title": dep_row["title"],
                            "summary": dep_row["summary"],
                            "contract_section": contract_title,
                            "excerpt": excerpt,
                        }
                    )

        return dependencies

    def search(
        self,
        query: str,
        top_k: int = 3,
        domain_filter: Optional[str] = None,
        include_session: bool = True,
        session_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute hybrid search: FTS5 BM25 + dense vector cosine similarity + domain boost.
        Unconditionally pins Root Governance to the top, automatically resolves cross-domain
        dependencies, and appends active ephemeral SDLC session artifacts.
        """
        start_time = time.time()
        query_clean = query.strip()

        # 0. Prevent stale cache: run incremental sync
        self.sync_index()

        if not query_clean:
            return {
                "query": query,
                "top_k": top_k,
                "results": [],
                "synthesized_context": "No query provided.",
                "duration_ms": 0.0,
            }

        # 1. Compute query vector
        query_vec = self.embedder.embed_text(query_clean)
        query_tokens = set(tokenize_text(query_clean))

        with self._get_connection() as conn:
            # 2. Perform FTS5 lexical match
            fts_scores: Dict[str, float] = {}
            fts_query_str = self._sanitize_fts_query(query_clean)
            if fts_query_str:
                try:
                    cursor = conn.execute(
                        """
                        SELECT chunk_id, bm25(chunks_fts) as rank
                        FROM chunks_fts
                        WHERE chunks_fts MATCH ?
                        ORDER BY rank
                        LIMIT 50;
                        """,
                        (fts_query_str,),
                    )
                    for row in cursor.fetchall():
                        raw_rank = float(row["rank"])
                        normalized_bm25 = 1.0 / (1.0 + max(0.0, raw_rank))
                        fts_scores[row["chunk_id"]] = normalized_bm25
                except sqlite3.OperationalError:
                    pass

            # 3. Retrieve chunks for vector similarity & domain boost
            if domain_filter:
                cursor = conn.execute(
                    "SELECT * FROM chunks WHERE domain = ? OR domain LIKE ?;",
                    (domain_filter, f"{domain_filter}/%"),
                )
            else:
                cursor = conn.execute("SELECT * FROM chunks;")

            rows = cursor.fetchall()
            scored_candidates = []

            for row in rows:
                chunk_id = row["chunk_id"]
                domain = row["domain"]
                title = row["section_title"]
                file_path = row["file_path"]
                content = row["content"]
                summary = row["summary"]
                token_count = row["token_count"]

                chunk_vec = unpack_vector(row["vector"])
                cos_sim = self.embedder.similarity(query_vec, chunk_vec)
                semantic_score = max(0.0, cos_sim)
                lexical_score = fts_scores.get(chunk_id, 0.0)

                domain_parts = set(tokenize_text(domain))
                domain_overlap = len(query_tokens.intersection(domain_parts))
                domain_boost = 0.35 if domain_overlap > 0 else 0.0

                title_parts = set(tokenize_text(title))
                title_overlap = len(query_tokens.intersection(title_parts))
                title_boost = 0.20 if title_overlap > 0 else 0.0

                composite_score = (
                    (0.40 * semantic_score)
                    + (0.35 * lexical_score)
                    + (0.15 * domain_boost)
                    + (0.10 * title_boost)
                )

                excerpt = summary
                if not excerpt or len(excerpt) < 50:
                    clean_lines = [l for l in content.splitlines() if l.strip() and not l.startswith("#")]
                    excerpt = " ".join(clean_lines[:3])[:280]

                scored_candidates.append(
                    {
                        "chunk_id": chunk_id,
                        "domain": domain,
                        "file_path": file_path,
                        "section_title": title,
                        "score": round(composite_score, 4),
                        "semantic_sim": round(semantic_score, 4),
                        "lexical_score": round(lexical_score, 4),
                        "summary": summary,
                        "excerpt": excerpt,
                        "token_count": token_count,
                        "content": content,
                    }
                )

        scored_candidates.sort(key=lambda x: x["score"], reverse=True)
        top_results = scored_candidates[:top_k]

        primary_domain = top_results[0]["domain"] if top_results else "root"
        matched_domains = list(dict.fromkeys(r["domain"] for r in top_results))

        # 4. Resolve Root Governance ("Always-On")
        root_gov = self._get_root_governance()

        # 5. Resolve Cross-Domain Dependencies
        dependencies = self._get_domain_dependencies(matched_domains)

        # 6. Retrieve Ephemeral Session Artifacts (intent.md, spec.md, plan.md)
        session_artifacts: List[Dict[str, Any]] = []
        if include_session:
            session_artifacts = scan_session_artifacts(work_dir=session_dir, repo_root=self.repo_root)

        # 7. Synthesize Comprehensive Lean Markdown Prompt Context
        synth_lines = [
            "### Universal Root Governance (Always-On SOT: AGENTS.md)",
            f"> **Source:** `{root_gov['source']}` | **Status:** Authoritative Global Invariants",
            "",
            "**Core Monorepo Invariants:**",
        ]
        for inv in root_gov["invariants"]:
            synth_lines.append(f"- {inv}")

        # Active Session Artifacts Section (if present)
        if session_artifacts:
            synth_lines.extend([
                "",
                "---",
                "### Active SDLC Session Artifacts (Ephemeral State)",
            ])
            for sa in session_artifacts:
                synth_lines.append(f"- **{sa['kind'].upper()}: `{sa['title']}`** (`{sa['file_path']}` | Status: `{sa['status']}`)")
                if sa.get("locked_files"):
                    locks_str = ", ".join(f"`{f}`" for f in sa["locked_files"])
                    synth_lines.append(f"  - Active File Locks: {locks_str}")
                if sa.get("tasks"):
                    synth_lines.append("  - Active Steps:")
                    for t in sa["tasks"][:4]:
                        synth_lines.append(f"    - {t}")
                if sa.get("summary"):
                    synth_lines.append(f"  - Summary: {sa['summary']}")

        # Primary Intent Results Section
        synth_lines.extend([
            "",
            "---",
            f"### Context Routing for Intent: '{query_clean}'",
            f"- **Recommended Primary Domain:** `{primary_domain}`",
            f"- **Confidence Score:** {top_results[0]['score'] if top_results else 0.0}",
            "",
            "#### Relevant Domain Context Sections:",
        ])

        for idx, res in enumerate(top_results, start=1):
            synth_lines.extend([
                f"{idx}. **[{res['domain']}] {res['section_title']}** (Score: {res['score']})",
                f"   - File: `{res['file_path']}`",
                f"   - Summary: {res['summary']}",
                f"   - Key Rules & Interfaces:",
                f"```markdown",
                f"{res['excerpt']}",
                f"```",
                "",
            ])

        # Cross-Domain Dependencies Section (if any)
        if dependencies:
            synth_lines.extend([
                "#### Cross-Domain Dependencies (Auto-Appended):",
            ])
            for dep in dependencies:
                synth_lines.extend([
                    f"- **`{dep['domain']}`** (Required dependency of `{dep['required_by']}`):",
                    f"  - Spec Path: `{dep['file_path']}`",
                    f"  - Summary: {dep['summary']}",
                    f"  - Contracts / Primitives: `{dep['contract_section']}`",
                    f"```markdown",
                    f"{dep['excerpt']}",
                    f"```",
                    "",
                ])

        synth_lines.extend([
            "> **Agent Instruction:** Restrict domain modifications strictly to the boundaries identified above. "
            "Never bypass root invariants or file locks.",
        ])

        duration_ms = (time.time() - start_time) * 1000.0

        return {
            "query": query_clean,
            "primary_domain": primary_domain,
            "top_k": top_k,
            "root_governance": root_gov,
            "dependencies": dependencies,
            "session_artifacts": session_artifacts,
            "results": [
                {
                    "chunk_id": r["chunk_id"],
                    "domain": r["domain"],
                    "file_path": r["file_path"],
                    "section_title": r["section_title"],
                    "score": r["score"],
                    "summary": r["summary"],
                    "excerpt": r["excerpt"],
                    "token_count": r["token_count"],
                }
                for r in top_results
            ],
            "synthesized_context": "\n".join(synth_lines),
            "duration_ms": round(duration_ms, 2),
        }
