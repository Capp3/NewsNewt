"""Unit tests for configuration module."""

from pathlib import Path

import pytest

from newsnewt.config import Settings


class TestSettings:
    """Tests for Settings configuration."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        settings = Settings()
        assert settings.archive_service == "archive_is"
        assert settings.timeout_seconds == 300
        assert settings.log_level == "INFO"
        assert isinstance(settings.log_dir, Path)

    def test_archive_service_validation_valid(self):
        """Test validation accepts valid archive services."""
        # Should not raise
        settings = Settings()
        settings.validate()

    def test_archive_service_validation_invalid(self, monkeypatch):
        """Test validation rejects invalid archive services."""
        monkeypatch.setenv("NEWSNEWT_ARCHIVE_SERVICE", "invalid_service")
        # Need to reload the module for env var to take effect
        from importlib import reload

        import newsnewt.config as config_module

        reload(config_module)
        settings = config_module.Settings()
        with pytest.raises(ValueError, match="Invalid.*ARCHIVE_SERVICE"):
            settings.validate()

    def test_timeout_validation_valid(self):
        """Test validation accepts valid timeout."""
        settings = Settings()
        settings.validate()

    def test_timeout_validation_zero(self, monkeypatch):
        """Test validation rejects zero timeout."""
        monkeypatch.setenv("NEWSNEWT_TIMEOUT_SECONDS", "0")
        from importlib import reload

        import newsnewt.config as config_module

        reload(config_module)
        settings = config_module.Settings()
        with pytest.raises(ValueError, match="greater than 0"):
            settings.validate()

    def test_timeout_validation_negative(self, monkeypatch):
        """Test validation rejects negative timeout."""
        monkeypatch.setenv("NEWSNEWT_TIMEOUT_SECONDS", "-10")
        from importlib import reload

        import newsnewt.config as config_module

        reload(config_module)
        settings = config_module.Settings()
        with pytest.raises(ValueError, match="greater than 0"):
            settings.validate()

    def test_log_level_validation_valid(self):
        """Test validation accepts valid log levels."""
        settings = Settings()
        settings.validate()

    def test_log_level_validation_invalid(self, monkeypatch):
        """Test validation rejects invalid log level."""
        monkeypatch.setenv("NEWSNEWT_LOG_LEVEL", "INVALID")
        from importlib import reload

        import newsnewt.config as config_module

        reload(config_module)
        settings = config_module.Settings()
        with pytest.raises(ValueError, match="Invalid.*LOG_LEVEL"):
            settings.validate()

    def test_environment_variable_override(self, monkeypatch):
        """Test that environment variables override defaults."""
        monkeypatch.setenv("NEWSNEWT_ARCHIVE_SERVICE", "archive_today")
        monkeypatch.setenv("NEWSNEWT_TIMEOUT_SECONDS", "120")
        monkeypatch.setenv("NEWSNEWT_LOG_LEVEL", "DEBUG")

        # Reload module to pick up env vars
        from importlib import reload

        import newsnewt.config as config_module

        reload(config_module)
        settings = config_module.Settings()
        assert settings.archive_service == "archive_today"
        assert settings.timeout_seconds == 120
        assert settings.log_level == "DEBUG"

    def test_directories_are_paths(self):
        """Test that directory settings are Path objects."""
        settings = Settings()
        assert isinstance(settings.log_dir, Path)
        assert isinstance(settings.log_file, Path)
        assert str(settings.log_dir).endswith("logs")
        assert str(settings.log_file).endswith("newsnewt.log")
