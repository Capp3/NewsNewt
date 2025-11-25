"""Integration tests for API endpoints."""

from unittest.mock import AsyncMock, patch

from newsnewt.archive import ArchiveFailureError, ArchiveTimeoutError
from newsnewt.extractor import ExtractionError


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_check_returns_200(self, test_client):
        """Test that health endpoint returns 200 OK."""
        response = test_client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestRootEndpoint:
    """Tests for root endpoint."""

    def test_root_returns_service_info(self, test_client):
        """Test that root endpoint returns service information."""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "NewsNewt"
        assert "version" in data
        assert "endpoints" in data


class TestArticleEndpoint:
    """Tests for POST /article endpoint."""

    def test_article_success_workflow(
        self, test_client, sample_article_url, sample_bbc_html
    ):
        """Test successful article processing workflow."""
        mock_archive_url = "https://archive.is/test123"

        with patch("newsnewt.api.archive_url", new_callable=AsyncMock) as mock_archive:
            with patch(
                "newsnewt.api.extract_article_content", new_callable=AsyncMock
            ) as mock_extract:
                # Configure mocks
                mock_archive.return_value = (mock_archive_url, sample_bbc_html)
                mock_extract.return_value = (
                    "Ukraine's foreign minister has called for a meeting..."
                )

                # Make request
                response = test_client.post(
                    "/article",
                    json={
                        "url": sample_article_url,
                        "force_archive": False,
                        "archive_service": "archive_is",
                    },
                )

                # Verify response
                assert response.status_code == 200
                data = response.json()
                assert data["url"] == sample_article_url
                assert data["archive_url"] == mock_archive_url
                assert len(data["body_text"]) > 0
                assert data["title"] is None  # MVP doesn't extract metadata

    def test_article_invalid_url_format(self, test_client):
        """Test handling of invalid URL format."""
        response = test_client.post(
            "/article",
            json={
                "url": "not-a-valid-url",
                "force_archive": False,
                "archive_service": "archive_is",
            },
        )

        # Pydantic validation should reject this
        assert response.status_code == 422

    def test_article_invalid_url_protocol(self, test_client):
        """Test handling of non-HTTP URL."""
        response = test_client.post(
            "/article",
            json={
                "url": "ftp://example.com/file.txt",
                "force_archive": False,
                "archive_service": "archive_is",
            },
        )

        # Pydantic catches this before our validation (422), which is fine
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_article_archive_timeout_error(self, test_client, sample_article_url):
        """Test handling of archive timeout (error mapping)."""
        with patch("newsnewt.api.archive_url", new_callable=AsyncMock) as mock_archive:
            # Simulate archive timeout
            mock_archive.side_effect = ArchiveTimeoutError(
                "Archive timed out after 60s"
            )

            response = test_client.post(
                "/article",
                json={
                    "url": sample_article_url,
                    "force_archive": False,
                    "archive_service": "archive_is",
                },
            )

            # Verify error is properly mapped
            assert response.status_code == 500
            data = response.json()
            assert data["detail"]["error"]["code"] == "ARCHIVE_TIMEOUT"
            assert "timed out" in data["detail"]["error"]["message"].lower()

    def test_article_archive_failure_error(self, test_client, sample_article_url):
        """Test handling of archive failure (error mapping)."""
        with patch("newsnewt.api.archive_url", new_callable=AsyncMock) as mock_archive:
            # Simulate archive failure
            mock_archive.side_effect = ArchiveFailureError(
                "Archive service unavailable"
            )

            response = test_client.post(
                "/article",
                json={
                    "url": sample_article_url,
                    "force_archive": False,
                    "archive_service": "archive_is",
                },
            )

            # Verify error is properly mapped
            assert response.status_code == 500
            data = response.json()
            assert data["detail"]["error"]["code"] == "ARCHIVE_FAILURE"
            assert "failed" in data["detail"]["error"]["message"].lower()

    def test_article_extraction_failure_error(
        self, test_client, sample_article_url, sample_bbc_html
    ):
        """Test handling of extraction failure (error mapping)."""
        mock_archive_url = "https://archive.is/test123"

        with patch("newsnewt.api.archive_url", new_callable=AsyncMock) as mock_archive:
            with patch(
                "newsnewt.api.extract_article_content", new_callable=AsyncMock
            ) as mock_extract:
                # Archive succeeds but extraction fails
                mock_archive.return_value = (mock_archive_url, sample_bbc_html)
                mock_extract.side_effect = ExtractionError("Empty body text")

                response = test_client.post(
                    "/article",
                    json={
                        "url": sample_article_url,
                        "force_archive": False,
                        "archive_service": "archive_is",
                    },
                )

                # Verify error is properly mapped
                assert response.status_code == 500
                data = response.json()
                assert data["detail"]["error"]["code"] == "EXTRACTION_FAILURE"
                assert "extraction" in data["detail"]["error"]["message"].lower()

    def test_article_unexpected_error_handling(self, test_client, sample_article_url):
        """Test handling of unexpected errors (error mapping)."""
        with patch("newsnewt.api.archive_url", new_callable=AsyncMock) as mock_archive:
            # Simulate unexpected error
            mock_archive.side_effect = RuntimeError("Unexpected problem")

            response = test_client.post(
                "/article",
                json={
                    "url": sample_article_url,
                    "force_archive": False,
                    "archive_service": "archive_is",
                },
            )

            # Verify error is properly mapped
            assert response.status_code == 500
            data = response.json()
            assert data["detail"]["error"]["code"] == "INTERNAL_ERROR"

    def test_article_with_force_archive_flag(
        self, test_client, sample_article_url, sample_bbc_html
    ):
        """Test that force_archive flag is passed correctly."""
        mock_archive_url = "https://archive.is/test123"

        with patch("newsnewt.api.archive_url", new_callable=AsyncMock) as mock_archive:
            with patch(
                "newsnewt.api.extract_article_content", new_callable=AsyncMock
            ) as mock_extract:
                mock_archive.return_value = (mock_archive_url, sample_bbc_html)
                mock_extract.return_value = "Test content"

                response = test_client.post(
                    "/article",
                    json={
                        "url": sample_article_url,
                        "force_archive": True,  # Force new archive
                        "archive_service": "archive_is",
                    },
                )

                assert response.status_code == 200
                # Verify force_archive was passed to archive_url
                mock_archive.assert_called_once()
                call_kwargs = mock_archive.call_args.kwargs
                assert call_kwargs["force_archive"] is True
