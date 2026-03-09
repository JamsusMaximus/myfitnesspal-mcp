"""MFPClient - async wrapper around the sync myfitnesspal library.

The upstream myfitnesspal library's __init__ calls _get_auth_data() which
hits /user/auth_token - an endpoint now blocked by MFP's WAF (403).
We work around this by:
1. Creating the Client object without calling __init__
2. Setting up the session and cookies manually
3. Getting the username from MFP's NextAuth session endpoint
4. The HTML scraping methods (get_date, get_measurements) still work fine
"""

import asyncio
import json
import logging
import time
from datetime import date
from http.cookiejar import CookieJar
from typing import Any

import requests

import myfitnesspal
from myfitnesspal.client import Client as MFPLibClient

from mfp_mcp.auth import get_credential
from mfp_mcp.auth.validator import _build_cookiejar

logger = logging.getLogger("mfp-mcp")

REQUEST_INTERVAL = 0.5

NEXTAUTH_SESSION_URL = "https://www.myfitnesspal.com/api/auth/session"


class MFPClientError(Exception):
    """Error from MFP client operations."""

    def __init__(self, message: str, error_code: str = "API_ERROR"):
        super().__init__(message)
        self.error_code = error_code


def _create_mfp_client(cookiejar: CookieJar) -> MFPLibClient:
    """Create a myfitnesspal Client, bypassing the broken __init__.

    The library's __init__ tries to hit /user/auth_token which MFP now
    blocks with a 403. We set up the session manually and get the username
    from the NextAuth session endpoint instead.
    """
    client = object.__new__(MFPLibClient)

    # Set required attributes that __init__ would set
    client._client_instance_id = None
    client._request_counter = 0
    client._log_requests_to = None
    client.unit_aware = False

    # Create session with plain requests (cloudscraper gets blocked by MFP's WAF)
    client.session = requests.Session()
    client.session.headers.update({
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/122.0.0.0 Safari/537.36"
        )
    })
    client.session.cookies.update(cookiejar)

    # Get username from NextAuth session (works, unlike /user/auth_token)
    try:
        resp = client.session.get(NEXTAUTH_SESSION_URL, timeout=10)
        if resp.ok and resp.headers.get("Content-Type", "").startswith("application/json"):
            session_data = resp.json()
            username = session_data.get("user", {}).get("name")
            user_id = session_data.get("userId")
            if username:
                # Set the internal metadata the library expects
                client._user_metadata = {"username": username}
                client._auth_data = {
                    "user_id": user_id,
                    "access_token": None,
                }
                return client

        raise MFPClientError(
            "Could not authenticate with MyFitnessPal. Please log in again.",
            error_code="AUTH_EXPIRED",
        )
    except MFPClientError:
        raise
    except Exception as e:
        raise MFPClientError(
            f"Failed to verify MFP session: {type(e).__name__}",
            error_code="AUTH_INVALID",
        ) from e


