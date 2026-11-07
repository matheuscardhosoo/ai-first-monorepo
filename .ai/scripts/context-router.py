#!/usr/bin/env python3
"""
Convenience CLI launcher for Context Router.
Usage:
  python3 .ai/scripts/context-router.py search "Implement auth middleware"
  python3 .ai/scripts/context-router.py index
  python3 .ai/scripts/context-router.py map
"""

import sys
import os

repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
pkg_dir = os.path.join(repo_root, "packages", "context-router")
if pkg_dir not in sys.path:
    sys.path.insert(0, pkg_dir)

from context_router.cli import main

if __name__ == "__main__":
    main()
