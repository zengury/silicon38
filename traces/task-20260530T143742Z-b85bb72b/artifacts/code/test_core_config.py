"""
Unit tests for core.config — centralized settings singleton.
"""

from core.config import settings


class TestCoreConfig:
    """Verify settings load correctly with environment-based values."""

    def test_settings_is_singleton(self):
        from core.config import settings as s2
        assert settings is s2

    def test_app_title(self):
        assert settings.APP_TITLE == "RAAS管理平台接口"

    def test_app_version(self):
        assert settings.APP_VERSION == "3.0.1"

    def test_api_prefix(self):
        assert settings.API_PREFIX == "/api/v1"

    def test_jwt_secret_exists(self):
        assert isinstance(settings.JWT_SECRET, str)
        assert len(settings.JWT_SECRET) > 0

    def test_jwt_algorithm(self):
        assert settings.JWT_ALGORITHM == "HS256"

    def test_access_token_expire_days(self):
        assert settings.ACCESS_TOKEN_EXPIRE_DAYS == 7

    def test_default_password(self):
        assert settings.DEFAULT_PASSWORD == "12345678"

    def test_environment(self):
        assert settings.ENVIRONMENT == "development"
        assert settings.is_development is True
        assert settings.is_production is False
