from unittest.mock import MagicMock, patch

import pytest

from cxn.providers import RedisProvider


@pytest.fixture
def redis_mock():
    with patch("cxn.providers.importlib.import_module") as mock_import_module:
        redis_module = MagicMock()
        redis_module.__version__ = "2.0"
        mock_import_module.return_value = redis_module
        redis_module.exceptions.ConnectionError = Exception
        yield redis_module


def test_valid_redis_connection(redis_mock):
    connection_mock = MagicMock()
    redis_mock.from_url.return_value = connection_mock
    connection_mock.ping.return_value = True
    redis_instance = RedisProvider("redis://localhost:5672/")
    assert redis_instance.connection is True


def test_invalid_scheme(redis_mock):  # noqa: ARG001
    with pytest.raises(ValueError, match="Protocol http is not supported"):
        RedisProvider("http://localhost:5672/")


def test_invalid_url_pattern(redis_mock):  # noqa: ARG001
    with pytest.raises(ValueError, match="Invalid URL format"):
        RedisProvider("redis//localhost:5672/")


def test_invalid_port(redis_mock):  # noqa: ARG001
    with pytest.raises(ValueError, match="Port out of range 0-65535"):
        RedisProvider("redis://localhost:70000/")


def test_missing_required_module():
    with patch(
        "cxn.providers.importlib.import_module", side_effect=ImportError
    ):
        with pytest.raises(
            ImportError, match="Required module 'redis' is not installed"
        ):
            RedisProvider("redis://localhost:5672/")


def test_connection_failure(redis_mock):
    connection_mock = MagicMock()
    connection_mock.ping.side_effect = redis_mock.exceptions.ConnectionError
    redis_mock.from_url.return_value = connection_mock
    redis_instance = RedisProvider("redis://localhost:5672/")
    assert redis_instance.connection is False


def test_module_version_issue(redis_mock):
    RedisProvider.require = "redis>=1.3"
    redis_mock.__version__ = "1.0"
    with pytest.raises(
        ImportError, match="does not satisfy the requirement 'redis>=1.3'"
    ):
        RedisProvider("redis://localhost:5672/")
