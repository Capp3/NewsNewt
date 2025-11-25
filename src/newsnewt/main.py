"""Main entry point for NewsNewt service."""

import uvicorn

from newsnewt.api import app
from newsnewt.config import settings
from newsnewt.logging_config import get_logger

logger = get_logger(__name__)


def main() -> None:
    """Run the NewsNewt service."""
    logger.info("Starting NewsNewt service")
    logger.info(
        f"Configuration: archive_service={settings.archive_service}, "
        f"timeout={settings.timeout_seconds}s, log_level={settings.log_level}"
    )

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config=None,  # We handle logging ourselves
    )


if __name__ == "__main__":
    main()
