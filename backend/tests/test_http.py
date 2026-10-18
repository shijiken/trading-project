from unittest.mock import MagicMock

import pytest
import requests

import services.http as http


def _resp(status=200):
    m = MagicMock()
    m.status_code = status
    m.raise_for_status.return_value = None
    return m


def test_returns_response_on_first_success(monkeypatch):
    mock_get = MagicMock(return_value=_resp())
    monkeypatch.setattr(http.requests, "get", mock_get)

    assert http.get_with_retry("http://x") is mock_get.return_value
    assert mock_get.call_count == 1


def test_retries_transient_server_errors_then_succeeds(monkeypatch):
    mock_get = MagicMock(side_effect=[_resp(503), _resp(500), _resp(200)])
    monkeypatch.setattr(http.requests, "get", mock_get)
    monkeypatch.setattr(http.time, "sleep", lambda s: None)

    resp = http.get_with_retry("http://x")

    assert resp.status_code == 200
    assert mock_get.call_count == 3


def test_retries_timeouts(monkeypatch):
    mock_get = MagicMock(side_effect=[requests.Timeout("slow"), _resp(200)])
    monkeypatch.setattr(http.requests, "get", mock_get)
    monkeypatch.setattr(http.time, "sleep", lambda s: None)

    assert http.get_with_retry("http://x").status_code == 200
    assert mock_get.call_count == 2


def test_gives_up_after_max_attempts(monkeypatch):
    mock_get = MagicMock(side_effect=requests.ConnectionError("down"))
    monkeypatch.setattr(http.requests, "get", mock_get)
    monkeypatch.setattr(http.time, "sleep", lambda s: None)

    with pytest.raises(requests.ConnectionError):
        http.get_with_retry("http://x")

    assert mock_get.call_count == http.MAX_ATTEMPTS


def test_does_not_retry_client_errors(monkeypatch):
    resp = _resp(404)
    resp.raise_for_status.side_effect = requests.HTTPError("not found")
    mock_get = MagicMock(return_value=resp)
    monkeypatch.setattr(http.requests, "get", mock_get)

    with pytest.raises(requests.HTTPError):
        http.get_with_retry("http://x")

    # a 404 won't fix itself — no point burning retries on it
    assert mock_get.call_count == 1
