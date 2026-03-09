"""Tests for diary tool."""

from unittest.mock import AsyncMock, patch

import pytest

from mfp_mcp.tools.diary import mfp_get_diary


class TestMfpGetDiary:
    @pytest.mark.asyncio
    async def test_invalid_date(self):
        result = await mfp_get_diary("not-a-date")
        assert result["isError"]
        assert result["error_code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    @patch("mfp_mcp.tools.diary.MFPClient")
    async def test_success(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_client.get_diary = AsyncMock(return_value={
            "date": "2026-03-09",
            "meals": [],
            "totals": {"calories": 2000},
            "goals": {"calories": 2500},
            "water": 8.0,
            "notes": "",
        })

        result = await mfp_get_diary("2026-03-09")
        assert not result.get("isError")
        assert result["date"] == "2026-03-09"

    @pytest.mark.asyncio
    @patch("mfp_mcp.tools.diary.MFPClient")
    async def test_auth_error(self, mock_client_cls):
        from mfp_mcp.client.mfp import MFPClientError
        mock_client = mock_client_cls.return_value
        mock_client.get_diary = AsyncMock(
            side_effect=MFPClientError("No credentials", error_code="AUTH_REQUIRED")
        )

        result = await mfp_get_diary("2026-03-09")
        assert result["isError"]
        assert result["error_code"] == "AUTH_REQUIRED"