class MFPClient:
    """Async wrapper around the sync myfitnesspal.Client.

    Caches the underlying client at class level to reuse across tool calls
    within a session. All public methods are async, using asyncio.to_thread()
    to run sync calls off the event loop.
    """

    _shared_client: MFPLibClient | None = None
    _shared_username: str | None = None
    _last_request_time: float = 0.0
    _lock: asyncio.Lock | None = None

    @classmethod
    def _get_lock(cls) -> asyncio.Lock:
        if cls._lock is None:
            cls._lock = asyncio.Lock()
        return cls._lock

    @classmethod
    def _clear_cache(cls) -> None:
        """Clear the cached client (e.g. after re-auth)."""
        cls._shared_client = None
        cls._shared_username = None

    def _get_sync_client(self) -> MFPLibClient:
        """Get or create the sync myfitnesspal client."""
        if MFPClient._shared_client is not None:
            return MFPClient._shared_client

        cred = get_credential()
        if not cred.success or not cred.cookies:
            raise MFPClientError(
                "No credentials stored. Run 'mfp-mcp auth' to authenticate.",
                error_code="AUTH_REQUIRED",
            )

        jar = _build_cookiejar(cred.cookies)
        client = _create_mfp_client(jar)
        MFPClient._shared_client = client
        MFPClient._shared_username = client.effective_username
        return client

    async def _throttle(self) -> None:
        """Enforce rate limiting between requests."""
        now = time.monotonic()
        elapsed = now - MFPClient._last_request_time
        if elapsed < REQUEST_INTERVAL:
            await asyncio.sleep(REQUEST_INTERVAL - elapsed)
        MFPClient._last_request_time = time.monotonic()

    async def _run(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Run a sync function in a thread with rate limiting."""
        async with self._get_lock():
            await self._throttle()
            try:
                return await asyncio.to_thread(func, *args, **kwargs)
            except MFPClientError:
                raise
            except Exception as e:
                error_msg = str(e).lower()
                if "401" in error_msg or "unauthorized" in error_msg or "login" in error_msg:
                    MFPClient._clear_cache()
                    raise MFPClientError(
                        "Session expired. Run 'mfp-mcp auth' to re-authenticate.",
                        error_code="AUTH_EXPIRED",
                    ) from e
                if "403" in error_msg or "blocked" in error_msg:
                    MFPClient._clear_cache()
                    raise MFPClientError(
                        "Request blocked by MFP. Session may be expired. Run 'mfp-mcp auth' to re-authenticate.",
                        error_code="AUTH_EXPIRED",
                    ) from e
                # SECURITY: Only include exception type, not str(e) which could
                # theoretically contain cookie data in edge cases
                raise MFPClientError(
                    f"MFP request failed: {type(e).__name__}",
                    error_code="API_ERROR",
                ) from e

    async def get_diary(self, diary_date: date) -> dict[str, Any]:
        """Get food diary for a specific date."""
        def _fetch() -> dict[str, Any]:
            client = self._get_sync_client()
            day = client.get_date(diary_date.year, diary_date.month, diary_date.day)

            meals = []
            for meal in day.meals:
                entries = []
                for entry in meal.entries:
                    entries.append({
                        "name": entry.name,
                        "nutrition": dict(entry.totals) if entry.totals else {},
                    })
                meal_totals = {}
                for e in meal.entries:
                    for k, v in (e.totals or {}).items():
                        meal_totals[k] = meal_totals.get(k, 0) + v
                meals.append({
                    "name": meal.name,
                    "entries": entries,
                    "totals": meal_totals,
                })

            return {
                "date": diary_date.isoformat(),
                "meals": meals,
                "totals": dict(day.totals) if day.totals else {},
                "goals": dict(day.goals) if day.goals else {},
                "water": day.water,
                "notes": day.notes,
            }

        return await self._run(_fetch)

    async def get_measurements(
        self,
        measurement: str = "Weight",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """Get body measurements over time."""
        def _fetch() -> list[dict[str, Any]]:
            client = self._get_sync_client()
            lower_bound = start_date or date(2000, 1, 1)
            upper_bound = end_date or date.today()
            data = client.get_measurements(measurement, lower_bound, upper_bound)
            return [
                {"date": d.isoformat(), "value": v}
                for d, v in sorted(data.items())
            ]

        return await self._run(_fetch)

    async def get_report(
        self,
        report_name: str = "Net Calories",
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[dict[str, Any]]:
        """Get a nutrition report over time."""
        def _fetch() -> list[dict[str, Any]]:
            client = self._get_sync_client()
            lower_bound = start_date or date.today()
            upper_bound = end_date or date.today()
            data = client.get_report(report_name, lower_bound, upper_bound)
            return [
                {"date": d.isoformat(), "value": v}
                for d, v in sorted(data.items())
            ]

        return await self._run(_fetch)

    async def get_user_metadata(self) -> dict[str, Any]:
        """Get user metadata/profile from NextAuth session."""
        def _fetch() -> dict[str, Any]:
            client = self._get_sync_client()
            resp = client.session.get(NEXTAUTH_SESSION_URL, timeout=10)
            if resp.ok:
                return resp.json()
            return {"username": client.effective_username}

        return await self._run(_fetch)
