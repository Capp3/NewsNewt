# Vibe Dev Template Makefile
# Example Makefile with uv and mkdocs commands

TEMP_DIR := ./temp
USERNAME := $(USER)


.PHONY: help install setup serve build clean lint lint-fix

# Default target
help: ## Show this help message
	@echo "Available targets:"
	@fgrep -h "##" $(MAKEFILE_LIST) | grep -v fgrep | sed -e 's/\([^:]*\):[^#]*##\(.*\)/  \1|\2/' | column -t -s '|'



install: ## Install uv package manager
	@echo "Installing uv..."
	curl -LsSf https://astral.sh/uv/install.sh | sh
	@echo "uv installed successfully!"

# Create virtual environment with uv
setup: ## Create virtual environment with uv
	@echo "Creating virtual environment with uv..."
	uv venv
	@echo "Virtual environment created!"

# Start MkDocs development server using uvx (no local install needed)
serve: ## Start MkDocs development server using uvx (no local install needed)
	@echo "Starting MkDocs development server..."
	uvx mkdocs serve

# Build MkDocs static site using uvx
build: ## Build MkDocs static site using uvx
	@echo "Building MkDocs static site..."
	uvx mkdocs build

# Clean build artifacts
clean: ## Clean build artifacts
	@echo "Cleaning build artifacts..."
	rm -rf site/
	rm -rf .cache/
	@echo "Clean complete!"

# Development workflow - setup and serve
dev: setup serve ## Development workflow - setup and serve

# Full build workflow
deploy: build ## Full build workflow
	@echo "Site built in 'site/' directory"
	@echo "Ready for deployment!"

# Run linting checks with ruff and pyright
lint: ## Run linting checks with ruff and pyright
	@echo "Running linting checks..."
	@echo "Checking with ruff..."
	uv run ruff check src/ tests/
	@echo "Checking formatting with ruff..."
	uv run ruff format --check src/ tests/
	@echo "Type checking with pyright..."
	uv run pyright src/ tests/
	@echo "Linting complete!"

# Auto-fix linting issues with ruff
lint-fix: ## Auto-fix linting issues with ruff
	@echo "Auto-fixing linting issues..."
	@echo "Fixing ruff issues..."
	uv run ruff check --fix src/ tests/
	@echo "Formatting code with ruff..."
	uv run ruff format src/ tests/
	@echo "Auto-fix complete! Run 'make lint' to verify."

post-install: ## Clean up after installation
	@echo "Running post-install cleanup..."
	@rm -rf $(SCRIPTS_DIR) 2>/dev/null || true
	@rm -rf $(TEMP_DIR) 2>/dev/null || true
	@echo "Post-install cleanup complete."

# =============================================================================
# Cursor Memory Bank
# =============================================================================
# Source: https://github.com/vanzan01/cursor-memory-bank
# Provides AI-powered development commands and rules for Cursor IDE

update-memory-bank: ## Update the memory bank commands and rules
	@echo "Updating Cursor Memory Bank..."
	@mkdir -p $(TEMP_DIR)
	@if git clone --depth 1 https://github.com/vanzan01/cursor-memory-bank.git $(TEMP_DIR)/cursor-memory-bank 2>/dev/null; then \
		echo "Successfully cloned cursor-memory-bank repository"; \
		if [ -d "$(TEMP_DIR)/cursor-memory-bank/.cursor/commands" ]; then \
			mkdir -p .cursor/commands; \
			cp -R $(TEMP_DIR)/cursor-memory-bank/.cursor/commands/* .cursor/commands/ && \
			echo "Commands updated successfully"; \
		else \
			echo "Warning: Commands directory not found in repository"; \
		fi; \
		if [ -d "$(TEMP_DIR)/cursor-memory-bank/.cursor/rules/isolation_rules" ]; then \
			mkdir -p .cursor/rules/isolation_rules; \
			cp -R $(TEMP_DIR)/cursor-memory-bank/.cursor/rules/isolation_rules/* .cursor/rules/isolation_rules/ && \
			echo "Isolation rules updated successfully"; \
		else \
			echo "Warning: Isolation rules directory not found in repository"; \
		fi; \
		rm -rf $(TEMP_DIR)/cursor-memory-bank; \
		echo "Memory bank update complete."; \
	else \
		echo "Error: Failed to clone cursor-memory-bank repository"; \
		echo "Please check your internet connection and try again"; \
		exit 1; \
	fi

install-memory-bank: update-memory-bank ## Install the memory bank commands and rules (alias for update)

# =============================================================================
# Awesome Cursor Rules
# =============================================================================
# Source: https://github.com/PatrickJS/awesome-cursorrules
# Collection of cursor rules for various frameworks and languages

update-rules: ## Update cursor rules for frameworks and languages
	@echo "Updating Awesome Cursor Rules..."
	@mkdir -p $(TEMP_DIR)
	@if git clone --depth 1 https://github.com/PatrickJS/awesome-cursorrules.git $(TEMP_DIR)/awesome-cursorrules 2>/dev/null; then \
		echo "Successfully cloned awesome-cursorrules repository"; \
		if [ -d "$(TEMP_DIR)/awesome-cursorrules/rules-new/" ]; then \
			mkdir -p .cursor/rules; \
			cp -R $(TEMP_DIR)/awesome-cursorrules/rules-new/* .cursor/rules/ && \
			echo "Rules updated successfully"; \
		else \
			echo "Warning: Rules directory not found in repository"; \
		fi; \
		rm -rf $(TEMP_DIR)/awesome-cursorrules; \
		echo "Rules update complete."; \
	else \
		echo "Error: Failed to clone awesome-cursorrules repository"; \
		echo "Please check your internet connection and try again"; \
		exit 1; \
	fi

install-rules: update-rules ## Install cursor rules (alias for update)

# =============================================================================
# Combined Installation
# =============================================================================

vibe: install-rules install-memory-bank ## Install both cursor rules and memory bank
	@echo ""
	@echo "=========================================="
	@echo "Vibe setup complete!"
	@echo "=========================================="
	@echo "Installed:"
	@echo "  - Cursor Memory Bank (commands & rules)"
	@echo "  - Awesome Cursor Rules (framework rules)"
	@echo ""
	@echo "Please restart Cursor IDE to load the new configurations."
	@echo ""
