"""
Topological Monorepo Scanner, Context Artifact Chunker, and Ephemeral SDLC Tracker.
Discovers distributed AGENTS.md files, parses their semantic sections and cross-domain
dependencies, tracks active session artifacts (intent.md, spec.md, plan.md), and
generates root-level INDEX.json and MAP.md routing artifacts.
"""

import os
import re
import json
import time
import glob
from typing import List, Dict, Any, Optional, Tuple

IGNORE_DIRS = {
    ".git",
    "node_modules",
    "target",
    "dist",
    "build",
    ".turbo",
    ".cache",
    ".pytest_cache",
    "__pycache__",
    ".ai/cache",
}

BACKTICK_REGEX = re.compile(r"`([^`]+)`")
BOLD_REGEX = re.compile(r"\*\*([^*]+)\*\*")
FUNC_REGEX = re.compile(r"([a-zA-Z_][a-zA-Z0-9_]*)\s*\(")
FRONTMATTER_REGEX = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


class ContextChunk:
    """Represents an isolated, indexed section of an AGENTS.md document."""

    def __init__(
        self,
        chunk_id: str,
        domain: str,
        file_path: str,
        section_title: str,
        content: str,
        summary: str,
        keywords: List[str],
        token_count: int,
        mtime: float,
    ):
        self.chunk_id = chunk_id
        self.domain = domain
        self.file_path = file_path
        self.section_title = section_title
        self.content = content
        self.summary = summary
        self.keywords = keywords
        self.token_count = token_count
        self.mtime = mtime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "domain": self.domain,
            "file_path": self.file_path,
            "section_title": self.section_title,
            "content": self.content,
            "summary": self.summary,
            "keywords": self.keywords,
            "token_count": self.token_count,
            "mtime": self.mtime,
        }


