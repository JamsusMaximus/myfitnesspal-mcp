"""Tests for MFPClient wrapper."""

import json
from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from mfp_mcp.auth.keyring import CredentialResult
from mfp_mcp.client.mfp import MFPClient, MFPClientError, _create_mfp_client


class TestMFPClientError:
    def test_error_code(self):
        err = MFPClientError("test", error_code="AUTH_EXPIRED")
        assert err.error_code == "AUTH_EXPIRED"
        assert str(err) == "test"


class TestCreateMfpClient:
    @patch("mfp_mcp.client.mfp.requests.Session")
    def test_successful_creation(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.json.return_value = {
            "user": {"name": "testuser"},
            "userId": "123",
        }
        mock_session.get.return_value = mock_resp

        from http.cookiejar import CookieJar
        jar = CookieJar()
        client = _create_mfp_client(jar)
        assert client.effective_username == "testuser"

    @patch("mfp_mcp.client.mfp.requests.Session")
    def test_failed_session(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_resp = MagicMock()
        mock_resp.ok = False
        mock_resp.status_code = 403
        mock_resp.headers = {"Content-Type": "text/html"}
        mock_session.get.return_value = mock_resp

        from http.cookiejar import CookieJar
        with pytest.raises(MFPClientError, match="authenticate"):
            _create_mfp_client(CookieJar())


class TestMFPClient:
    def setup_method(self):
        MFPClient._clear_cache()

    def test_clear_cache(self):
        MFPClient._shared_client = "something"
        MFPClient._clear_cache()
        assert MFPClient._shared_client is None

    @patch("mfp_mcp.client.mfp.get_credential")
    def test_no_credentials(self, mock_get_cred):
        mock_get_cred.return_value = CredentialResult(success=False, message="none")
        client = MFPClient()
        with pytest.raises(MFPClientError, match="No credentials"):
            client._get_sync_client()
