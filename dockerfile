FROM python:3.12-slim-bookworm

# Install uv by copying the pre-built binary from the official uv image
# Pinning to a specific version is best practice for reproducibility
COPY --from=ghcr.io/astral-sh/uv:0.9.11 /uv /uvx /bin/

# Set working directory
WORKDIR /app

# Create logs directory
RUN mkdir -p /app/logs

# Copy project files (use .dockerignore to exclude unnecessary files)
COPY . .

# Install dependencies (frozen lockfile)
RUN uv sync --frozen

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"

# Run the application
CMD ["uv", "run", "python", "-m", "newsnewt.main"]
