import unittest
from context_router.mcp_server import MCPServer


class TestMCPServer(unittest.TestCase):
    def setUp(self):
        self.server = MCPServer()

    def test_initialize(self):
        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {},
        }
        resp = self.server.handle_request(req)
        self.assertEqual(resp["id"], 1)
        self.assertEqual(resp["result"]["serverInfo"]["name"], "context-router")
        self.assertIn("tools", resp["result"]["capabilities"])

    def test_tools_list(self):
        req = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        resp = self.server.handle_request(req)
        tools = resp["result"]["tools"]
        tool_names = [t["name"] for t in tools]
        self.assertIn("search_context", tool_names)
        self.assertIn("get_topological_map", tool_names)
        self.assertIn("get_domain_context", tool_names)

    def test_tools_call_search(self):
        req = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "search_context",
                "arguments": {
                    "intent": "Implement auth middleware",
                    "top_k": 2,
                },
            },
        }
        resp = self.server.handle_request(req)
        self.assertEqual(resp["id"], 3)
        content = resp["result"]["content"]
        self.assertEqual(content[0]["type"], "text")
        self.assertIn("packages/auth", content[0]["text"])

    def test_tools_call_get_map(self):
        req = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "get_topological_map",
                "arguments": {},
            },
        }
        resp = self.server.handle_request(req)
        content = resp["result"]["content"]
        self.assertIn("Monorepo Context Topology Map", content[0]["text"])


if __name__ == "__main__":
    unittest.main()
