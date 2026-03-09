"""Tests for unified credential storage."""

from unittest.mock import patch

from mfp_mcp.auth.keyring import CredentialResult
from mfp_mcp.auth.storage import get_credential, get_storage_backend, store_credential


class TestGetStorageBackend:
    def test_env_var(self):
        with patch.dict("os.environ", {"MFP_COOKIES": "data"}):
            assert get_storage_backend() == "environment"

    @patch("mfp_mcp.auth.storage.is_keyring_available", return_value=True)
    def test_keyring(self, _):
        assert get_storage_backend() == "keyring"

    @patch("mfp_mcp.auth.storage.is_keyring_available", return_value=False)
    def test_encrypted_file(self, _):
        assert get_storage_backend() == "encrypted_file"


class TestGetCredential:
    def test_env_var_takes_priority(self):
        with patch.dict("os.environ", {"MFP_COOKIES": '["test"]'}):
            result = get_credential()
            assert result.success
            assert result.cookies == '["test"]'

    @patch("mfp_mcp.auth.storage.is_keyring_available", return_value=True)
    @patch("mfp_mcp.auth.storage.get_credential_keyring")
    def test_keyring_fallback(self, mock_kr, _):
        mock_kr.return_value = CredentialResult(success=True, message="ok", cookies="kr_data")
        result = get_credential()
        assert result.success
        assert result.cookies == "kr_data"


class TestStoreCredential:
    @patch("mfp_mcp.auth.storage.store_credential_encrypted")
    @patch("mfp_mcp.auth.storage.is_keyring_available", return_value=False)
    def test_stores_encrypted(self, _, mock_enc):
        mock_enc.return_value = CredentialResult(success=True, message="ok")
        result = store_credential("cookies")
        assert result.success
        mock_enc.assert_called_once_with("cookies")
