"""mfp_get_measurements - Get body measurements over time."""

import logging
from typing import Any

from pydantic import ValidationError

from mfp_mcp.client import MFPClient
from mfp_mcp.client.mfp import MFPClientError
from mfp_mcp.tools._validation import MeasurementInput, format_validation_error

logger = logging.getLogger("mfp-mcp")


async def mfp_get_measurements(
    measurement: str = "Weight",
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Get body measurements over time.

    Args:
        measurement: Measurement type (e.g. Weight, Body Fat).
        start_date: Start date in YYYY-MM-DD format (optional).
        end_date: End date in YYYY-MM-DD format (optional).

    Returns:
        Dict with measurement entries.
    """
    try:
        validated = MeasurementInput(
            measurement=measurement,
            start_date=start_date,
            end_date=end_date,
        )
    except ValidationError as e:
        return {
            "isError": True,
            "error_code": "VALIDATION_ERROR",
            "message": format_validation_error(e),
        }

    try:
        client = MFPClient()
        entries = await client.get_measurements(
            measurement=validated.measurement,
            start_date=validated.start_date,
            end_date=validated.end_date,
        )
        return {
            "measurement": validated.measurement,
            "entries": entries,
            "count": len(entries),
        }
    except MFPClientError as e:
        return {
            "isError": True,
            "error_code": e.error_code,
            "message": str(e),
        }
    except Exception:
        logger.exception("Error fetching measurements")
        return {
            "isError": True,
            "error_code": "API_ERROR",
            "message": "Failed to fetch measurements. Check server logs.",
        }
