# Contributing to NewsNewt

Thank you for your interest in contributing to NewsNewt! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Git

### Getting Started

1. Fork the repository and clone your fork:
   ```bash
   git clone https://github.com/your-username/NewsNewt.git
   cd NewsNewt
   ```

2. Install dependencies:
   ```bash
   uv sync
   ```

3. Set up configuration:
   ```bash
   cp config/.env.sample config/.env
   # Edit config/.env with your settings
   ```

4. Verify the setup:
   ```bash
   uv run python -m newsnewt
   ```

## Development Workflow

### Code Style

NewsNewt uses the following tools for code quality:

- **Black** - Code formatting
- **Ruff** - Linting and import sorting

Before committing, ensure your code passes:

```bash
# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/
uv run ruff format --check src/ tests/
```

### Testing

- Write tests for new features and bug fixes
- Ensure all tests pass before submitting a PR:
  ```bash
  uv run pytest
  ```
- Aim for meaningful test coverage, especially for critical paths

### Project Structure

- `src/newsnewt/` - Main application code
- `tests/` - Test suite
- `docs/` - Documentation
- `config/` - Configuration files
- `logs/` - Application logs (gitignored)

## Pull Request Process

1. **Create a branch** from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. **Make your changes** following the code style guidelines

3. **Write or update tests** as needed

4. **Update documentation** if you're changing functionality

5. **Commit your changes** with clear, descriptive commit messages:
   ```bash
   git commit -m "Add feature: description of what you did"
   ```

6. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

7. **Open a Pull Request** on GitHub with:
   - Clear description of changes
   - Reference to related issues (if any)
   - Testing notes

### Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Be descriptive but concise
- Reference issue numbers when applicable: "Fix #123: description"

### PR Checklist

Before submitting, ensure:

- [ ] Code follows style guidelines (black, ruff)
- [ ] Tests pass locally
- [ ] Documentation updated (if needed)
- [ ] No merge conflicts with main
- [ ] Commit messages are clear

## Code Review

- All PRs require review before merging
- Address review feedback promptly
- Be open to suggestions and constructive criticism
- Keep PRs focused and reasonably sized

## Project Philosophy

NewsNewt follows a "one-trick pony" philosophy:

- **Minimal and focused** - Avoid feature creep
- **Archive-first workflow** - Mandatory archiving ensures content preservation
- **Clear error handling** - Structured error responses
- **Private network deployment** - Designed for controlled environments

When proposing changes, consider:

- Does this align with the project's single-purpose design?
- Is this necessary for the MVP or core functionality?
- Can this be achieved with existing dependencies?

## Questions?

- Check existing documentation in `docs/`
- Review open issues and PRs
- Open a discussion issue for questions

Thank you for contributing to NewsNewt!

