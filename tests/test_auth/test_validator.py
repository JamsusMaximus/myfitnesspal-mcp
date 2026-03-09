"""Tests for cookie validation."""

import json
from unittest.mock import MagicMock, patch

import pytest

from mfp_mcp.auth.validator import AuthStatus, _build_cookiejar, validate_auth, validate_auth_sync


class TestBuildCookiejar:
    def test_builds_jar(self):
        cookies = [
            {"name": "session", "value": "abc", "domain": ".myfitnesspal.com", "path": "/", "secure": True},
        ]
        jar = _build_cookiejar(json.dumps(cookies))
        cookie_list = list(jar)
        assert len(cookie_list) == 1
        assert cookie_list[0].name == "session"
        assert cookie_list[0].value == "abc"

    def test_empty_list(self):
        jar = _build_cookiejar("[]")
        assert len(list(jar)) == 0


class TestValidateAuthSync:
    def test_empty_input(self):
        result = validate_auth_sync("")
        assert result.status == AuthStatus.NO_CREDENTIAL

    def test_whitespace_input(self):
        result = validate_auth_sync("   ")
        assert result.status == AuthStatus.NO_CREDENTIAL

    @patch("mfp_mcp.auth.validator.requests.Session")
    def test_valid_session(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.headers = {"Content-Type": "application/json; charset=utf-8"}
        mock_resp.json.return_value = {
            "user": {"name": "testuser"},
            "userId": "12345",
        }
        mock_session.get.return_value = mock_resp

        cookies = json.dumps([{"name": "s", "value": "v", "domain": ".myfitnesspal.com"}])
        result = validate_auth_sync(cookies)
        assert result.is_valid
        assert result.username == "testuser"

    @patch("mfp_mcp.auth.validator.requests.Session")
    def test_expired_session(self, mock_session_cls):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        mock_resp = MagicMock()
        mock_resp.ok = True
        mock_resp.headers = {"Content-Type": "application/json; charset=utf-8"}
        mock_resp.json.return_value = {}  # Empty session = expired
        mock_session.get.return_value = mock_resp

        cookies = json.dumps([{"name": "s", "value": "v", "domain": ".myfitnesspal.com"}])
        result = validate_auth_sync(cookies)
        assert result.status == AuthStatus.EXPIRED


class TestValidateAuthAsync:
    @pytest.mark.asyncio
    async def test_empty_input(self):
        result = await validate_auth("")
        assert result.status == AuthStatus.NO_CREDENTIAL
