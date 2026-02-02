"""Tests for health check endpoint."""


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_check_returns_200(self, test_client):
        """Test that health check returns 200 status code."""
        response = test_client.get("/health")

        assert response.status_code == 200

    def test_health_check_returns_ok(self, test_client):
        """Test that health check returns ok status."""
        response = test_client.get("/health")
        data = response.json()

        assert data["status"] == "ok"

    def test_health_check_content_type(self, test_client):
        """Test that health check returns JSON."""
        response = test_client.get("/health")

        assert response.headers["content-type"] == "application/json"

    def test_health_check_no_parameters(self, test_client):
        """Test that health check works without parameters."""
        response = test_client.get("/health")

        assert response.status_code == 200
        assert "status" in response.json()
