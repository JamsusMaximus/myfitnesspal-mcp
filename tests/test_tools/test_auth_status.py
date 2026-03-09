"""Tests for auth_status tool."""

from unittest.mock import AsyncMock, patch

import pytest

from mfp_mcp.auth.keyring import CredentialResult
from mfp_mcp.auth.validator import AuthResult, AuthStatus
from mfp_mcp.tools.auth_status import mfp_auth_status


class TestMfpAuthStatus:
    @pytest.mark.asyncio
    @patch("mfp_mcp.tools.auth_status.get_credential")
    async def test_no_credential(self, mock_get_cred):
        mock_get_cred.return_value = CredentialResult(success=False, message="none")
        result = await mfp_auth_status()
        assert not result["valid"]
        assert "action_needed" in result

    @pytest.mark.asyncio
    @patch("mfp_mcp.tools.auth_status.validate_auth", new_callable=AsyncMock)
    @patch("mfp_mcp.tools.auth_status.get_credential")
    async def test_valid(self, mock_get_cred, mock_validate):
        mock_get_cred.return_value = CredentialResult(success=True, message="ok", cookies="data")
        mock_validate.return_value = AuthResult(
            status=AuthStatus.VALID, username="testuser"
        )
        result = await mfp_auth_status()
        assert result["valid"]
        assert result["username"] == "testuser"

    @pytest.mark.asyncio
    @patch("mfp_mcp.tools.auth_status.validate_auth", new_callable=AsyncMock)
    @patch("mfp_mcp.tools.auth_status.get_credential")
    async def test_expired(self, mock_get_cred, mock_validate):
        mock_get_cred.return_value = CredentialResult(success=True, message="ok", cookies="data")
        mock_validate.return_value = AuthResult(
            status=AuthStatus.EXPIRED, message="Session expired"
        )
        result = await mfp_auth_status()
        assert not result["valid"]
        assert "expired" in result["action_needed"].lower()
