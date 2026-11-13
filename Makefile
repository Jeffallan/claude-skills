.PHONY: dev-link dev-unlink guard guard-check guard-test validate test evidence eval-workflow eval-intake eval-baseline site-dev site-build lint format lint-fix

PLUGIN_NAME := fullstack-dev-skills
VERSION := $(shell python -c "import json; print(json.load(open('version.json'))['version'])")
CACHE_BASE := $(HOME)/.claude/plugins/cache/$(PLUGIN_NAME)/$(PLUGIN_NAME)
CACHE_DIR := $(CACHE_BASE)/$(VERSION)

dev-link:
	@if [ -L "$(CACHE_DIR)" ]; then \
		echo "Error: $(CACHE_DIR) is already a symlink."; \
		exit 1; \
	fi
	@if [ -d "$(CACHE_DIR).bak" ]; then \
		echo "Error: Backup already exists at $(CACHE_DIR).bak"; \
		echo "Run 'make dev-unlink' first to restore it."; \
		exit 1; \
	fi
	@if [ ! -d "$(CACHE_DIR)" ]; then \
		echo "Error: Cache directory not found at $(CACHE_DIR)"; \
		echo "Is the plugin installed? Check: cat ~/.claude/plugins/installed_plugins.json"; \
		exit 1; \
	fi
	mv "$(CACHE_DIR)" "$(CACHE_DIR).bak"
	ln -s "$(CURDIR)" "$(CACHE_DIR)"
	@echo ""
	@echo "Linked: $(CACHE_DIR) -> $(CURDIR)"
	@echo "Restart Claude Code to load changes from your working copy."

dev-unlink:
	@if [ ! -L "$(CACHE_DIR)" ]; then \
		echo "Error: $(CACHE_DIR) is not a symlink. Nothing to unlink."; \
		exit 1; \
	fi
	@if [ ! -d "$(CACHE_DIR).bak" ]; then \
		echo "Error: No backup found at $(CACHE_DIR).bak"; \
		exit 1; \
	fi
	rm "$(CACHE_DIR)"
	mv "$(CACHE_DIR).bak" "$(CACHE_DIR)"
	@echo ""
	@echo "Restored cache from backup."
	@echo "Restart Claude Code to load the released version."

guard:
	python3 scripts/build-guard.py runtime runtime/guard.pyz

guard-check:
	python3 scripts/build-guard.py runtime runtime/guard.pyz --check

guard-test:
	cd runtime && PYTHONPATH=. uv run --no-project --with pytest python -m pytest tests -q -p no:cacheprovider

validate:
	uvx skill-linter@0.4.0 release
	uvx skill-linter@0.4.0 stamp --check

test: guard-check guard-test
	bash scripts/test-makefile.sh
	bash scripts/test-build-plugin-dist.sh
	bash scripts/test-review-wiring.sh
	bash scripts/test-launch-command.sh
	bash scripts/test-eval-workflow.sh
	bash scripts/test-eval-intake.sh

EXPECT_UPSTREAM ?= 0
RETIRED ?= spec:reopen\|create-epic\|complete-sprint\|execute-ticket

evidence:
	EXPECT_UPSTREAM=$(EXPECT_UPSTREAM) RETIRED='$(RETIRED)' bash scripts/evidence.sh

site-dev:
	cd site && npm run dev

site-build:
	cd site && npm run build

lint:
	ruff check scripts/
	ruff format --check scripts/
	pyright scripts/
	cd site && npx prettier --plugin prettier-plugin-astro --check "src/**" "scripts/**" astro.config.mjs
	npx prettier --check "skills/**/*.md" "docs/**/*.md" "*.md" "research/**/*.md"

format:
	ruff check --fix scripts/
	ruff format scripts/
	cd site && npx prettier --plugin prettier-plugin-astro --write "src/**" "scripts/**" astro.config.mjs
	npx prettier --write "skills/**/*.md" "docs/**/*.md" "*.md" "research/**/*.md"

lint-fix: format

eval-workflow:
	@python3 scripts/eval_workflow_run.py $(if $(EVAL),--eval "$(EVAL)" --run "$(RUN)") \
		$(if $(REPO),--repo "$(REPO)") $(if $(SPEC),--spec "$(SPEC)") \
		$(if $(GOLD),--gold "$(GOLD)") $(foreach t,$(TRANSCRIPTS),--transcript "$(t)") $(if $(REFLOG),--reflog "$(REFLOG)") \
		$(if $(PLUGIN),--version "$(PLUGIN)") $(if $(MODEL),--model "$(MODEL)")

eval-intake:
	@python3 scripts/eval_intake_run.py $(if $(EVAL),--eval "$(EVAL)" --run "$(RUN)") \
		$(if $(REPO),--repo "$(REPO)") $(if $(START),--start "$(START)") \
		$(if $(TEST_CMD),--test-cmd "$(TEST_CMD)") $(foreach g,$(TEST_PATHS),--test-path "$(g)") $(foreach t,$(TRANSCRIPTS),--transcript "$(t)") $(if $(REFLOG),--reflog "$(REFLOG)") \
		$(if $(PLUGIN),--version "$(PLUGIN)") $(if $(MODEL),--model "$(MODEL)")

eval-baseline:
	@python3 scripts/eval_intake_baseline.py "$(EVAL)"