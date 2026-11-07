import os
import unittest
import tempfile
import shutil
from context_router.engine import ContextSearchEngine


class TestContextSearchEngine(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_context.db")
        self.engine = ContextSearchEngine(repo_root=self.repo_root, db_path=self.db_path)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_build_index_and_search(self):
        # Index the repository
        res = self.engine.build_index()
        self.assertEqual(res["status"], "success")
        self.assertGreater(res["domains_indexed"], 0)
        self.assertGreater(res["chunks_indexed"], 0)

        # Test searching for "Implement auth middleware"
        search_res = self.engine.search("Implement auth middleware", top_k=3)
        self.assertEqual(search_res["primary_domain"], "packages/auth")
        self.assertGreater(len(search_res["results"]), 0)

        top_match = search_res["results"][0]
        self.assertEqual(top_match["domain"], "packages/auth")
        self.assertGreater(top_match["score"], 0.3)
        self.assertIn("packages/auth/AGENTS.md", top_match["file_path"])

    def test_database_search(self):
        self.engine.build_index()
        search_res = self.engine.search("PostgreSQL connection pool and transactions", top_k=3)
        self.assertEqual(search_res["primary_domain"], "packages/database")
        self.assertIn("packages/database/AGENTS.md", search_res["results"][0]["file_path"])

    def test_domain_filtering(self):
        self.engine.build_index()
        search_res = self.engine.search("tokens", top_k=5, domain_filter="packages/auth")
        for match in search_res["results"]:
            self.assertEqual(match["domain"], "packages/auth")


if __name__ == "__main__":
    unittest.main()
