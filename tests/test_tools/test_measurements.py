"""Tests for measurements tool."""

from unittest.mock import AsyncMock, patch

import pytest

from mfp_mcp.tools.measurements import mfp_get_measurements


class TestMfpGetMeasurements:
    @pytest.mark.asyncio
    async def test_invalid_date_range(self):
        result = await mfp_get_measurements(
            start_date="2026-03-10",
            end_date="2026-03-01",
        )
        assert result["isError"]
        assert result["error_code"] == "VALIDATION_ERROR"

    @pytest.mark.asyncio
    @patch("mfp_mcp.tools.measurements.MFPClient")
    async def test_success(self, mock_client_cls):
        mock_client = mock_client_cls.return_value
        mock_client.get_measurements = AsyncMock(return_value=[
            {"date": "2026-03-01", "value": 70.0},
            {"date": "2026-03-08", "value": 69.5},
        ])

        result = await mfp_get_measurements()
        assert not result.get("isError")
        assert result["count"] == 2
        assert result["measurement"] == "Weight"
