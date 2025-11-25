"""Unit tests for utils module."""

from newsnewt.utils import extract_domain, resolve_archive_service, validate_url


class TestValidateUrl:
    """Tests for URL validation."""

    def test_valid_http_url(self):
        """Test validation of valid HTTP URL."""
        is_valid, error = validate_url("http://example.com")
        assert is_valid is True
        assert error is None

    def test_valid_https_url(self):
        """Test validation of valid HTTPS URL."""
        is_valid, error = validate_url("https://example.com")
        assert is_valid is True
        assert error is None

    def test_valid_url_with_path(self):
        """Test validation of URL with path."""
        is_valid, error = validate_url("https://example.com/article/123")
        assert is_valid is True
        assert error is None

    def test_valid_url_with_query(self):
        """Test validation of URL with query parameters."""
        is_valid, error = validate_url("https://example.com/article?id=123")
        assert is_valid is True
        assert error is None

    def test_invalid_empty_url(self):
        """Test validation of empty URL."""
        is_valid, error = validate_url("")
        assert is_valid is False
        assert "non-empty string" in error

    def test_invalid_non_http_protocol(self):
        """Test validation of non-HTTP protocol."""
        is_valid, error = validate_url("ftp://example.com")
        assert is_valid is False
        assert "valid http or https URL" in error

    def test_invalid_no_protocol(self):
        """Test validation of URL without protocol."""
        is_valid, error = validate_url("example.com")
        assert is_valid is False
        assert "valid http or https URL" in error

    def test_invalid_malformed_url(self):
        """Test validation of malformed URL."""
        is_valid, error = validate_url("ht!tp://not-a-url")
        assert is_valid is False
        assert error is not None


class TestExtractDomain:
    """Tests for domain extraction."""

    def test_extract_domain_simple(self):
        """Test extracting domain from simple URL."""
        domain = extract_domain("https://example.com")
        assert domain == "example.com"

    def test_extract_domain_with_www(self):
        """Test extracting domain with www."""
        domain = extract_domain("https://www.example.com")
        assert domain == "www.example.com"

    def test_extract_domain_with_path(self):
        """Test extracting domain from URL with path."""
        domain = extract_domain("https://example.com/article/123")
        assert domain == "example.com"

    def test_extract_domain_with_subdomain(self):
        """Test extracting domain with subdomain."""
        domain = extract_domain("https://news.example.com")
        assert domain == "news.example.com"

    def test_extract_domain_invalid_url(self):
        """Test extracting domain from invalid URL."""
        domain = extract_domain("not-a-url")
        # Invalid URLs return empty string or None
        assert domain in ("", None)


class TestResolveArchiveService:
    """Tests for archive service resolution."""

    def test_resolve_auto_returns_archive_is(self):
        """Test that 'auto' resolves to 'archive_is'."""
        service = resolve_archive_service("auto")
        assert service == "archive_is"

    def test_resolve_archive_is(self):
        """Test that 'archive_is' stays as 'archive_is'."""
        service = resolve_archive_service("archive_is")
        assert service == "archive_is"

    def test_resolve_archive_today_to_archive_is(self):
        """Test that 'archive_today' normalizes to 'archive_is'."""
        service = resolve_archive_service("archive_today")
        # archive_today is normalized to archive_is (same service)
        assert service == "archive_is"

    def test_resolve_invalid_service_returns_as_is(self):
        """Test that invalid service is returned as-is (validated elsewhere)."""
        service = resolve_archive_service("invalid_service")
        # Invalid services are returned as-is and validated in config/API layer
        assert service == "invalid_service"

    def test_resolve_none_returns_as_is(self):
        """Test that None is returned as-is."""
        service = resolve_archive_service(None)
        assert service is None

    def test_resolve_empty_string_returns_as_is(self):
        """Test that empty string is returned as-is."""
        service = resolve_archive_service("")
        assert service == ""
