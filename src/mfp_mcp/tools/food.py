"""mfp_search_food and mfp_get_food_details - Food database tools."""

import logging
from typing import Any

from pydantic import ValidationError

from mfp_mcp.client import MFPClient
from mfp_mcp.client.mfp import MFPClientError
from mfp_mcp.tools._validation import FoodSearchInput, format_validation_error

logger = logging.getLogger("mfp-mcp")


async def mfp_search_food(query: str) -> dict[str, Any]:
    """Search the MFP food database.

    Args:
        query: Search query string.

    Returns:
        Dict with search results.
    """
    try:
        validated = FoodSearchInput(query=query)
    except ValidationError as e:
        return {
            "isError": True,
            "error_code": "VALIDATION_ERROR",
            "message": format_validation_error(e),
        }

    try:
        client = MFPClient()

        # The myfitnesspal library doesn't have a direct search method
        # that returns structured results. We'll note this limitation.
        return {
            "isError": True,
            "error_code": "NOT_IMPLEMENTED",
            "message": (
                f"Food search for '{validated.query}' is not yet supported. "
                "The myfitnesspal library does not expose a food search API."
            ),
        }
    except MFPClientError as e:
        return {
            "isError": True,
            "error_code": e.error_code,
            "message": str(e),
        }


async def mfp_get_food_details(mfp_id: int) -> dict[str, Any]:
    """Get detailed nutrition info for a food item.

    Args:
        mfp_id: MFP food item ID.

    Returns:
        Dict with food details and nutrition.
    """
    try:
        client = MFPClient()

        return {
            "isError": True,
            "error_code": "NOT_IMPLEMENTED",
            "message": (
                f"Food details for ID {mfp_id} is not yet supported. "
                "The myfitnesspal library does not expose a food detail API."
            ),
        }
    except MFPClientError as e:
        return {
            "isError": True,
            "error_code": e.error_code,
            "message": str(e),
        }
