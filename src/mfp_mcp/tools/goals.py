"""mfp_get_goals - Get nutrition goals."""

import logging
from datetime import date
from typing import Any

from mfp_mcp.client import MFPClient
from mfp_mcp.client.mfp import MFPClientError

logger = logging.getLogger("mfp-mcp")


async def mfp_get_goals() -> dict[str, Any]:
    """Get the user's nutrition goals.

    Returns:
        Dict with calorie and macro goals.
    """
    try:
        client = MFPClient()
        # Goals are included in the diary response for any date
        diary = await client.get_diary(date.today())
        return {
            "goals": diary.get("goals", {}),
            "message": "Goals retrieved from today's diary",
        }
    except MFPClientError as e:
        return {
            "isError": True,
            "error_code": e.error_code,
            "message": str(e),
        }
    except Exception:
        logger.exception("Error fetching goals")
        return {
            "isError": True,
            "error_code": "API_ERROR",
            "message": "Failed to fetch goals. Check server logs.",
        }
