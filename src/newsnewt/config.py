"""Configuration management for NewsNewt."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from config/.env if it exists
env_path = Path(__file__).parent.parent.parent / "config" / ".env"
if env_path.exists():
    load_dotenv(env_path)


class Settings:
    """Application settings loaded from environment variables."""

    # Archive service configuration
    archive_service: str = os.getenv("NEWSNEWT_ARCHIVE_SERVICE", "archive_is")

    # Timeout configuration (in seconds)
    timeout_seconds: int = int(os.getenv("NEWSNEWT_TIMEOUT_SECONDS", "300"))

    # Logging configuration
    log_level: str = os.getenv("NEWSNEWT_LOG_LEVEL", "INFO")

    # Timezone configuration
    timezone: str = os.getenv("TZ", "UTC")

    # Log directory
    log_dir: Path = Path(__file__).parent.parent.parent / "logs"
    log_file: Path = log_dir / "newsnewt.log"

    def __init__(self):
        """Initialize settings and create log directory if needed."""
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def validate(self) -> None:
        """Validate configuration settings."""
        # Validate archive service
        valid_services = ["archive_is", "archive_today", "auto"]
        if self.archive_service not in valid_services:
            raise ValueError(
                f"Invalid NEWSNEWT_ARCHIVE_SERVICE: {self.archive_service}. "
                f"Must be one of {valid_services}"
            )

        # Validate timeout
        if self.timeout_seconds <= 0:
            raise ValueError(
                f"Invalid NEWSNEWT_TIMEOUT_SECONDS: {self.timeout_seconds}. "
                "Must be greater than 0"
            )

        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(
                f"Invalid NEWSNEWT_LOG_LEVEL: {self.log_level}. "
                f"Must be one of {valid_log_levels}"
            )


# Global settings instance
settings = Settings()
