"""Tests for configuration module."""

import os
from unittest.mock import patch


from app.config import Config


class TestConfig:
    """Test configuration loading and validation."""

    def test_default_values(self):
        """Test that default values are set correctly."""
        assert Config.log_level == "INFO" or os.getenv("LOG_LEVEL")
        assert isinstance(Config.playwright_headless, bool)
        assert isinstance(Config.enable_stealth, bool)
        assert isinstance(Config.crawl_concurrency, int)

    def test_crawler_settings_dict(self):
        """Test that get_crawler_settings returns proper dictionary."""
        settings = Config.get_crawler_settings()

        assert isinstance(settings, dict)
        assert "headless" in settings
        assert "enable_stealth" in settings
        assert "max_concurrency" in settings
        assert "log_level" in settings

        # Check types
        assert isinstance(settings["headless"], bool)
        assert isinstance(settings["enable_stealth"], bool)
        assert isinstance(settings["max_concurrency"], int)
        assert isinstance(settings["log_level"], str)

    @patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"})
    def test_log_level_from_env(self):
        """Test that log level can be set from environment."""
        # Reload config to pick up env var
        from importlib import reload
        from app import config as config_module

        reload(config_module)

        assert config_module.Config.log_level == "DEBUG"

    @patch.dict(os.environ, {"CRAWL_CONCURRENCY": "5"})
    def test_concurrency_from_env(self):
        """Test that concurrency can be set from environment."""
        from importlib import reload
        from app import config as config_module

        reload(config_module)

        assert config_module.Config.crawl_concurrency == 5

    @patch.dict(os.environ, {"PLAYWRIGHT_HEADLESS": "false"})
    def test_headless_false_from_env(self):
        """Test that headless mode can be disabled from environment."""
        from importlib import reload
        from app import config as config_module

        reload(config_module)

        assert config_module.Config.playwright_headless is False

    @patch.dict(os.environ, {"ENABLE_STEALTH": "false"})
    def test_stealth_false_from_env(self):
        """Test that stealth mode can be disabled from environment."""
        from importlib import reload
        from app import config as config_module

        reload(config_module)

        assert config_module.Config.enable_stealth is False

    def test_concurrency_is_positive(self):
        """Test that concurrency is a positive integer."""
        assert Config.crawl_concurrency > 0
