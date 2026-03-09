"""mfp_get_profile - Get user profile and preferences."""

import logging
from typing import Any

from mfp_mcp.client import MFPClient
from mfp_mcp.client.mfp import MFPClientError

logger = logging.getLogger("mfp-mcp")


async def mfp_get_profile() -> dict[str, Any]:
    """Get MFP user profile information.

    Returns:
        Dict with username and available metadata.
    """
    try:
        client = MFPClient()
        metadata = await client.get_user_metadata()
        return {
            "username": metadata.get("user_name") or metadata.get("username"),
            "metadata": metadata,
        }
    except MFPClientError as e:
        return {
            "isError": True,
            "error_code": e.error_code,
            "message": str(e),
        }
    except Exception:
        logger.exception("Error fetching profile")
        return {
            "isError": True,
            "error_code": "API_ERROR",
            "message": "Failed to fetch profile. Check server logs.",
        }
