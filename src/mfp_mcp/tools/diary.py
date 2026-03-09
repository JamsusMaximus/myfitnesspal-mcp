"""mfp_get_diary - Get food diary for a single date."""

import logging
from typing import Any

from pydantic import ValidationError

from mfp_mcp.client import MFPClient
from mfp_mcp.client.mfp import MFPClientError
from mfp_mcp.tools._validation import DateInput, format_validation_error

logger = logging.getLogger("mfp-mcp")


async def mfp_get_diary(date_str: str) -> dict[str, Any]:
    """Get food diary for a specific date.

    Args:
        date_str: Date in YYYY-MM-DD format.

    Returns:
        Dict with date, meals, totals, goals, water, notes.
    """
    try:
        validated = DateInput(date=date_str)
    except ValidationError as e:
        return {
            "isError": True,
            "error_code": "VALIDATION_ERROR",
            "message": format_validation_error(e),
        }

    try:
        client = MFPClient()
        return await client.get_diary(validated.date)
    except MFPClientError as e:
        return {
            "isError": True,
            "error_code": e.error_code,
            "message": str(e),
        }
    except Exception:
        logger.exception("Error fetching diary")
        return {
            "isError": True,
            "error_code": "API_ERROR",
            "message": "Failed to fetch diary. Check server logs.",
        }
