import logging
from unittest.mock import MagicMock, PropertyMock, patch
from urllib.parse import urlparse

import pytest

from cxn.__about__ import __version__
from cxn.cli import main


def test_cli_version(monkeypatch, capsys):
    monkeypatch.setattr("sys.argv", ["cxn", "--version"])

    with pytest.raises(SystemExit):
        main()

    captured = capsys.readouterr()
    assert f"cxn {__version__}" in captured.out


def test_terminate_exits(monkeypatch, caplog):
    provider = MagicMock
    provider.connection = False
    provider.uri = urlparse("test://localhost:27017/db")
    monkeypatch.setattr("sys.argv", ["cxn", "-t", "test", "--url", "test"])
    monkeypatch.setattr("cxn.providers.registry.get", lambda name: provider)

    with pytest.raises(SystemExit) as excinfo:
        main()

    captured = caplog.text
    assert "No connection" in captured
    assert excinfo.value.code == 1


def test_failure_exit(monkeypatch, caplog):
    provider = MagicMock
    provider.connection = False
    provider.uri = urlparse("test://localhost:27017/db")
    monkeypatch.setattr("sys.argv", ["cxn", "test", "-u", "test"])
    monkeypatch.setattr("cxn.providers.registry.get", lambda name: provider)

    with caplog.at_level(logging.INFO):
        with pytest.raises(SystemExit) as excinfo:
            main()

    captured = caplog.text
    assert "No connection" in captured
    assert excinfo.value.code == 0


def test_success_exits(monkeypatch, caplog):
    provider = MagicMock
    provider.connection = True
    provider.uri = urlparse("test://localhost:27017/db")
    monkeypatch.setattr("sys.argv", ["cxn", "test", "--url", "test"])
    monkeypatch.setattr("cxn.providers.registry.get", lambda name: provider)

    with caplog.at_level(logging.INFO):
        with pytest.raises(SystemExit) as excinfo:
            main()

    captured = caplog.text
    assert "Ok" in captured
    assert excinfo.value.code == 0


def test_backoff(monkeypatch, caplog):
    provider = MagicMock
    provider.connection = PropertyMock(
        side_effect=[False, False, False, False, True]
    )
    provider.uri = urlparse("test://localhost:27017/db")
    monkeypatch.setattr("sys.argv", ["cxn", "test", "-u", "test", "-b"])
    monkeypatch.setattr("cxn.providers.registry.get", lambda name: provider)

    with patch("time.sleep") as mocked_sleep, caplog.at_level(logging.INFO):
        with pytest.raises(SystemExit) as excinfo:
            main()

        mocked_sleep.assert_any_call(1)
        mocked_sleep.assert_any_call(2)
        mocked_sleep.assert_any_call(4)
        mocked_sleep.assert_any_call(8)

    captured = caplog.text

    assert "Retrying in 1 seconds..." in captured
    assert "Retrying in 2 seconds..." in captured
    assert "Retrying in 4 seconds..." in captured
    assert "Retrying in 8 seconds..." in captured
    assert "Ok" in captured
    assert excinfo.value.code == 0


def test_backoff_retry(monkeypatch, caplog):
    provider = MagicMock
    provider.connection = PropertyMock(
        side_effect=[False, False, False, False]
    )
    provider.uri = urlparse("test://localhost:27017/db")
    monkeypatch.setattr(
        "sys.argv", ["cxn", "test", "-u", "test", "-bt", "-r", "2"]
    )
    monkeypatch.setattr("cxn.providers.registry.get", lambda name: provider)

    with patch("time.sleep") as mocked_sleep, caplog.at_level(logging.INFO):
        with pytest.raises(SystemExit) as excinfo:
            main()

        mocked_sleep.assert_any_call(1)
        mocked_sleep.assert_any_call(2)
        assert mocked_sleep.call_count == 2

    captured = caplog.text

    assert "Retrying in 1 seconds..." in captured
    assert "Retrying in 2 seconds..." in captured
    assert excinfo.value.code == 1
