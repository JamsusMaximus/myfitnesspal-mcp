"""Tests for browser cookie extraction."""

from unittest.mock import MagicMock, patch

from mfp_mcp.auth.browser import BrowserCookieResult, extract_mfp_cookies


class TestBrowserCookieResult:
    def test_repr_hides_cookies(self):
        result = BrowserCookieResult(success=True, cookies="secret", browser="chrome")
        assert "secret" not in repr(result)
        assert "<present>" in repr(result)


class TestExtractMfpCookies:
    @patch("mfp_mcp.auth.browser.browser_cookie3", create=True)
    def test_chrome_success(self, mock_bc3):
        # Create mock cookies
        cookie = MagicMock()
        cookie.name = "session"
        cookie.value = "abc123"
        cookie.domain = ".myfitnesspal.com"
        cookie.path = "/"
        cookie.secure = True

        mock_jar = MagicMock()
        mock_jar.__iter__ = MagicMock(return_value=iter([cookie]))
        mock_bc3.chrome.return_value = mock_jar

        # Patch the import inside the function
        import sys
        sys.modules["browser_cookie3"] = mock_bc3

        result = extract_mfp_cookies("chrome")
        assert result.success
        assert result.browser == "chrome"
        assert result.cookies is not None
        assert "abc123" not in result.message  # security: no cookie values in message

    def test_unknown_browser(self):
        result = extract_mfp_cookies("netscape")
        # Will fail with import error or unknown browser
        assert not result.success

    @patch("mfp_mcp.auth.browser.browser_cookie3", create=True)
    def test_empty_cookies(self, mock_bc3):
        mock_jar = MagicMock()
        mock_jar.__iter__ = MagicMock(return_value=iter([]))
        mock_bc3.chrome.return_value = mock_jar

        import sys
        sys.modules["browser_cookie3"] = mock_bc3

        result = extract_mfp_cookies("chrome")
        assert not result.success
        assert "No MFP cookies" in result.message
