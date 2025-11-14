"""Tests for the health check endpoint."""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from fastapi.testclient import TestClient

from eduscale.main import app

client = TestClient(app)


def test_health_endpoint():
    """Test that the health endpoint returns correct response."""
    response = client.get("/health")

    # Assert status code is 200
    assert response.status_code == 200

    # Parse JSON response
    data = response.json()

    # Assert response contains required keys
    assert "status" in data
    assert "service" in data
    assert "version" in data

    # Assert status field equals "ok"
    assert data["status"] == "ok"


def test_health_endpoint_values():
    """Test that the health endpoint returns expected values."""
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    # Verify expected values
    assert data["service"] == "eduscale-engine"
    assert data["version"] == "0.1.0"
