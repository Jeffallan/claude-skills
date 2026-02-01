.PHONY: dev-link dev-unlink validate test

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

validate:
	python scripts/validate-skills.py
	python scripts/update-docs.py --check

test:
	bash scripts/test-makefile.sh
