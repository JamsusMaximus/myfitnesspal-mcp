"""Cookie validation for MyFitnessPal authentication.

Validates stored cookies by hitting MFP's NextAuth session endpoint.
The old /user/auth_token endpoint is blocked by MFP's WAF, so we use
/api/auth/session which works with standard requests + browser cookies.
"""

import asyncio
import json
from dataclasses import dataclass
from enum import Enum
from http.cookiejar import Cookie, CookieJar

import requests


NEXTAUTH_SESSION_URL = "https://www.myfitnesspal.com/api/auth/session"


class AuthStatus(Enum):
    """Authentication status codes."""

    VALID = "valid"
    EXPIRED = "expired"
    INVALID = "invalid"
    NETWORK_ERROR = "network_error"
    NO_CREDENTIAL = "no_credential"


@dataclass
class AuthResult:
    """Result of authentication validation."""

    status: AuthStatus
    username: str | None = None
    message: str = ""

    @property
    def is_valid(self) -> bool:
        return self.status == AuthStatus.VALID


def _build_cookiejar(cookies_json: str) -> CookieJar:
    """Build a CookieJar from serialised JSON cookie data."""
    cookies = json.loads(cookies_json)
    jar = CookieJar()
    for c in cookies:
        cookie = Cookie(
            version=0,
            name=c["name"],
            value=c["value"],
            port=None,
            port_specified=False,
            domain=c.get("domain", ".myfitnesspal.com"),
            domain_specified=True,
            domain_initial_dot=c.get("domain", ".myfitnesspal.com").startswith("."),
            path=c.get("path", "/"),
            path_specified=True,
            secure=c.get("secure", False),
            expires=None,
            discard=True,
            comment=None,
            comment_url=None,
            rest={},
        )
        jar.set_cookie(cookie)
    return jar


def _validate_sync(cookies_json: str) -> AuthResult:
    """Validate MFP cookies by hitting the NextAuth session endpoint."""
    try:
        jar = _build_cookiejar(cookies_json)

        session = requests.Session()
        session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            )
        })
        session.cookies.update(jar)

        resp = session.get(NEXTAUTH_SESSION_URL, timeout=10)

        if not resp.ok:
            return AuthResult(
                status=AuthStatus.EXPIRED,
                message=f"MFP returned status {resp.status_code}. Please re-authenticate.",
            )

        if not resp.headers.get("Content-Type", "").startswith("application/json"):
            return AuthResult(
                status=AuthStatus.INVALID,
                message="Unexpected response from MFP. Cookies may be invalid.",
            )

        data = resp.json()
        username = data.get("user", {}).get("name")

        if username:
            return AuthResult(
                status=AuthStatus.VALID,
                username=username,
                message="Authentication valid",
            )

        # Empty session response means not authenticated
        if not data.get("user"):
            return AuthResult(
                status=AuthStatus.EXPIRED,
                message="Session expired. Please re-authenticate.",
            )

        return AuthResult(
            status=AuthStatus.VALID,
            username=None,
            message="Authentication valid (username not found in session)",
        )

    except requests.exceptions.Timeout:
        return AuthResult(
            status=AuthStatus.NETWORK_ERROR,
            message="Request timed out. Check your network connection.",
        )
    except requests.exceptions.ConnectionError:
        return AuthResult(
            status=AuthStatus.NETWORK_ERROR,
            message="Connection error. Check your network connection.",
        )
    except Exception as e:
        return AuthResult(
            status=AuthStatus.INVALID,
            message=f"Validation failed: {type(e).__name__}",
        )


async def validate_auth(cookies_json: str) -> AuthResult:
    """Validate MFP cookies (async wrapper).

    Args:
        cookies_json: Serialised cookie JSON string.

    Returns:
        AuthResult with validation status and username if valid.
    """
    if not cookies_json or not cookies_json.strip():
        return AuthResult(
            status=AuthStatus.NO_CREDENTIAL, message="No credential provided"
        )
    return await asyncio.to_thread(_validate_sync, cookies_json)


def validate_auth_sync(cookies_json: str) -> AuthResult:
    """Validate MFP cookies (synchronous).

    Args:
        cookies_json: Serialised cookie JSON string.

    Returns:
        AuthResult with validation status and username if valid.
    """
    if not cookies_json or not cookies_json.strip():
        return AuthResult(
            status=AuthStatus.NO_CREDENTIAL, message="No credential provided"
        )
    return _validate_sync(cookies_json)
