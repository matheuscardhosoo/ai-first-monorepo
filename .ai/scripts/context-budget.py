#!/usr/bin/env python3
"""
Context Budget & Token Estimator for AI-First Monorepo.
Measures characters, estimated tokens (~4 chars/token), and provides budget alerts.
"""
import os
import sys
import glob

if len(sys.argv) < 2:
    print("Usage: context-budget.py <directory-or-domain>")
    sys.exit(1)

domain = sys.argv[1]
if not os.path.exists(domain):
    print(f"Error: Path '{domain}' does not exist.")
    sys.exit(1)

ignored_patterns = [".git", "node_modules", "target", "dist", "__pycache__", ".turbo", ".cache"]
files = [
    f for f in glob.glob(f"{domain}/**/*", recursive=True)
    if os.path.isfile(f) and not any(p in f for p in ignored_patterns)
]

total_chars = sum(os.path.getsize(f) for f in files)
est_tokens = total_chars // 4

print(f"Context Budget Analysis for: {domain}")
print(f"  Total Files:        {len(files)}")
print(f"  Total Characters:   {total_chars:,}")
print(f"  Estimated Tokens:   ~{est_tokens:,} tokens")

if est_tokens > 25000:
    print("  [!] WARNING: Context exceeds 25,000 tokens! Recommend narrowing domain scope or pruning before LLM input.")
elif est_tokens > 10000:
    print("  [*] MODERATE: Fits within standard context, but recommend relying on prompt caching or sub-domain focus.")
else:
    print("  [+] OPTIMAL: Lean context (<10k tokens). High prompt cache hit rate and minimal token inference cost.")
