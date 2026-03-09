"""mfp_refresh_auth - Refresh authentication from browser.

SECURITY NOTES:
- Cookie values are NEVER included in the return dict (would leak to Claude)
- Only returns: success status, browser name, username
- Cookies are stored directly via store_credential(), never passed through return
"""

from typing import Any

from mfp_mcp.auth import store_credential, validate_auth
from mfp_mcp.auth.browser import extract_mfp_cookies
from mfp_mcp.client.mfp import MFPClient


def _sanitize_result(result: dict[str, Any]) -> dict[str, Any]:
    """SECURITY: Ensure no cookie values in result dict before returning to Claude."""
    sensitive_keys = ["cookie", "token", "auth", "credential", "password", "secret"]
    sanitized = {}
    for key, value in result.items():
        key_lower = key.lower()
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            continue
        sanitized[key] = value
    return sanitized


async def mfp_refresh_auth(browser: str = "auto") -> dict[str, Any]:
    """Refresh MFP authentication by extracting cookies from browser.

    Args:
        browser: Browser to extract from (chrome, firefox, safari, edge, auto).

    Returns:
        Dict with success status and message.
    """
    result = extract_mfp_cookies(browser if browser != "auto" else None)

    if not result.success:
        if "not installed" in result.message:
            return {
                "success": False,
                "message": "Browser extraction not available",
                "details": "The browser-cookie3 package is not installed.",
                "action_needed": "Run: pip install mfp-mcp[browser]",
            }

        return {
            "success": False,
            "message": "Could not extract cookies from browser",
            "details": result.message,
            "action_needed": (
                "Make sure you're logged into MyFitnessPal at www.myfitnesspal.com "
                "in your browser, then try again. Or run 'mfp-mcp auth' manually."
            ),
        }

    cookies = result.cookies
    validation = await validate_auth(cookies)

    if not validation.is_valid:
        return {
            "success": False,
            "message": "Extracted cookies are invalid or expired",
            "details": validation.message,
            "action_needed": "Log into MyFitnessPal at www.myfitnesspal.com in your browser, then try again.",
        }

    store_result = store_credential(cookies)

    if not store_result.success:
        return {
            "success": False,
            "message": "Could not store the refreshed cookies",
            "details": store_result.message,
            "action_needed": "Run 'mfp-mcp auth' manually.",
        }

    # Clear cached client so it picks up new cookies
    MFPClient._clear_cache()

    return _sanitize_result({
        "success": True,
        "message": f"Authentication refreshed from {result.browser}",
        "username": validation.username,
        "action_needed": None,
    })
