"""
Command Line Interface for Context Router.
Provides commands for indexing, searching, syncing, watching, and inspecting topological maps.
"""

import sys
import os
import argparse
import json
from typing import Optional

# Ensure package can be run directly as a script
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from context_router.api import (
    search_context,
    get_topological_map,
    get_domain_context,
    build_index,
    sync_index,
    get_active_session_artifacts,
)
from context_router.watcher import ContextFileWatcher


def main(args: Optional[list] = None):
    parser = argparse.ArgumentParser(
        prog="context-router",
        description="Optimized Discovery and Retrieval Routing Layer for Distributed AGENTS.md files",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: index
    index_parser = subparsers.add_parser("index", help="Scan repository and build complete index artifacts")
    index_parser.add_argument("--root", type=str, default=None, help="Repository root path")

    # Command: sync
    sync_parser = subparsers.add_parser("sync", help="Granularly re-index only modified AGENTS.md files")
    sync_parser.add_argument("--root", type=str, default=None, help="Repository root path")
    sync_parser.add_argument("--force", action="store_true", help="Force complete re-index")

    # Command: watch
    watch_parser = subparsers.add_parser("watch", help="Watch for AGENTS.md modifications and auto-reindex")
    watch_parser.add_argument("--root", type=str, default=None, help="Repository root path")
    watch_parser.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds")

    # Command: search
    search_parser = subparsers.add_parser("search", help="Execute hybrid search against AGENTS.md context")
    search_parser.add_argument("intent", type=str, help="Task description or search intent")
    search_parser.add_argument("--top-k", type=int, default=3, help="Number of results to retrieve (default: 3)")
    search_parser.add_argument("--domain", type=str, default=None, help="Filter by specific domain")
    search_parser.add_argument("--no-session", action="store_true", help="Do not include active ephemeral session artifacts")
    search_parser.add_argument("--json", action="store_true", help="Output raw JSON instead of markdown synthesis")
    search_parser.add_argument("--root", type=str, default=None, help="Repository root path")

    # Command: session
    session_parser = subparsers.add_parser("session", help="Inspect active ephemeral SDLC session artifacts")
    session_parser.add_argument("--root", type=str, default=None, help="Repository root path")

    # Command: map
    map_parser = subparsers.add_parser("map", help="Display the topological domain map (MAP.md)")
    map_parser.add_argument("--root", type=str, default=None, help="Repository root path")

    # Command: get
    get_parser = subparsers.add_parser("get", help="Retrieve raw AGENTS.md for a given domain")
    get_parser.add_argument("domain", type=str, help="Domain name, e.g. packages/auth or root")
    get_parser.add_argument("--root", type=str, default=None, help="Repository root path")

    parsed = parser.parse_args(args)

    if not parsed.command:
        parser.print_help()
        sys.exit(1)

    if parsed.command == "index":
        print("Scanning repository and rebuilding context index...")
        res = build_index(repo_root=parsed.root)
        print(f"Indexed {res['domains_indexed']} domains and {res['chunks_indexed']} sections in {res['duration_ms']}ms.")
        print(f"Topological artifacts created:\n  - {res['artifacts_generated']['index_json']}\n  - {res['artifacts_generated']['map_md']}")

    elif parsed.command == "sync":
        res = sync_index(repo_root=parsed.root, force=parsed.force)
        if res.get("status") == "up_to_date":
            print(f"Index is already up to date ({res.get('checked_domains', 0)} domains checked in {res.get('duration_ms')}ms).")
        else:
            print(f"Sync complete in {res.get('duration_ms')}ms. Modified: {res.get('modified_domains', [])}, Added: {res.get('added_domains', [])}")

    elif parsed.command == "watch":
        watcher = ContextFileWatcher(repo_root=parsed.root, poll_interval=parsed.interval)
        watcher.run()

    elif parsed.command == "search":
        res = search_context(
            intent=parsed.intent,
            top_k=parsed.top_k,
            domain_filter=parsed.domain,
            repo_root=parsed.root,
            include_session=not parsed.no_session,
        )
        if parsed.json:
            print(json.dumps(res, indent=2))
        else:
            print(res["synthesized_context"])
            print(f"\n[Retrieval completed in {res['duration_ms']}ms]")

    elif parsed.command == "session":
        artifacts = get_active_session_artifacts(repo_root=parsed.root)
        if not artifacts:
            print("No active ephemeral SDLC session artifacts found (plan.md, spec.md, intent.md).")
        else:
            print(f"Found {len(artifacts)} active session artifacts:")
            for a in artifacts:
                print(f"- [{a['kind'].upper()}] {a['title']} ({a['file_path']}) | Status: {a['status']}")
                if a.get("locked_files"):
                    print(f"    Locked files: {', '.join(a['locked_files'])}")

    elif parsed.command == "map":
        content = get_topological_map(repo_root=parsed.root)
        print(content)

    elif parsed.command == "get":
        try:
            content = get_domain_context(domain=parsed.domain, repo_root=parsed.root)
            print(content)
        except FileNotFoundError as err:
            print(f"Error: {err}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
