import os
import unittest
import sys

# Ensure package paths are present
current_dir = os.path.dirname(os.path.abspath(__file__))
pkg_root = os.path.dirname(current_dir)
repo_root = os.path.dirname(os.path.dirname(pkg_root))

if pkg_root not in sys.path:
    sys.path.insert(0, pkg_root)

context_router_path = os.path.join(repo_root, "packages", "context-router")
if context_router_path not in sys.path:
    sys.path.insert(0, context_router_path)

from agent_evals.datasets import BENCHMARK_INTENTS, BenchmarkItem
from agent_evals.metrics import calculate_eval_metrics, EvalSummary
from agent_evals.benchmark import run_ab_benchmark
from agent_evals.gatekeeper import run_gatekeeper
from agent_evals.runner import render_markdown_report


class TestAgentEvals(unittest.TestCase):
    def setUp(self):
        self.repo_root = repo_root

    def test_benchmark_dataset_integrity(self):
        """Ensure benchmark intents cover all core monorepo domains."""
        self.assertGreaterEqual(len(BENCHMARK_INTENTS), 6)
        expected_domains = {item.expected_domain for item in BENCHMARK_INTENTS}
        self.assertIn("packages/auth", expected_domains)
        self.assertIn("packages/database", expected_domains)
        self.assertIn("apps/api-gateway", expected_domains)
        self.assertIn("packages/common", expected_domains)
        self.assertIn("root", expected_domains)

    def test_metrics_calculation_math(self):
        """Verify token reduction and accuracy metric calculations."""
        mock_records = [
            {
                "expected_domain": "packages/auth",
                "acceptable_domains": ["packages/auth"],
                "router": {
                    "primary_domain": "packages/auth",
                    "matched_domains": ["packages/auth", "packages/common"],
                    "context_tokens": 200,
                    "duration_ms": 5.0,
                },
                "raw": {
                    "context_tokens": 1000,
                    "duration_ms": 25.0,
                },
            },
            {
                "expected_domain": "packages/database",
                "acceptable_domains": ["packages/database"],
                "router": {
                    "primary_domain": "packages/database",
                    "matched_domains": ["packages/database"],
                    "context_tokens": 300,
                    "duration_ms": 6.0,
                },
                "raw": {
                    "context_tokens": 1100,
                    "duration_ms": 30.0,
                },
            },
        ]

        summary = calculate_eval_metrics(mock_records, accuracy_threshold=0.90)
        self.assertEqual(summary.total_queries, 2)
        self.assertEqual(summary.top1_accuracy_pct, 100.0)
        self.assertEqual(summary.top_k_accuracy_pct, 100.0)
        self.assertAlmostEqual(summary.avg_raw_tokens, 1050.0)
        self.assertAlmostEqual(summary.avg_router_tokens, 250.0)
        # Token reduction = (1050 - 250) / 1050 = 800 / 1050 = 76.19%
        self.assertGreater(summary.token_reduction_rate_pct, 70.0)
        self.assertGreater(summary.latency_speedup_factor, 1.0)
        self.assertTrue(summary.passed_threshold)

    def test_full_ab_benchmark_execution(self):
        """Verify the full A/B benchmark runs and meets performance thresholds."""
        subset = BENCHMARK_INTENTS[:3]
        result = run_ab_benchmark(repo_root=self.repo_root, items=subset, accuracy_threshold=0.90)

        self.assertEqual(len(result.records), 3)
        self.assertGreaterEqual(result.summary.top1_accuracy_pct, 90.0)
        self.assertGreater(result.summary.token_reduction_rate_pct, 50.0)
        self.assertGreater(result.summary.dollars_saved_per_1k_queries, 0.0)
        self.assertGreater(result.summary.hours_saved_per_sprint, 0.0)

        report = render_markdown_report(result)
        self.assertIn("# AI Context Router A/B Performance Evaluation Report", report)
        self.assertIn("Token Reduction Rate", report)

    def test_gatekeeper_pass(self):
        """Verify the CI/Pre-commit gatekeeper passes on the current repository state."""
        exit_code = run_gatekeeper(repo_root=self.repo_root, threshold=0.90)
        self.assertEqual(exit_code, 0)


if __name__ == "__main__":
    unittest.main()
