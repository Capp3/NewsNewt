FROM python:3.12-slim-bookworm

# Install uv by copying the pre-built binary from the official uv image
# Pinning to a specific version is best practice for reproducibility
COPY --from=ghcr.io/astral-sh/uv:0.9.11 /uv /uvx /bin/

ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies required for Playwright and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    fonts-liberation \
    fonts-noto-color-emoji \
    libxshmfence1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Create logs directory
RUN mkdir -p /app/logs

# Set Playwright environment variables
ENV PLAYWRIGHT_BROWSERS_PATH=/app/.playwright
ENV PLAYWRIGHT_SKIP_BROWSER_DOWNLOAD=0

# Set Python path to include src directory
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Copy project files (use .dockerignore to exclude unnecessary files)
COPY . .

# Install Python dependencies (frozen lockfile)
RUN uv sync --frozen

# Install Playwright browsers
RUN uv run playwright install chromium --with-deps

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:3000/health')"

# Run the application
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "3000"]
