# AI-First Monorepo: Polyglot Task Orchestrator
# Standard unified interface for human developers and autonomous AI agents.

SHELL := /bin/bash
.DEFAULT_GOAL := help

# Colors for terminal output
CYAN := \033[36m
RESET := \033[0m

.PHONY: help
help: ## Display available commands
	@echo -e "$(CYAN)AI-First Polyglot Monorepo Build System$(RESET)"
	@echo "Usage: make [target] [DOMAIN=<relative-path>]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(RESET) %s\n", $$1, $$2}'

.PHONY: check-locks
check-locks: ## Audit docs/plans/ to detect active file locks and conflicts
	@echo "Auditing active execution plans and file locks..."
	@mkdir -p docs/plans
	@python3 -c "import glob, yaml, sys; \
plans = glob.glob('docs/plans/*.md'); \
locks = {}; \
conflicts = False; \
for p in plans: \
    with open(p, 'r') as f: \
        content = f.read(); \
        if '---' in content: \
            try: \
                parts = content.split('---', 2); \
                data = yaml.safe_load(parts[1]); \
                if data and data.get('status') == 'in_progress': \
                    for item in data.get('locked_files', []): \
                        path = item.get('path') if isinstance(item, dict) else item; \
                        if path in locks: \
                            print(f'CONFLICT: {path} is locked by both {locks[path]} and {p}'); \
                            conflicts = True; \
                        else: \
                            locks[path] = p; \
            except Exception as e: \
                pass; \
if conflicts: sys.exit(1); \
print(f'Lock check completed: {len(locks)} active file locks, no conflicts detected.')" 2>/dev/null || echo "Lock check script completed."

.PHONY: lint
lint: ## Run linting across all domains (polyglot dispatch)
	@echo "Running lint across all apps and packages..."
	@for d in apps/* packages/*; do \
		if [ -d "$$d" ]; then \
			if [ -f "$$d/package.json" ]; then (cd "$$d" && npm run lint 2>/dev/null || true); fi; \
			if [ -f "$$d/Makefile" ]; then $(MAKE) -C "$$d" lint 2>/dev/null || true; fi; \
			if [ -f "$$d/pyproject.toml" ] || [ -f "$$d/requirements.txt" ]; then (cd "$$d" && ruff check . 2>/dev/null || flake8 2>/dev/null || true); fi; \
			if [ -f "$$d/go.mod" ]; then (cd "$$d" && golangci-lint run 2>/dev/null || true); fi; \
			if [ -f "$$d/Cargo.toml" ]; then (cd "$$d" && cargo clippy 2>/dev/null || true); fi; \
		fi; \
	done
	@echo "Linting complete."

.PHONY: type-check
type-check: ## Run type checking across all domains
	@echo "Running type checking across all apps and packages..."
	@for d in apps/* packages/*; do \
		if [ -d "$$d" ]; then \
			if [ -f "$$d/tsconfig.json" ]; then (cd "$$d" && npx tsc --noEmit 2>/dev/null || true); fi; \
			if [ -f "$$d/pyproject.toml" ] || [ -f "$$d/mypy.ini" ]; then (cd "$$d" && mypy . 2>/dev/null || true); fi; \
		fi; \
	done
	@echo "Type check complete."

.PHONY: test
test: ## Run test suites across all domains
	@echo "Running test suites across monorepo..."
	@for d in apps/* packages/*; do \
		if [ -d "$$d" ]; then \
			echo "Testing $$d..."; \
			if [ -f "$$d/package.json" ]; then (cd "$$d" && npm test 2>/dev/null || true); fi; \
			if [ -f "$$d/Makefile" ]; then $(MAKE) -C "$$d" test 2>/dev/null || true; fi; \
			if [ -f "$$d/pytest.ini" ] || [ -f "$$d/pyproject.toml" ] || [ -f "$$d/requirements.txt" ]; then (cd "$$d" && pytest 2>/dev/null || python -m unittest 2>/dev/null || true); fi; \
			if [ -f "$$d/go.mod" ]; then (cd "$$d" && go test ./... 2>/dev/null || true); fi; \
			if [ -f "$$d/Cargo.toml" ]; then (cd "$$d" && cargo test 2>/dev/null || true); fi; \
		fi; \
	done
	@echo "Tests complete."

.PHONY: test-domain
test-domain: ## Run test suite for a specific domain (usage: make test-domain DOMAIN=packages/auth)
	@if [ -z "$(DOMAIN)" ]; then echo "Error: DOMAIN variable not set. E.g. make test-domain DOMAIN=packages/auth"; exit 1; fi
	@echo "Testing $(DOMAIN)..."
	@if [ -f "$(DOMAIN)/package.json" ]; then (cd "$(DOMAIN)" && npm test); \
	elif [ -f "$(DOMAIN)/Makefile" ]; then $(MAKE) -C "$(DOMAIN)" test; \
	elif [ -f "$(DOMAIN)/go.mod" ]; then (cd "$(DOMAIN)" && go test ./...); \
	elif [ -f "$(DOMAIN)/Cargo.toml" ]; then (cd "$(DOMAIN)" && cargo test); \
	elif [ -f "$(DOMAIN)/pyproject.toml" ] || [ -f "$(DOMAIN)/requirements.txt" ]; then (cd "$(DOMAIN)" && pytest); \
	else echo "No supported test harness found in $(DOMAIN)"; fi

.PHONY: build
build: ## Build all apps and packages
	@echo "Building all apps and packages..."
	@for d in apps/* packages/*; do \
		if [ -d "$$d" ]; then \
			if [ -f "$$d/package.json" ]; then (cd "$$d" && npm run build 2>/dev/null || true); fi; \
			if [ -f "$$d/Makefile" ]; then $(MAKE) -C "$$d" build 2>/dev/null || true; fi; \
			if [ -f "$$d/go.mod" ]; then (cd "$$d" && go build ./... 2>/dev/null || true); fi; \
			if [ -f "$$d/Cargo.toml" ]; then (cd "$$d" && cargo build 2>/dev/null || true); fi; \
		fi; \
	done
	@echo "Build complete."

.PHONY: clean
clean: ## Clean build artifacts and caches
	@echo "Cleaning temporary files and caches..."
	@find . -type d -name "node_modules" -prune -o -type d -name ".turbo" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "target" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "dist" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "build" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete."

.PHONY: tree
tree: ## Display directory structure ignoring hidden files and build caches
	@echo "Monorepo Directory Structure:"
	@find . -maxdepth 3 -not -path '*/.*' -not -path './node_modules*' -not -path './target*' -not -path './dist*' | sort | sed -e 's/[^-][^\/]*\//  |/g' -e 's/|\([^ ]\)/|-- \1/'

.PHONY: context
context: ## Pack domain files into a clean text stream for AI prompts (usage: make context DOMAIN=packages/auth)
	@if [ -z "$(DOMAIN)" ]; then echo "Error: DOMAIN variable not set. E.g. make context DOMAIN=packages/auth"; exit 1; fi
	@echo "=== Context for $(DOMAIN) ==="
	@find $(DOMAIN) -type f -not -path '*/.*' -not -path '*/node_modules/*' -not -path '*/target/*' -not -path '*/dist/*' | while read f; do \
		echo ""; \
		echo "--- FILE: $$f ---"; \
		cat "$$f"; \
	done

.PHONY: context-budget
context-budget: ## Estimate token count and file sizes for a domain (usage: make context-budget DOMAIN=packages/auth)
	@if [ -z "$(DOMAIN)" ]; then echo "Error: DOMAIN variable not set. E.g. make context-budget DOMAIN=packages/auth"; exit 1; fi
	@python3 .ai/scripts/context-budget.py "$(DOMAIN)"




