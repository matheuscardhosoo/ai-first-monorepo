"""
Predefined Benchmark Intents and Ground Truth Datasets for AI Context Retrieval.
"""

from typing import List, Dict, Any


class BenchmarkItem:
    def __init__(
        self,
        item_id: str,
        intent: str,
        expected_domain: str,
        acceptable_domains: List[str],
        category: str,
        description: str,
    ):
        self.item_id = item_id
        self.intent = intent
        self.expected_domain = expected_domain
        self.acceptable_domains = acceptable_domains
        self.category = category
        self.description = description

    def to_dict(self) -> Dict[str, Any]:
        return {
            "item_id": self.item_id,
            "intent": self.intent,
            "expected_domain": self.expected_domain,
            "acceptable_domains": self.acceptable_domains,
            "category": self.category,
            "description": self.description,
        }


BENCHMARK_INTENTS: List[BenchmarkItem] = [
    BenchmarkItem(
        item_id="INTENT-001",
        intent="Where is the auth middleware?",
        expected_domain="packages/auth",
        acceptable_domains=["packages/auth", "apps/api-gateway"],
        category="Security & Auth",
        description="Verify token signing, JWT verification, and auth middleware contract.",
    ),
    BenchmarkItem(
        item_id="INTENT-002",
        intent="How to configure PostgreSQL connection pool and transactions?",
        expected_domain="packages/database",
        acceptable_domains=["packages/database"],
        category="Persistence",
        description="Verify database client pool, schema migrations, and transaction manager.",
    ),
    BenchmarkItem(
        item_id="INTENT-003",
        intent="Where are the API Gateway routing rules and rate limiting?",
        expected_domain="apps/api-gateway",
        acceptable_domains=["apps/api-gateway"],
        category="API Ingress",
        description="Verify public HTTP ingress, reverse proxying, and middleware pipeline execution.",
    ),
    BenchmarkItem(
        item_id="INTENT-004",
        intent="Frontend client state management and WCAG accessibility guidelines",
        expected_domain="apps/web",
        acceptable_domains=["apps/web"],
        category="Frontend UI",
        description="Verify web client components, cookie token storage, and accessibility rules.",
    ),
    BenchmarkItem(
        item_id="INTENT-005",
        intent="Shared error classes, AppError hierarchy, and correlation ID logger",
        expected_domain="packages/common",
        acceptable_domains=["packages/common"],
        category="Shared Primitives",
        description="Verify foundational logging, error primitives, and utility contracts.",
    ),
    BenchmarkItem(
        item_id="INTENT-006",
        intent="Topological monorepo context indexing and hybrid vector search",
        expected_domain="packages/context-router",
        acceptable_domains=["packages/context-router"],
        category="Context Routing",
        description="Verify context scanner, embeddings, and hybrid retrieval engine.",
    ),
    BenchmarkItem(
        item_id="INTENT-007",
        intent="Dual-grilling SDLC state machine, Moment 1 PO gate, and multi-agent file locks",
        expected_domain="root",
        acceptable_domains=["root"],
        category="Governance & SDLC",
        description="Verify core architectural invariants, SDLC approval moments, and file lock engine.",
    ),
    BenchmarkItem(
        item_id="INTENT-008",
        intent="A/B performance benchmarking, token reduction rate, and retrieval accuracy eval gate",
        expected_domain="packages/agent-evals",
        acceptable_domains=["packages/agent-evals"],
        category="Quality & Evaluation",
        description="Verify evaluation harness, metric calculation, and pre-commit gatekeeper.",
    ),
]
