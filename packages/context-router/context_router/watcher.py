"""
Lightweight File Watcher for Automated AGENTS.md Re-Indexing.
Monitors the repository for changes, additions, or deletions of AGENTS.md files
and triggers granular updates of SQLite vector DB and INDEX.json/MAP.md in <10ms.
Zero external library dependencies (uses Python standard library).
"""

import os
import sys
import time
import signal
from typing import Dict, Any, Optional, Callable, List, Tuple

from .engine import ContextSearchEngine
from .indexer import IGNORE_DIRS


class ContextFileWatcher:
    """Zero-dependency polling file watcher for distributed context artifacts."""

    def __init__(
        self,
        repo_root: Optional[str] = None,
        poll_interval: float = 1.0,
        on_change_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        from .api import _find_repo_root
        self.repo_root = os.path.abspath(repo_root or _find_repo_root())
        self.poll_interval = poll_interval
        self.on_change = on_change_callback
        self.engine = ContextSearchEngine(repo_root=self.repo_root)
        self.running = False
        self._mtime_cache: Dict[str, float] = {}

    def _discover_agents_files(self) -> Dict[str, float]:
        """Scan directory tree for AGENTS.md files and capture modification times."""
        files_map: Dict[str, float] = {}
        for root, dirs, files in os.walk(self.repo_root):
            dirs[:] = [
                d
                for d in dirs
                if d not in IGNORE_DIRS
                and not any(root.endswith(os.sep + ign) for ign in IGNORE_DIRS)
            ]
            if "AGENTS.md" in files:
                fpath = os.path.join(root, "AGENTS.md")
                try:
                    files_map[fpath] = os.stat(fpath).st_mtime
                except OSError:
                    pass
        return files_map

    def check_once(self) -> Dict[str, Any]:
        """Perform a single pass check and trigger granular reindex if changes exist."""
        current_files = self._discover_agents_files()

        if not self._mtime_cache:
            self._mtime_cache = current_files
            # Ensure engine is up to date initially
            return self.engine.sync_index()

        changed = False
        if set(current_files.keys()) != set(self._mtime_cache.keys()):
            changed = True
        else:
            for p, mtime in current_files.items():
                if abs(mtime - self._mtime_cache.get(p, 0.0)) > 0.001:
                    changed = True
                    break

        if changed:
            self._mtime_cache = current_files
            res = self.engine.sync_index()
            if self.on_change:
                self.on_change(res)
            return res

        return {"status": "up_to_date"}

    def run(self):
        """Start foreground polling loop until SIGINT/SIGTERM."""
        self.running = True

        def handle_stop(signum, frame):
            print("\n[watcher] Stopping Context File Watcher...")
            self.running = False

        signal.signal(signal.SIGINT, handle_stop)
        signal.signal(signal.SIGTERM, handle_stop)

        print(f"[watcher] Starting Context File Watcher on '{self.repo_root}' (poll interval: {self.poll_interval}s)...")
        initial_sync = self.check_once()
        print(f"[watcher] Initial state verified ({initial_sync.get('status')}). Monitoring for AGENTS.md modifications...")

        try:
            while self.running:
                time.sleep(self.poll_interval)
                res = self.check_once()
                if res.get("status") == "updated":
                    mods = res.get("modified_domains", [])
                    adds = res.get("added_domains", [])
                    rems = res.get("removed_domains", [])
                    duration = res.get("duration_ms", 0.0)
                    summary = []
                    if mods:
                        summary.append(f"modified: {', '.join(mods)}")
                    if adds:
                        summary.append(f"added: {', '.join(adds)}")
                    if rems:
                        summary.append(f"removed: {', '.join(rems)}")

                    print(f"[{time.strftime('%H:%M:%S')}] [watcher] Granular reindex completed in {duration}ms ({'; '.join(summary)})")
        except KeyboardInterrupt:
            pass
        finally:
            self.running = False
            print("[watcher] File watcher terminated.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Context Router File Watcher Daemon")
    parser.add_argument("--root", type=str, default=None, help="Monorepo root path")
    parser.add_argument("--interval", type=float, default=1.0, help="Polling interval in seconds")
    parser.add_argument("--once", action="store_true", help="Run a single check and exit")

    args = parser.parse_args()
    watcher = ContextFileWatcher(repo_root=args.root, poll_interval=args.interval)

    if args.once:
        res = watcher.check_once()
        print(f"Check completed: {res}")
    else:
        watcher.run()


if __name__ == "__main__":
    main()
