"""Browser cookie extraction for MyFitnessPal authentication.

SECURITY NOTES:
- Domain is HARDCODED to .myfitnesspal.com - cannot be changed via parameters
- Cookie values must NEVER be included in error messages or logs
- Only return cookies in BrowserCookieResult.cookies field, never in message
"""

import json
from dataclasses import dataclass, field


@dataclass
class BrowserCookieResult:
    """Result of browser cookie extraction.

    SECURITY: Cookie values are stored in `cookies` field only.
    The `message` field must NEVER contain cookie values.
    """

    success: bool
    cookies: str | None = field(default=None, repr=False)
    message: str = ""
    browser: str | None = None

    def __repr__(self) -> str:
        """Safe repr that never exposes cookie values."""
        cookies_status = "present" if self.cookies else "None"
        return (
            f"BrowserCookieResult(success={self.success}, cookies=<{cookies_status}>, "
            f"message={self.message!r}, browser={self.browser!r})"
        )


SUPPORTED_BROWSERS = ["chrome", "firefox", "safari", "edge", "chromium", "brave", "opera"]

MFP_DOMAIN = ".myfitnesspal.com"


def _serialise_cookiejar(cj: "http.cookiejar.CookieJar") -> str:
    """Serialise relevant MFP cookies from a cookie jar to JSON.

    Only includes cookies for the MFP domain.
    """
    cookies = []
    for cookie in cj:
        if MFP_DOMAIN in (cookie.domain or ""):
            cookies.append({
                "name": cookie.name,
                "value": cookie.value,
                "domain": cookie.domain,
                "path": cookie.path or "/",
                "secure": cookie.secure,
            })
    return json.dumps(cookies)


def extract_mfp_cookies(browser: str | None = None) -> BrowserCookieResult:
    """Extract MyFitnessPal cookies from browser.

    Args:
        browser: Browser name (chrome, firefox, safari, edge, chromium, brave, opera).
                 If None, tries all browsers in order.

    Returns:
        BrowserCookieResult with serialised cookies if found.
    """
    try:
        import browser_cookie3
    except ImportError:
        return BrowserCookieResult(
            success=False,
            message="browser-cookie3 not installed. Run: pip install mfp-mcp[browser]",
        )

    browser_funcs = {
        "chrome": browser_cookie3.chrome,
        "firefox": browser_cookie3.firefox,
        "safari": browser_cookie3.safari,
        "edge": browser_cookie3.edge,
        "chromium": browser_cookie3.chromium,
        "brave": browser_cookie3.brave,
        "opera": browser_cookie3.opera,
    }

    def try_browser(name: str) -> BrowserCookieResult:
        func = browser_funcs.get(name)
        if not func:
            return BrowserCookieResult(success=False, message=f"Unknown browser: {name}")

        try:
            cj = func(domain_name=MFP_DOMAIN)
            serialised = _serialise_cookiejar(cj)
            cookie_list = json.loads(serialised)
            if cookie_list:
                return BrowserCookieResult(
                    success=True,
                    cookies=serialised,
                    browser=name,
                    message=f"Found {len(cookie_list)} cookies in {name}",
                )
            return BrowserCookieResult(success=False, message=f"No MFP cookies in {name}")
        except PermissionError:
            return BrowserCookieResult(
                success=False,
                message=f"Permission denied reading {name} cookies. Close {name} and try again.",
            )
        except Exception as e:
            error_type = type(e).__name__
            return BrowserCookieResult(success=False, message=f"Error reading {name}: {error_type}")

    if browser:
        browser = browser.lower()
        if browser not in browser_funcs:
            return BrowserCookieResult(
                success=False,
                message=f"Unknown browser: {browser}. Supported: {', '.join(SUPPORTED_BROWSERS)}",
            )
        return try_browser(browser)

    errors = []
    for name in SUPPORTED_BROWSERS:
        result = try_browser(name)
        if result.success:
            return result
        errors.append(f"  {name}: {result.message}")

    return BrowserCookieResult(
        success=False,
        message="Could not find MFP cookies in any browser.\n" + "\n".join(errors),
    )
