"""mfp_auth_status - Check authentication status."""

from typing import Any

from mfp_mcp.auth import AuthStatus, get_credential, get_storage_backend, validate_auth


async def mfp_auth_status() -> dict[str, Any]:
    """Check MyFitnessPal authentication status.

    Returns:
        Dict with auth status, username if valid, and any action needed.
    """
    cred = get_credential()

    if not cred.success or not cred.cookies:
        return {
            "valid": False,
            "username": None,
            "message": "No credential stored",
            "action_needed": "Run 'mfp-mcp auth' to authenticate",
        }

    result = await validate_auth(cred.cookies)

    if result.is_valid:
        return {
            "valid": True,
            "username": result.username,
            "storage": get_storage_backend(),
            "message": "Authentication valid",
            "action_needed": None,
        }

    action_map = {
        AuthStatus.EXPIRED: "Session expired. Run 'mfp-mcp auth' to re-authenticate.",
        AuthStatus.INVALID: "Invalid credentials. Run 'mfp-mcp auth' to re-authenticate.",
        AuthStatus.NETWORK_ERROR: "Network error. Check connection and retry.",
    }

    return {
        "valid": False,
        "username": None,
        "message": result.message,
        "action_needed": action_map.get(result.status, "Run 'mfp-mcp auth' to authenticate"),
    }
