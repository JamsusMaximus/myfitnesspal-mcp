"""Tests for encrypted file credential storage."""

import tempfile
from pathlib import Path
from unittest.mock import patch

from mfp_mcp.auth.encrypted import EncryptedCredentialStore


class TestEncryptedCredentialStore:
    def test_store_and_retrieve(self, tmp_path):
        with patch("mfp_mcp.auth.encrypted.CONFIG_DIR", tmp_path), \
             patch("mfp_mcp.auth.encrypted.CREDENTIALS_FILE", tmp_path / "creds.enc"):
            store = EncryptedCredentialStore()
            cookies = '[{"name": "test", "value": "val", "domain": ".myfitnesspal.com"}]'

            result = store.store(cookies)
            assert result.success

            result = store.get()
            assert result.success
            assert result.cookies == cookies

    def test_store_empty_rejects(self, tmp_path):
        with patch("mfp_mcp.auth.encrypted.CONFIG_DIR", tmp_path), \
             patch("mfp_mcp.auth.encrypted.CREDENTIALS_FILE", tmp_path / "creds.enc"):
            store = EncryptedCredentialStore()
            result = store.store("")
            assert not result.success

    def test_get_missing_file(self, tmp_path):
        with patch("mfp_mcp.auth.encrypted.CREDENTIALS_FILE", tmp_path / "nonexistent.enc"):
            store = EncryptedCredentialStore()
            result = store.get()
            assert not result.success
            assert "No credential file" in result.message

    def test_clear(self, tmp_path):
        creds_file = tmp_path / "creds.enc"
        creds_file.write_text("data")
        with patch("mfp_mcp.auth.encrypted.CREDENTIALS_FILE", creds_file):
            store = EncryptedCredentialStore()
            result = store.clear()
            assert result.success
            assert not creds_file.exists()

    def test_wrong_password_fails(self, tmp_path):
        with patch("mfp_mcp.auth.encrypted.CONFIG_DIR", tmp_path), \
             patch("mfp_mcp.auth.encrypted.CREDENTIALS_FILE", tmp_path / "creds.enc"):
            store1 = EncryptedCredentialStore(password="correct")
            store1.store("secret cookies")

            store2 = EncryptedCredentialStore(password="wrong")
            result = store2.get()
            assert not result.success
            assert "Decryption failed" in result.message
