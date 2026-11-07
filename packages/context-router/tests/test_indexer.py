import os
import unittest
from context_router.indexer import (
    RepositoryContextScanner,
    parse_agents_file,
    extract_keywords_from_markdown,
    extract_summary,
)


class TestIndexer(unittest.TestCase):
    def setUp(self):
        self.repo_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

    def test_extract_keywords(self):
        text = "This module implements `verifyToken(token)` and uses **Argon2id** password hashing."
        keywords = extract_keywords_from_markdown(text)
        self.assertIn("verifyToken", keywords)
        self.assertIn("Argon2id", keywords)

    def test_extract_summary(self):
        text = "# Title\n\nThis is the first sentence. This is the second sentence."
        summary = extract_summary(text)
        self.assertTrue(summary.startswith("This is the first sentence"))

    def test_parse_agents_file(self):
        auth_agents = os.path.join(self.repo_root, "packages", "auth", "AGENTS.md")
        parsed = parse_agents_file(auth_agents, self.repo_root)
        self.assertEqual(parsed["domain"], "packages/auth")
        self.assertEqual(parsed["parent"], "packages")
        self.assertGreater(len(parsed["chunks"]), 1)
        self.assertTrue(any("Public API Contract" in s for s in parsed["section_titles"]))

    def test_scanner_topological_map(self):
        scanner = RepositoryContextScanner(self.repo_root)
        scanned = scanner.scan()
        domains = [item["domain"] for item in scanned]
        self.assertIn("root", domains)
        self.assertIn("packages/auth", domains)

        topo_map = scanner.build_topological_map(scanned)
        self.assertIn("root", topo_map["domains"])
        self.assertIn("packages/auth", topo_map["domains"])
        self.assertIn("packages", topo_map["hierarchy"])

        md_map = scanner.render_markdown_map(topo_map)
        self.assertIn("Monorepo Context Topology Map", md_map)
        self.assertIn("packages/auth", md_map)


if __name__ == "__main__":
    unittest.main()
