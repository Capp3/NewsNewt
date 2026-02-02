# Development Guide

## Setup

### Prerequisites

- Python 3.12+
- `uv` package manager installed
- Docker and Docker Compose (for containerized deployment)

### Initial Setup

```bash
# Install all dependencies from pyproject.toml
uv sync

# Install Playwright browsers
uv run playwright install chromium --with-deps
```

### Running Locally

```bash
# Run the FastAPI application
uv run uvicorn app.main:app --host 0.0.0.0 --port 3000 --reload
```

## Dependency Management

### Adding Dependencies

**Always use `uv`, never `pip`:**

```bash
# Add a new dependency
uv add <package-name>

# Add a development dependency
uv add --dev <package-name>

# Add with version constraint
uv add "package-name>=1.0.0"
```

### Updating Dependencies

```bash
# Update all dependencies
uv sync --upgrade

# Update specific package
uv add --upgrade <package-name>
```

### Lock File

- `uv.lock` is automatically generated and should be committed
- Run `uv sync --frozen` in CI/CD to ensure reproducible builds

## Project Structure

- `pyproject.toml` - Project configuration and dependencies
- `uv.lock` - Locked dependency versions
- `src/app/` - Application source code
- `memory-bank/` - Project documentation and planning

## Important Notes

- **Never use `pip`** - Always use `uv` commands
- Dependencies are managed in `pyproject.toml`, not `requirements.txt`
- Use `uv run` prefix for all Python commands
- The project uses `uv`'s virtual environment management automatically
