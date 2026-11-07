#!/usr/bin/env python3
"""
Model Context Protocol (MCP) Server for Context Router.
Communicates via standard I/O (stdio) using JSON-RPC 2.0 to provide
autonomous agents with context discovery tools, active SDLC session inspection,
and on-demand cache reindexing.
"""

import sys
import os
import json
from typing import Dict, Any, Optional

# Ensure package root is in sys.path
package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if package_root not in sys.path:
    sys.path.insert(0, package_root)

from context_router.api import (
    search_context,
    get_topological_map,
    get_domain_context,
    build_index,
    sync_index,
    get_active_session_artifacts,
)

PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "context-router"
SERVER_VERSION = "1.1.0"


def create_jsonrpc_response(req_id: Any, result: Any) -> Dict[str, Any]:
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def create_jsonrpc_error(req_id: Any, code: int, message: str, data: Any = None) -> Dict[str, Any]:
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": req_id, "error": err}


class MCPServer:
    """Stdio-based JSON-RPC 2.0 Model Context Protocol Server."""

    def __init__(self):
        self.tools = [
            {
                "name": "search_context",
                "description": (
                    "Optimized discovery tool: Search distributed AGENTS.md context artifacts across the monorepo "
                    "using hybrid semantic similarity and FTS5 full-text search. Unconditionally pins Root Governance rules, "
                    "auto-resolves cross-domain dependencies, and injects active SDLC task plan/spec artifacts."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "intent": {
                            "type": "string",
                            "description": "Developer intent or task description (e.g. 'Implement auth middleware', 'Postgres connection pool')",
                        },
                        "top_k": {
                            "type": "integer",
                            "description": "Number of top relevant sections to return (default: 3)",
                            "default": 3,
                        },
                        "domain": {
                            "type": "string",
                            "description": "Optional domain filter (e.g. 'packages/auth', 'apps/api-gateway')",
                        },
                        "include_session": {
                            "type": "boolean",
                            "description": "Whether to track and include active ephemeral session artifacts (plan.md, spec.md, intent.md)",
                            "default": True,
                        },
                    },
                    "required": ["intent"],
                },
            },
            {
                "name": "get_active_session",
                "description": (
                    "Inspect active ephemeral SDLC session artifacts (intent.md, spec.md, plan.md, and active "
                    "in_progress plans in docs/plans/) to retrieve current task goals, steps, and acquired file locks."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_topological_map",
                "description": (
                    "Retrieve the monorepo topological context map (MAP.md), providing an ASCII hierarchy tree, "
                    "cross-domain dependencies, and domain responsibility matrix across all branches."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_domain_context",
                "description": "Retrieve the raw localized AGENTS.md specification for a specified domain.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "description": "Domain path identifier (e.g. 'packages/auth', 'packages/database', 'root')",
                        }
                    },
                    "required": ["domain"],
                },
            },
            {
                "name": "sync_context",
                "description": "Granularly re-index only modified, added, or deleted AGENTS.md files in SQLite and INDEX.json in <10ms.",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "force": {
                            "type": "boolean",
                            "description": "Force full re-index of all domains",
                            "default": False,
                        }
                    },
                },
            },
            {
                "name": "reindex_context",
                "description": "Force a complete re-scan and full rebuild of INDEX.json, MAP.md, and vector database.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
        ]

    def handle_request(self, req: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        method = req.get("method")
        req_id = req.get("id")
        params = req.get("params", {})

        if req_id is None:
            return None

        if method == "initialize":
            return create_jsonrpc_response(
                req_id,
                {
                    "protocolVersion": PROTOCOL_VERSION,
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION,
                    },
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                    },
                },
            )

        elif method == "tools/list":
            return create_jsonrpc_response(req_id, {"tools": self.tools})

        elif method == "tools/call":
            tool_name = params.get("name")
            args = params.get("arguments", {})

            try:
                if tool_name == "search_context":
                    intent = args.get("intent", "")
                    top_k = int(args.get("top_k", 3))
                    domain = args.get("domain")
                    include_session = bool(args.get("include_session", True))
                    res = search_context(
                        intent=intent,
                        top_k=top_k,
                        domain_filter=domain,
                        include_session=include_session,
                    )
                    return create_jsonrpc_response(
                        req_id,
                        {
                            "content": [
                                {
                                    "type": "text",
                                    "text": res["synthesized_context"],
                                }
                            ]
                        },
                    )

                elif tool_name == "get_active_session":
                    artifacts = get_active_session_artifacts()
                    return create_jsonrpc_response(
                        req_id,
                        {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(artifacts, indent=2),
                                }
                            ]
                        },
                    )

                elif tool_name == "get_topological_map":
                    content = get_topological_map()
                    return create_jsonrpc_response(
                        req_id,
                        {
                            "content": [
                                {
                                    "type": "text",
                                    "text": content,
                                }
                            ]
                        },
                    )

                elif tool_name == "get_domain_context":
                    domain = args.get("domain", "")
                    content = get_domain_context(domain=domain)
                    return create_jsonrpc_response(
                        req_id,
                        {
                            "content": [
                                {
                                    "type": "text",
                                    "text": content,
                                }
                            ]
                        },
                    )

                elif tool_name == "sync_context":
                    force = bool(args.get("force", False))
                    res = sync_index(force=force)
                    return create_jsonrpc_response(
                        req_id,
                        {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Index sync status: {res.get('status')} in {res.get('duration_ms', 0)}ms.",
                                }
                            ]
                        },
                    )

                elif tool_name == "reindex_context":
                    res = build_index()
                    return create_jsonrpc_response(
                        req_id,
                        {
                            "content": [
                                {
                                    "type": "text",
                                    "text": f"Context completely reindexed in {res['duration_ms']}ms. Total domains: {res['domains_indexed']}, sections: {res['chunks_indexed']}.",
                                }
                            ]
                        },
                    )

                else:
                    return create_jsonrpc_error(req_id, -32601, f"Unknown tool: '{tool_name}'")

            except Exception as err:
                return create_jsonrpc_response(
                    req_id,
                    {
                        "content": [
                            {
                                "type": "text",
                                "text": f"Error executing tool '{tool_name}': {str(err)}",
                            }
                        ],
                        "isError": True,
                    },
                )

        elif method == "resources/list":
            return create_jsonrpc_response(
                req_id,
                {
                    "resources": [
                        {
                            "uri": "context://map",
                            "name": "Monorepo Context Topological Map",
                            "mimeType": "text/markdown",
                        },
                        {
                            "uri": "context://index",
                            "name": "Machine Readable Context Index",
                            "mimeType": "application/json",
                        },
                    ]
                },
            )

        elif method == "resources/read":
            uri = params.get("uri")
            if uri == "context://map":
                return create_jsonrpc_response(
                    req_id,
                    {
                        "contents": [
                            {
                                "uri": "context://map",
                                "mimeType": "text/markdown",
                                "text": get_topological_map(),
                            }
                        ]
                    },
                )
            elif uri == "context://index":
                root = os.getcwd()
                idx_path = os.path.join(root, "INDEX.json")
                if os.path.exists(idx_path):
                    with open(idx_path, "r", encoding="utf-8") as f:
                        text = f.read()
                else:
                    text = "{}"
                return create_jsonrpc_response(
                    req_id,
                    {
                        "contents": [
                            {
                                "uri": "context://index",
                                "mimeType": "application/json",
                                "text": text,
                            }
                        ]
                    },
                )
            else:
                return create_jsonrpc_error(req_id, -32602, f"Resource not found: '{uri}'")

        else:
            return create_jsonrpc_error(req_id, -32601, f"Method not found: '{method}'")

    def run(self):
        """Main stdio loop reading JSON-RPC lines from stdin."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                req = json.loads(line)
                resp = self.handle_request(req)
                if resp is not None:
                    sys.stdout.write(json.dumps(resp) + "\n")
                    sys.stdout.flush()
            except json.JSONDecodeError:
                err = create_jsonrpc_error(None, -32700, "Parse error")
                sys.stdout.write(json.dumps(err) + "\n")
                sys.stdout.flush()


def main():
    server = MCPServer()
    server.run()


if __name__ == "__main__":
    main()
