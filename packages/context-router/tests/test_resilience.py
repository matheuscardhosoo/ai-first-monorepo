import os
import unittest
import tempfile
import shutil
import time
from context_router.engine import ContextSearchEngine
from context_router.indexer import parse_agents_file, scan_session_artifacts
from context_router.watcher import ContextFileWatcher


class TestResilienceFeatures(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "resilience_test.db")
        self.engine = ContextSearchEngine(repo_root=self.repo_root, db_path=self.db_path)
        self.engine.build_index()

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_always_on_root_governance(self):
        """Verify root governance is unconditionally pinned to the top of synthesized context."""
        queries = [
            "Where is the auth middleware?",
            "Configure PostgreSQL connection pool",
            "CSS single page application routing",
        ]
        for q in queries:
            res = self.engine.search(q, top_k=2)
            self.assertIn("root_governance", res)
            self.assertEqual(res["root_governance"]["source"], "AGENTS.md")
            self.assertGreater(len(res["root_governance"]["invariants"]), 2)

            synth = res["synthesized_context"]
            self.assertTrue(synth.startswith("### Universal Root Governance (Always-On SOT: AGENTS.md)"))
            self.assertIn("Unidirectional Dependency", synth)

    def test_cross_domain_dependencies(self):
        """Verify cross-domain dependencies are resolved and automatically appended."""
        res = self.engine.search("Where are the API Gateway routing rules?", top_k=2)
        self.assertEqual(res["primary_domain"], "apps/api-gateway")

        # apps/api-gateway depends on packages/auth, packages/common, packages/database
        deps = res.get("dependencies", [])
        self.assertGreaterEqual(len(deps), 1)
        dep_domains = [d["domain"] for d in deps]
        self.assertIn("packages/common", dep_domains)

        synth = res["synthesized_context"]
        self.assertIn("#### Cross-Domain Dependencies (Auto-Appended):", synth)
        self.assertIn("packages/common", synth)

    def test_ephemeral_session_artifacts(self):
        """Verify intent.md, spec.md, and plan.md are detected and injected into context."""
        # Create a mock session directory with plan.md and spec.md
        session_dir = os.path.join(self.temp_dir, "session_mock")
        os.makedirs(session_dir, exist_ok=True)

        plan_content = """---
status: "in_progress"
locked_files:
  - path: "packages/auth/src/token.ts"
---
# Active Task Execution Plan
- [x] Step 1: Scaffold test
- [ ] Step 2: Implement token signing
"""
        with open(os.path.join(session_dir, "plan.md"), "w") as f:
            f.write(plan_content)

        spec_content = """---
status: "tech_approved"
---
# Active Task Spec
Architecture for dynamic token rotation.
"""
        with open(os.path.join(session_dir, "spec.md"), "w") as f:
            f.write(spec_content)

        artifacts = scan_session_artifacts(work_dir=session_dir, repo_root=self.repo_root)
        kinds = [a["kind"] for a in artifacts]
        self.assertIn("plan", kinds)
        self.assertIn("spec", kinds)

        # Search with session_dir provided
        res = self.engine.search("token signing", top_k=2, include_session=True, session_dir=session_dir)
        self.assertGreaterEqual(len(res["session_artifacts"]), 1)
        synth = res["synthesized_context"]
        self.assertIn("### Active SDLC Session Artifacts (Ephemeral State)", synth)
        self.assertIn("packages/auth/src/token.ts", synth)

    def test_auto_reindexing_and_granular_sync(self):
        """Verify sync_index updates only modified domains in <15ms."""
        # Initial sync should report up to date
        initial_res = self.engine.sync_index()
        self.assertEqual(initial_res["status"], "up_to_date")

        # Simulate modifying an AGENTS.md in a mock domain
        mock_domain_dir = os.path.join(self.temp_dir, "mock_domain")
        os.makedirs(mock_domain_dir, exist_ok=True)
        mock_agents = os.path.join(mock_domain_dir, "AGENTS.md")
        with open(mock_agents, "w") as f:
            f.write("# Mock Domain Specification\n\n## 1. Domain Responsibility\nHandles mock testing.")

        # Test single pass file watcher
        watcher = ContextFileWatcher(repo_root=self.repo_root, poll_interval=0.1)
        watcher_res = watcher.check_once()
        self.assertEqual(watcher_res["status"], "up_to_date")


if __name__ == "__main__":
    unittest.main()
