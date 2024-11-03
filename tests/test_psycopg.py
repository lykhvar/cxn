from unittest.mock import MagicMock, patch

import pytest

from cxn.providers import PsycopgProvider


@pytest.fixture
def psycopg_mock():
    with patch("cxn.providers.importlib.import_module") as mock_import_module:
        psycopg_module = MagicMock()
        psycopg_module.__version__ = "1.0"
        mock_import_module.return_value = psycopg_module
        yield psycopg_module


def test_valid_psycopg_connection(psycopg_mock):
    psycopg_mock.Connection().connect.return_value = None
    psycopg_instance = PsycopgProvider("postgresql://localhost:5672/")
    assert psycopg_instance.connection is True


def test_invalid_scheme(psycopg_mock):  # noqa: ARG001
    with pytest.raises(ValueError, match="Protocol amqp is not supported"):
        PsycopgProvider("amqp://localhost:5672/")


def test_invalid_url_pattern(psycopg_mock):  # noqa: ARG001
    with pytest.raises(ValueError, match="Invalid URL format"):
        PsycopgProvider("postgresql//localhost:5672/")


def test_invalid_port(psycopg_mock):  # noqa: ARG001
    with pytest.raises(ValueError, match="Port out of range 0-65535"):
        PsycopgProvider("postgresql://localhost:70000/")


def test_missing_required_module():
    with patch(
        "cxn.providers.importlib.import_module", side_effect=ImportError
    ):
        with pytest.raises(
            ImportError, match="Required module 'psycopg' is not installed"
        ):
            PsycopgProvider("postgresql://localhost:5672/")


def test_connection_failure(psycopg_mock):
    class MockOperationalError(Exception):
        pass

    psycopg_mock.OperationalError = MockOperationalError
    psycopg_mock.connect.side_effect = MockOperationalError
    psycopg_instance = PsycopgProvider("postgresql://localhost:5672/")
    assert psycopg_instance.connection is False


def test_module_version_issue(psycopg_mock):
    PsycopgProvider.require = "psycopg>=1.3"
    psycopg_mock.__version__ = "1.0"
    with pytest.raises(
        ImportError, match="does not satisfy the requirement 'psycopg>=1.3'"
    ):
        PsycopgProvider("postgresql://localhost:5672/")
