"""Unified credential storage with automatic backend selection.

Uses system keyring when available, falls back to encrypted file storage.
Environment variable override is also supported for CI/testing.
"""

import os

from mfp_mcp.auth.encrypted import (
    clear_credential_encrypted,
    get_credential_encrypted,
    store_credential_encrypted,
)
from mfp_mcp.auth.keyring import CredentialResult, is_keyring_available
from mfp_mcp.auth.keyring import clear_credential as clear_credential_keyring
from mfp_mcp.auth.keyring import get_credential as get_credential_keyring
from mfp_mcp.auth.keyring import store_credential as store_credential_keyring

ENV_VAR_NAME = "MFP_COOKIES"


def get_storage_backend() -> str:
    """Get the current storage backend name."""
    if os.environ.get(ENV_VAR_NAME):
        return "environment"
    if is_keyring_available():
        return "keyring"
    return "encrypted_file"


def store_credential(cookies: str) -> CredentialResult:
    """Store MFP cookies.

    Always stores in encrypted file for reliability. Also stores in keyring
    if available.

    Args:
        cookies: Serialised cookie data (JSON string).

    Returns:
        CredentialResult with success status.
    """
    encrypted_result = store_credential_encrypted(cookies)

    if is_keyring_available():
        keyring_result = store_credential_keyring(cookies)
        if keyring_result.success:
            return CredentialResult(
                success=True,
                message="Credential stored in keyring and encrypted file",
            )

    return encrypted_result


def get_credential() -> CredentialResult:
    """Retrieve MFP cookies.

    Checks in order:
    1. Environment variable (for CI/testing)
    2. System keyring
    3. Encrypted file

    Returns:
        CredentialResult with cookies if found.
    """
    env_cookies = os.environ.get(ENV_VAR_NAME)
    if env_cookies:
        return CredentialResult(
            success=True,
            message="Credential from environment variable",
            cookies=env_cookies,
        )

    if is_keyring_available():
        result = get_credential_keyring()
        if result.success:
            return result

    return get_credential_encrypted()


def clear_credential() -> CredentialResult:
    """Clear stored credentials from all backends."""
    results = []

    if is_keyring_available():
        results.append(clear_credential_keyring())

    results.append(clear_credential_encrypted())

    if any(r.success for r in results):
        return CredentialResult(success=True, message="Credentials cleared")

    return CredentialResult(success=False, message="No credentials to clear")
