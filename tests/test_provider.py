from unittest.mock import MagicMock, patch

import pytest

from cxn.providers import Provider


class MockProvider(Provider):
    require = "mockmodule>=1.0.0,<2.0.0"
    connection = None
    schemas = ("test",)


def get_mock_provider(return_value=None):
    with patch.object(MockProvider, "connection", return_value=return_value):
        return MockProvider("test://localhost:27017/test")


def test_valid_module_version():
    with patch("cxn.providers.importlib.import_module") as mock_import:
        mock_module = MagicMock()
        mock_module.__version__ = "1.5.0"
        mock_import.return_value = mock_module

        provider = get_mock_provider()
        assert provider is not None


def test_invalid_module_version():
    with patch("cxn.providers.importlib.import_module") as mock_import:
        mock_module = MagicMock()
        mock_module.__version__ = "2.5.0"
        mock_import.return_value = mock_module

        with pytest.raises(
            ImportError, match="does not satisfy the requirement"
        ):
            get_mock_provider()


def test_missing_module():
    with patch(
        "cxn.providers.importlib.import_module",
        side_effect=ImportError("Module not found"),
    ):
        with pytest.raises(
            ImportError, match="Required module 'mockmodule' is not installed"
        ):
            get_mock_provider()


def test_module_without_version():
    with patch("cxn.providers.importlib.import_module") as mock_import:
        mock_module = MagicMock()
        del mock_module.__version__
        mock_import.return_value = mock_module

        with pytest.raises(
            ImportError,
            match="Unable to determine version of the 'mockmodule' module",
        ):
            get_mock_provider()


def test_module_version_storage():
    with patch("cxn.providers.importlib.import_module") as mock_import:
        mock_module = MagicMock()
        mock_module.__version__ = "1.5.0"
        mock_import.return_value = mock_module
        provider = get_mock_provider()

        assert provider.module == mock_module
        assert provider.module.__version__ == "1.5.0"