def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract YAML frontmatter and remaining markdown body.
    Supports standard pyyaml if installed, or fallback stdlib line-parser.
    """
    match = FRONTMATTER_REGEX.match(content)
    if not match:
        return {}, content

    raw_yaml = match.group(1)
    body = content[match.end():]
    data: Dict[str, Any] = {}

    try:
        import yaml  # type: ignore
        parsed = yaml.safe_load(raw_yaml)
        if isinstance(parsed, dict):
            return parsed, body
    except Exception:
        pass

    # Lightweight stdlib fallback parser
    current_list_key = None
    for line in raw_yaml.splitlines():
        line_clean = line.strip()
        if not line_clean or line_clean.startswith("#"):
            continue

        if line_clean.startswith("- ") and current_list_key:
            val = line_clean[2:].split("#")[0].strip()
            if val.startswith("path:"):
                val = val.split(":", 1)[1].strip().strip("\"'")
            else:
                val = val.strip("\"'")
            if val:
                data.setdefault(current_list_key, []).append(val)
            continue

        if current_list_key and line_clean.startswith("path:"):
            val = line_clean.split(":", 1)[1].split("#")[0].strip().strip("\"'")
            if val and val not in data.get(current_list_key, []):
                data.setdefault(current_list_key, []).append(val)
            continue

        if ":" in line_clean:
            parts = line_clean.split(":", 1)
            key = parts[0].strip()
            raw_val = parts[1].strip()
            # Strip inline comment
            val = raw_val.split("#")[0].strip()

            if not val:
                current_list_key = key
                data[key] = []
            elif val.startswith("[") and val.endswith("]"):
                current_list_key = None
                items = [x.strip().strip("\"'") for x in val[1:-1].split(",") if x.strip()]
                data[key] = items
            else:
                current_list_key = None
                data[key] = val.strip("\"'")

    return data, body


def extract_keywords_from_markdown(text: str) -> List[str]:
    """Extract code identifiers, backticked phrases, and bold terms."""
    keywords = set()

    for item in BACKTICK_REGEX.findall(text):
        cleaned = item.strip()
        if len(cleaned) > 1 and "\n" not in cleaned:
            keywords.add(cleaned)

    for item in BOLD_REGEX.findall(text):
        cleaned = item.strip()
        if 2 < len(cleaned) < 40:
            keywords.add(cleaned)

    for item in FUNC_REGEX.findall(text):
        if len(item) > 2:
            keywords.add(item)

    return sorted(list(keywords))[:25]


def extract_summary(text: str, max_chars: int = 240) -> str:
    """Extract the first 1-2 meaningful sentences of markdown text."""
    lines = [line.strip() for line in text.splitlines() if line.strip() and not line.strip().startswith("#")]
    if not lines:
        return ""
    joined = " ".join(lines)
    cleaned = re.sub(r"[`*#_\[\]]", "", joined)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_chars:
        return cleaned[:max_chars].rstrip() + "..."
    return cleaned


def extract_dependencies(content: str, frontmatter: Dict[str, Any], current_domain: str) -> List[str]:
    """
    Extract declared cross-domain dependencies from frontmatter or markdown sections.
    If frontmatter explicitly provides 'depends_on', it is treated as authoritative.
    """
    deps = set()

    # 1. Frontmatter extraction (Authoritative)
    if "depends_on" in frontmatter:
        fm_deps = frontmatter.get("depends_on")
        if isinstance(fm_deps, list):
            for d in fm_deps:
                if isinstance(d, str) and d.strip():
                    deps.add(d.strip().strip("\"'").strip("/"))
        elif isinstance(fm_deps, str) and fm_deps.strip():
            for d in fm_deps.split(","):
                if d.strip():
                    deps.add(d.strip().strip("\"'").strip("/"))
        deps.discard(current_domain)
        deps.discard("root")
        return sorted(list(deps))

    # 2. Text heuristics fallback (only if frontmatter is omitted)
    dep_patterns = [
        re.compile(r"(?:allowed imports|dependencies|can import from|depends on)[:\s]+([^\n\.]+)", re.IGNORECASE),
    ]

    for pat in dep_patterns:
        for match in pat.finditer(content):
            matched_text = match.group(1) if match.groups() else match.group(0)
            if "prohibited" in matched_text.lower():
                continue
            found_refs = re.findall(r"(?:packages|apps)/[a-zA-Z0-9_-]+", matched_text)
            for ref in found_refs:
                deps.add(ref.strip().strip("/"))

    # Remove self-reference and root
    deps.discard(current_domain)
    deps.discard("root")

    return sorted(list(deps))


def parse_agents_file(file_path: str, repo_root: str) -> Dict[str, Any]:
    """Parse a single AGENTS.md file into structural chunks, metadata, and dependencies."""
    rel_path = os.path.relpath(file_path, repo_root).replace(os.sep, "/")
    stat = os.stat(file_path)
    mtime = stat.st_mtime

    with open(file_path, "r", encoding="utf-8") as f:
        full_content = f.read()

    frontmatter, content = parse_frontmatter(full_content)

    # Determine domain name
    dir_name = os.path.dirname(rel_path)
    if dir_name in ("", "."):
        domain = "root"
        parent = None
    else:
        domain = dir_name
        parts = domain.split("/")
        parent = parts[0] if len(parts) > 1 else "root"

    # Override domain if explicitly declared in frontmatter
    if "domain" in frontmatter and isinstance(frontmatter["domain"], str):
        domain = frontmatter["domain"].strip().strip("/")

    # Extract cross-domain dependencies
    depends_on = extract_dependencies(content, frontmatter, domain)

    # Extract top document title
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    doc_title = title_match.group(1).strip() if title_match else f"{domain} specification"

    # Split document by markdown level-2 headers
    sections = re.split(r"(?m)^(?=##\s+)", content)
    chunks: List[ContextChunk] = []

    # First section (preamble / intro)
    preamble = sections[0].strip() if sections else ""
    if preamble:
        summary = extract_summary(preamble)
        keywords = extract_keywords_from_markdown(preamble)
        tokens_est = max(1, len(preamble) // 4)
        chunks.append(
            ContextChunk(
                chunk_id=f"{domain}:overview",
                domain=domain,
                file_path=rel_path,
                section_title="Overview & Architecture",
                content=preamble,
                summary=summary,
                keywords=keywords,
                token_count=tokens_est,
                mtime=mtime,
            )
        )

    # Remaining sections
    for idx, sec in enumerate(sections[1:], start=1):
        sec = sec.strip()
        if not sec:
            continue
        first_line = sec.splitlines()[0]
        sec_title = re.sub(r"^##\s+", "", first_line).strip()
        summary = extract_summary(sec)
        keywords = extract_keywords_from_markdown(sec)
        tokens_est = max(1, len(sec) // 4)
        chunk_slug = re.sub(r"[^a-zA-Z0-9]+", "_", sec_title).strip("_").lower()
        chunk_id = f"{domain}:{chunk_slug or idx}"

        chunks.append(
            ContextChunk(
                chunk_id=chunk_id,
                domain=domain,
                file_path=rel_path,
                section_title=sec_title,
                content=sec,
                summary=summary,
                keywords=keywords,
                token_count=tokens_est,
                mtime=mtime,
            )
        )

    # Overall file summary
    file_summary = chunks[0].summary if chunks else ""
    all_keywords = sorted(list({kw for c in chunks for kw in c.keywords}))[:30]

    return {
        "domain": domain,
        "parent": parent,
        "path": rel_path,
        "title": doc_title,
        "summary": file_summary,
        "keywords": all_keywords,
        "depends_on": depends_on,
        "section_titles": [c.section_title for c in chunks],
        "chunks": chunks,
        "total_tokens_est": sum(c.token_count for c in chunks),
        "mtime": mtime,
    }


def scan_session_artifacts(
    work_dir: Optional[str] = None,
    repo_root: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Discover active ephemeral SDLC session artifacts:
    - intent.md (or docs/epics/ active epic)
    - spec.md (or docs/specs/ active spec)
    - plan.md (or docs/plans/ active in_progress plan)
    
    Returns structured descriptors including status, tasks, locks, and summaries.
    """
    root = os.path.abspath(repo_root or os.getcwd())
    target_dir = os.path.abspath(work_dir or root)

    artifacts: List[Dict[str, Any]] = []

    # 1. Check working directory / repo root for direct session files
    candidate_files = [
        ("plan", ["plan.md", "PLAN.md"]),
        ("spec", ["spec.md", "SPEC.md"]),
        ("intent", ["intent.md", "INTENT.md"]),
    ]

    found_kinds = set()

    for kind, filenames in candidate_files:
        for fname in filenames:
            # Check target work_dir first, then root
            paths_to_check = [os.path.join(target_dir, fname)]
            if target_dir != root:
                paths_to_check.append(os.path.join(root, fname))

            for path in paths_to_check:
                if os.path.isfile(path) and kind not in found_kinds:
                    found_kinds.add(kind)
                    stat = os.stat(path)
                    with open(path, "r", encoding="utf-8") as f:
                        text = f.read()

                    fm, body = parse_frontmatter(text)
                    rel_p = os.path.relpath(path, root).replace(os.sep, "/")

                    # Extract checkboxes/tasks
                    tasks = [
                        re.sub(r"^\s*-\s*\[([ xX])\]\s*", "", line).strip()
                        for line in body.splitlines()
                        if re.match(r"^\s*-\s*\[([ xX])\]", line)
                    ]

                    # Extract locked files if plan
                    locked_files = []
                    fm_locks = fm.get("locked_files", [])
                    if isinstance(fm_locks, list):
                        for item in fm_locks:
                            if isinstance(item, dict):
                                locked_files.append(item.get("path", ""))
                            elif isinstance(item, str):
                                locked_files.append(item)

                    title_match = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
                    title = title_match.group(1).strip() if title_match else f"Active {kind.capitalize()} Artifact"

                    artifacts.append(
                        {
                            "kind": kind,
                            "file_path": rel_p,
                            "title": title,
                            "status": fm.get("status", "in_progress" if kind == "plan" else "active"),
                            "locked_files": [lf for lf in locked_files if lf],
                            "tasks": tasks[:10],
                            "summary": extract_summary(body),
                            "estimated_tokens": max(1, len(text) // 4),
                            "mtime": stat.st_mtime,
                        }
                    )
                    break

    # 2. Also check docs/plans/ for active in_progress execution plans if plan.md not found in root
    if "plan" not in found_kinds:
        plan_pattern = os.path.join(root, "docs", "plans", "PLAN-*.md")
        for pfile in sorted(glob.glob(plan_pattern), reverse=True):
            try:
                with open(pfile, "r", encoding="utf-8") as f:
                    pcontent = f.read()
                pfm, pbody = parse_frontmatter(pcontent)
                if pfm.get("status") == "in_progress":
                    stat = os.stat(pfile)
                    rel_p = os.path.relpath(pfile, root).replace(os.sep, "/")
                    locked_files = []
                    fm_locks = pfm.get("locked_files", [])
                    if isinstance(fm_locks, list):
                        for item in fm_locks:
                            if isinstance(item, dict):
                                locked_files.append(item.get("path", ""))
                            elif isinstance(item, str):
                                locked_files.append(item)

                    tasks = [
                        re.sub(r"^\s*-\s*\[([ xX])\]\s*", "", line).strip()
                        for line in pbody.splitlines()
                        if re.match(r"^\s*-\s*\[([ xX])\]", line)
                    ]
                    title_match = re.search(r"^#\s+(.+)$", pbody, re.MULTILINE)
                    title = title_match.group(1).strip() if title_match else os.path.basename(pfile)

                    artifacts.append(
                        {
                            "kind": "plan",
                            "file_path": rel_p,
                            "title": title,
                            "status": "in_progress",
                            "locked_files": [lf for lf in locked_files if lf],
                            "tasks": tasks[:10],
                            "summary": extract_summary(pbody),
                            "estimated_tokens": max(1, len(pcontent) // 4),
                            "mtime": stat.st_mtime,
                        }
                    )
                    break
            except Exception:
                pass

    return artifacts


class RepositoryContextScanner:
    """Scans monorepo for AGENTS.md files, constructs topological map and chunks."""

    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)

    def scan(self) -> List[Dict[str, Any]]:
        """Find and parse all AGENTS.md files in the repository."""
        results = []
        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [
                d
                for d in dirs
                if d not in IGNORE_DIRS
                and not any(root.endswith(os.sep + ign) for ign in IGNORE_DIRS)
            ]

            if "AGENTS.md" in files:
                file_path = os.path.join(root, "AGENTS.md")
                parsed = parse_agents_file(file_path, self.repo_root)
                results.append(parsed)

        results.sort(key=lambda x: (0 if x["domain"] == "root" else 1, x["domain"]))
        return results

    def build_topological_map(self, scanned_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Construct machine-readable JSON structure for INDEX.json."""
        hierarchy: Dict[str, List[str]] = {}
        domains_map: Dict[str, Any] = {}

        for item in scanned_files:
            dom = item["domain"]
            parent = item["parent"] or "root"
            domains_map[dom] = {
                "domain": dom,
                "path": item["path"],
                "parent": item["parent"],
                "depends_on": item.get("depends_on", []),
                "title": item["title"],
                "summary": item["summary"],
                "keywords": item["keywords"],
                "sections": item["section_titles"],
                "estimated_tokens": item["total_tokens_est"],
            }
            if dom != "root":
                hierarchy.setdefault(parent, []).append(dom)

        return {
            "version": "1.1.0",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "total_domains": len(scanned_files),
            "domains": domains_map,
            "hierarchy": hierarchy,
        }

    def render_markdown_map(self, index_data: Dict[str, Any]) -> str:
        """Render a clean, human & agent-readable topological MAP.md."""
        domains = index_data["domains"]
        hierarchy = index_data["hierarchy"]

        lines = [
            "# Monorepo Context Topology Map (MAP.md)",
            "",
            "> **NOTICE:** This map is automatically generated by `packages/context-router`. "
            "It acts as a hierarchical topological index of all localized `AGENTS.md` context artifacts. "
            "Agents should consult this map or call `search_context(intent)` to retrieve exact localized rules "
            "without scanning the raw filesystem.",
            "",
            "## 1. Domain Hierarchy Tree",
            "",
            "```",
            "root (./AGENTS.md)",
        ]

        def render_tree(parent_key: str, indent: str = "├── "):
            subdomains = hierarchy.get(parent_key, [])
            for i, sub in enumerate(subdomains):
                is_last = i == len(subdomains) - 1
                branch = "└── " if is_last else "├── "
                next_indent = indent.replace("├── ", "│   ").replace("└── ", "    ")
                lines.append(f"{indent[:-4]}{branch}{sub} ({domains[sub]['path']})")
                if sub in hierarchy:
                    render_tree(sub, next_indent + "├── ")

        for top_group in sorted(list(hierarchy.keys())):
            if top_group != "root" and "/" not in top_group:
                lines.append(f"├── {top_group}/")
                render_tree(top_group, "│   ├── ")

        lines.extend([
            "```",
            "",
            "## 2. Domain Responsibility & Capabilities Catalog",
            "",
            "| Domain | Path | Dependencies | Core Responsibilities | Key Capabilities / Exports | Est. Tokens |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ])

        for dom_name, meta in domains.items():
            path_link = f"[`{meta['path']}`]({meta['path']})"
            deps_list = meta.get("depends_on", [])
            deps_str = ", ".join(f"`{d}`" for d in deps_list) if deps_list else "_none_"
            summary = meta["summary"].replace("|", "\\|")
            keywords_preview = ", ".join(f"`{k}`" for k in meta["keywords"][:5])
            lines.append(
                f"| **`{dom_name}`** | {path_link} | {deps_str} | {summary} | {keywords_preview} | ~{meta['estimated_tokens']} |"
            )

        lines.extend([
            "",
            "## 3. Agent Navigation & Routing Directives",
            "",
            "1. **Never Crawl the Filesystem:** When looking for business rules or coding conventions, do not list or open every directory.",
            "2. **Instant Hybrid Retrieval:** Use `search_context(intent=\"<task description>\")` via CLI (`make search-context INTENT=\"...\"`) or the MCP server.",
            "3. **Domain Boundary Invariants:**",
            "   - Code in `apps/*` may import from `packages/*`.",
            "   - Code in `packages/*` must **NEVER** import from `apps/*`.",
            "   - Package contracts are restricted to public exports.",
            "",
        ])

        return "\n".join(lines)

    def write_artifacts(self, scanned_files: List[Dict[str, Any]]) -> Dict[str, str]:
        """Generate and save INDEX.json and MAP.md at the repo root."""
        index_data = self.build_topological_map(scanned_files)
        map_md = self.render_markdown_map(index_data)

        index_json_path = os.path.join(self.repo_root, "INDEX.json")
        map_md_path = os.path.join(self.repo_root, "MAP.md")

        with open(index_json_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, indent=2)

        with open(map_md_path, "w", encoding="utf-8") as f:
            f.write(map_md)

        return {
            "index_json": index_json_path,
            "map_md": map_md_path,
        }
