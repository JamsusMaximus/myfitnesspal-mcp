"""Authentication module for MyFitnessPal MCP Server."""

from mfp_mcp.auth.encrypted import EncryptedCredentialStore
from mfp_mcp.auth.keyring import CredentialResult, is_keyring_available
from mfp_mcp.auth.storage import (
    clear_credential,
    get_credential,
    get_storage_backend,
    store_credential,
)
from mfp_mcp.auth.validator import AuthResult, AuthStatus, validate_auth, validate_auth_sync

__all__ = [
    "AuthResult",
    "AuthStatus",
    "CredentialResult",
    "EncryptedCredentialStore",
    "clear_credential",
    "get_credential",
    "get_storage_backend",
    "is_keyring_available",
    "store_credential",
    "validate_auth",
    "validate_auth_sync",
]
