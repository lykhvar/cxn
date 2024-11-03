import socket
from unittest.mock import MagicMock, patch

import pytest

from cxn.providers import KombuProvider


@pytest.fixture
def kombu_mock():
    with patch("cxn.providers.importlib.import_module") as mock_import_module:
        kombu_module = MagicMock()
        kombu_module.__version__ = "2.0"
        mock_import_module.return_value = kombu_module
        yield kombu_module


def test_valid_kombu_connection(kombu_mock):
    kombu_mock.Connection().connect.return_value = None
    kombu_instance = KombuProvider("amqp://localhost:5672/")
    assert kombu_instance.connection is True


def test_invalid_scheme(kombu_mock):  # noqa: ARG001
    with pytest.raises(ValueError, match="Protocol http is not supported"):
        KombuProvider("http://localhost:5672/")


def test_invalid_url_pattern(kombu_mock):  # noqa: ARG001
    with pytest.raises(ValueError, match="Invalid URL format"):
        KombuProvider("amqp//localhost:5672/")


def test_invalid_port(kombu_mock):  # noqa: ARG001
    with pytest.raises(ValueError, match="Port out of range 0-65535"):
        KombuProvider("amqp://localhost:70000/")


def test_missing_required_module():
    with patch(
        "cxn.providers.importlib.import_module", side_effect=ImportError
    ):
        with pytest.raises(
            ImportError, match="Required module 'kombu' is not installed"
        ):
            KombuProvider("amqp://localhost:5672/")


def test_connection_failure(kombu_mock):
    kombu_mock.Connection().connect.side_effect = socket.error
    kombu_instance = KombuProvider("amqp://localhost:5672/")
    assert kombu_instance.connection is False


def test_module_version_issue(kombu_mock):
    KombuProvider.require = "kombu>=1.3"
    kombu_mock.__version__ = "1.0"
    with pytest.raises(
        ImportError, match="does not satisfy the requirement 'kombu>=1.3'"
    ):
        KombuProvider("amqp://localhost:5672/")
