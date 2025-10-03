"""Basic health check test for CI/CD pipeline."""
import pytest


def test_basic():
    """Placeholder test to prevent pytest from failing."""
    assert True


def test_imports():
    """Test that core modules can be imported."""
    try:
        from app.main import app
        from app.core.config import settings
        assert app is not None
        assert settings is not None
    except Exception as e:
        pytest.fail(f"Failed to import core modules: {e}")

