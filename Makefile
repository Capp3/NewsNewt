# NewsNewt Makefile
# Docker compose and development commands

.PHONY: help install setup lint lint-fix up down exec build logs

# Default target
help:
	@echo "Available commands:"
	@echo "  install    - Install uv package manager"
	@echo "  setup      - Create virtual environment with uv"
	@echo "  up         - Start containers with docker compose"
	@echo "  down       - Stop containers with docker compose"
	@echo "  exec       - Execute command in container (usage: make exec CMD='bash')"
	@echo "  build      - Build images without cache"
	@echo "  logs       - View container logs"
	@echo "  lint       - Run linting checks (ruff + pyright)"
	@echo "  lint-fix   - Auto-fix linting issues with ruff"
	@echo "  help       - Show this help message"

# Install uv package manager
install:
	@echo "Installing uv..."
	curl -LsSf https://astral.sh/uv/install.sh | sh
	@echo "uv installed successfully!"

# Create virtual environment with uv
setup:
	@echo "Creating virtual environment with uv..."
	uv venv
	@echo "Virtual environment created!"

# Start containers with docker compose
up:
	@echo "Starting containers..."
	docker compose up -d
	@echo "Containers started!"

# Stop containers with docker compose
down:
	@echo "Stopping containers..."
	docker compose down
	@echo "Containers stopped!"

# Execute command in container
exec:
	@if [ -z "$(CMD)" ]; then \
		echo "Error: CMD is required. Usage: make exec CMD='bash'"; \
		exit 1; \
	fi
	docker compose exec newsnewt $(CMD)

# Build images without cache
build:
	@echo "Building images without cache..."
	docker compose build --no-cache
	@echo "Build complete!"

# View container logs
logs:
	@echo "Viewing container logs (Ctrl+C to exit)..."
	docker compose logs -f

# Run linting checks with ruff and pyright
lint:
	@echo "Running linting checks..."
	@echo "Checking with ruff..."
	uv run ruff check src/ tests/
	@echo "Checking formatting with ruff..."
	uv run ruff format --check src/ tests/
	@echo "Type checking with pyright..."
	uv run pyright src/ tests/
	@echo "Linting complete!"

# Auto-fix linting issues with ruff
lint-fix:
	@echo "Auto-fixing linting issues..."
	@echo "Fixing ruff issues..."
	uv run ruff check --fix src/ tests/
	@echo "Formatting code with ruff..."
	uv run ruff format src/ tests/
	@echo "Auto-fix complete! Run 'make lint' to verify."
