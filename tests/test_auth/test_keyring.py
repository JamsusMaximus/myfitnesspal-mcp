"""Tests for keyring credential storage."""

from unittest.mock import patch

from mfp_mcp.auth.keyring import CredentialResult, clear_credential, get_credential, is_keyring_available, store_credential


class TestCredentialResult:
    def test_repr_hides_cookies(self):
        result = CredentialResult(success=True, message="ok", cookies="secret-data")
        assert "secret-data" not in repr(result)
        assert "<present>" in repr(result)

    def test_repr_shows_none_when_no_cookies(self):
        result = CredentialResult(success=False, message="fail")
        assert "<None>" in repr(result)


class TestStoreCredential:
    @patch("mfp_mcp.auth.keyring.keyring")
    def test_store_success(self, mock_keyring):
        result = store_credential('{"cookies": "data"}')
        assert result.success
        mock_keyring.set_password.assert_called_once()

    def test_store_empty_rejects(self):
        result = store_credential("")
        assert not result.success
        assert "empty" in result.message.lower()

    def test_store_whitespace_rejects(self):
        result = store_credential("   ")
        assert not result.success


class TestGetCredential:
    @patch("mfp_mcp.auth.keyring.keyring")
    def test_get_found(self, mock_keyring):
        mock_keyring.get_password.return_value = '{"cookies": "data"}'
        result = get_credential()
        assert result.success
        assert result.cookies == '{"cookies": "data"}'

    @patch("mfp_mcp.auth.keyring.keyring")
    def test_get_not_found(self, mock_keyring):
        mock_keyring.get_password.return_value = None
        result = get_credential()
        assert not result.success


class TestClearCredential:
    @patch("mfp_mcp.auth.keyring.keyring")
    def test_clear_success(self, mock_keyring):
        result = clear_credential()
        assert result.success
        mock_keyring.delete_password.assert_called_once()


class TestIsKeyringAvailable:
    @patch("mfp_mcp.auth.keyring.keyring")
    def test_available(self, mock_keyring):
        mock_keyring.get_keyring.return_value = type("GoodKeyring", (), {})()
        assert is_keyring_available()

    @patch("mfp_mcp.auth.keyring.keyring")
    def test_fail_backend(self, mock_keyring):
        mock_keyring.get_keyring.return_value = type("FailKeyring", (), {})()
        assert not is_keyring_available()
