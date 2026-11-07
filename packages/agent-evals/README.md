# Agent Evals (`packages/agent-evals`)

Standalone, decoupled evaluation and A/B benchmarking module for the AI-First Monorepo Context Router.

Based on industry methodologies from:
- [AI in the SDLC: Developer Productivity and Time Savings (Google Cloud)](https://cloud.google.com)
- [The AI-Native SDLC Playbook (Anthropic Claude)](https://claude.com/resources/articles/the-ai-native-sdlc-playbook)

---

## 1. Architectural Purpose & Decoupling

In an autonomous multi-agent monorepo, AI software engineers need to discover localized domain rules (`AGENTS.md`) without:
1. Crawling the raw filesystem (consuming thousands of tokens and multiple tool turns).
2. Losing track of global invariants (Root Governance).
3. Missing implicit cross-domain contracts (Dependencies).

`packages/agent-evals` exists to continuously measure, evaluate, and gate the context routing layer. It is **completely decoupled** from production applications (`apps/*`) and shared domain logic (`packages/*`), ensuring that benchmark infrastructure never pollutes production runtimes or deployment artifacts.

```
                    ┌───────────────────────────────┐
                    │  Developer / Agent Intent     │
                    └───────────────┬───────────────┘
                                    │
               ┌────────────────────┴────────────────────┐
               ▼                                         ▼
   [Path A: Naive Traversal]                 [Path B: Hybrid Router]
   - Recursive directory scan                - Sub-5ms SQLite FTS5 + Dense Vector
   - Regex grep over all files               - Always-on Root Governance
   - Context window explosion (~4.2k tok)     - Auto-appended Dependencies
   - Multi-turn tool flailing                - Lean synthesized prompt (~1.1k tok)
               │                                         │
               └────────────────────┬────────────────────┘
                                    │
                                    ▼
                      ┌───────────────────────────┐
                      │    packages/agent-evals   │
                      │  - Token Reduction Rate   │
                      │  - First-Pass Accuracy    │
                      │  - Latency / Speedup      │
                      │  - Time / Dollar Savings  │
                      │  - Git Pre-commit Gate    │
                      └───────────────────────────┘
```

---

## 2. Tracked Metrics & Methodologies

The evaluation harness measures and outputs four core metrics:

### 2.1 First-Pass Retrieval Accuracy (%)
Measures whether the top-1 primary recommended domain matches the ground-truth domain for a given intent:

$$\text{Accuracy}_{\text{Top-1}} = \frac{\sum_{i=1}^N \mathbb{I}(\text{PrimaryDomain}_i = \text{ExpectedDomain}_i)}{N} \times 100\%$$

- **Top-K Accuracy:** Checks whether the expected domain was present anywhere in the top-K candidate results or acceptable dependency domains.

### 2.2 Token Reduction Rate (%)
Measures the prompt context size efficiency achieved by the router over raw directory crawling:

$$\text{Token Reduction Rate} = \frac{\text{Tokens}_{\text{raw}} - \text{Tokens}_{\text{router}}}{\text{Tokens}_{\text{raw}}} \times 100\%$$

- **Observed Benchmark:** Achieves **>70% to >85% token reduction**, keeping LLM prompts lean and maximizing prompt cache hit rates.

### 2.3 Retrieval Latency & Cycle Time (ms)
Measures the wall-clock execution time taken to return full context:
- **Raw Traversal:** ~6ms to 50ms depending on file count and depth.
- **Hybrid Context Router:** ~2ms to 5ms locally in pure Python standard library.
- **Speedup Multiplier:** $\frac{T_{\text{raw}}}{T_{\text{router}}}$.

### 2.4 Prompt Performance & Assistant Time Savings (Google Cloud Framework)
Translates token and latency savings into concrete engineering productivity KPIs:
1. **Prompt Dollar Savings:** Based on input context avoided (\$3.00 per 1M input tokens):
   $$\text{Savings}_{1\text{k queries}} = \left(\frac{\Delta \text{Tokens} \times 1000}{1,000,000}\right) \times \$3.00$$
2. **Sprint Hours Reclaimed:** Avoiding recursive search tool flailing eliminates ~2 minutes of inference wait and multi-turn correction per agent task. Over a 2-week sprint with 200 agent tasks:
   $$\text{Hours Reclaimed} = \frac{200 \times 2.0 \text{ min}}{60} \approx 6.7 \text{ hours/sprint}$$

---

## 3. CLI Commands & Usage

All commands can be invoked via the root `Makefile` or directly through Python:

### 3.1 Run Full A/B Benchmark
Executes all benchmark intents and prints a GitHub-flavored markdown report:
```bash
make eval
# Or directly:
PYTHONPATH="packages/agent-evals:packages/context-router" python3 packages/agent-evals/agent_evals/runner.py
```

To export results as JSON:
```bash
PYTHONPATH="packages/agent-evals:packages/context-router" python3 packages/agent-evals/agent_evals/runner.py --json
```

To persist the report to `docs/evals/`:
```bash
PYTHONPATH="packages/agent-evals:packages/context-router" python3 packages/agent-evals/agent_evals/runner.py --output docs/evals/latest.md
```

### 3.2 Run Quality Gatekeeper
Enforces that retrieval accuracy meets or exceeds the pass threshold (default: 90%):
```bash
make eval-gate
# Or strict 100% threshold:
PYTHONPATH="packages/agent-evals:packages/context-router" python3 packages/agent-evals/agent_evals/gatekeeper.py --strict
```

### 3.3 Run Unit Tests
```bash
PYTHONPATH="packages/agent-evals:packages/context-router" python3 -m unittest discover -s packages/agent-evals/tests
```

---

## 4. Pre-commit & CI Integration

Following the *Claude AI-Native SDLC Playbook*, any developer or autonomous agent modifying or relocating an `AGENTS.md` file must prove that context discovery remains intact before committing code.

The gatekeeper runs automatically in:
1. **Git Pre-commit Hook (`.ai/scripts/pre-commit-hook.sh`):**
   - Automatically re-indexes modified `AGENTS.md` files.
   - Stages updated `INDEX.json`, `MAP.md`, and vector cache.
   - Executes `agent_evals.gatekeeper`.
   - Rejects the commit if retrieval accuracy drops below 90%.
2. **CI Pull Request Workflows:**
   - Ensures PRs cannot merge if domain boundary relocations break agent discovery.

---

## 5. Agent Self-Tuning Guide (Continuous Optimization)

Autonomous agents can utilize the generated evaluation metrics to self-tune the scoring weights of `packages/context-router`.

### Composite Retrieval Scoring Formula:
$$\text{Score} = w_{\text{semantic}} S_{\text{semantic}} + w_{\text{lexical}} S_{\text{lexical}} + w_{\text{domain}} S_{\text{domain}} + w_{\text{title}} S_{\text{title}}$$

Default configuration:
- $w_{\text{semantic}} = 0.40$
- $w_{\text{lexical}} = 0.35$
- $w_{\text{domain}} = 0.15$
- $w_{\text{title}} = 0.10$

### Self-Tuning Heuristics:
1. **High Semantic Drift (Exact identifier misses):**
   - *Symptom:* The agent searches for a specific symbol (e.g. `authMiddleware`) but retrieves a generic overview chunk.
   - *Action:* Increase lexical weight ($w_{\text{lexical}} \to 0.45$) and decrease semantic weight ($w_{\text{semantic}} \to 0.30$).
2. **Vocabulary Mismatch (Synonym misses):**
   - *Symptom:* The developer asks "Where is credential verification?" and misses `packages/auth` because the word "credential" appears infrequently.
   - *Action:* Increase semantic subword weight ($w_{\text{semantic}} \to 0.50$) and domain boost ($w_{\text{domain}} \to 0.20$).
3. **Cross-Domain Ambiguity:**
   - *Symptom:* Gateway and database share similar routing tokens.
   - *Action:* Increase section title boost ($w_{\text{title}} \to 0.20$) and domain boost ($w_{\text{domain}} \to 0.25$).

Evaluation results saved in `docs/evals/` allow continuous agents (Skill 07 Evaluator) to run hyperparameter sweeps and store optimal weights in `packages/context-router/context_router/engine.py`.
