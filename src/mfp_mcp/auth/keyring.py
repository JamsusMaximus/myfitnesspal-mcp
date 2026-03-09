"""Keyring-based credential storage for MyFitnessPal authentication."""

from dataclasses import dataclass, field

import keyring
from keyring.errors import KeyringError, NoKeyringError

SERVICE_NAME = "myfitnesspal-mcp"
USERNAME = "cookies"


@dataclass
class CredentialResult:
    """Result of a credential operation."""

    success: bool
    message: str
    cookies: str | None = field(default=None, repr=False)

    def __repr__(self) -> str:
        """Safe repr that never exposes cookie values."""
        cookies_status = "present" if self.cookies else "None"
        return f"CredentialResult(success={self.success}, cookies=<{cookies_status}>, message={self.message!r})"


def is_keyring_available() -> bool:
    """Check if a keyring backend is available."""
    try:
        backend = keyring.get_keyring()
        backend_name = type(backend).__name__.lower()
        return not ("fail" in backend_name or "null" in backend_name)
    except (NoKeyringError, KeyringError):
        return False


def store_credential(cookies: str) -> CredentialResult:
    """Store MFP cookies in the system keyring.

    Args:
        cookies: Serialised cookie data (JSON string).

    Returns:
        CredentialResult with success status.
    """
    if not cookies or not cookies.strip():
        return CredentialResult(success=False, message="Cookie data cannot be empty")

    try:
        keyring.set_password(SERVICE_NAME, USERNAME, cookies.strip())
        return CredentialResult(success=True, message="Credential stored in keyring")
    except NoKeyringError:
        return CredentialResult(success=False, message="No keyring backend available. Use encrypted file storage.")
    except KeyringError as e:
        return CredentialResult(success=False, message=f"Keyring error: {e}")


def get_credential() -> CredentialResult:
    """Retrieve MFP cookies from the system keyring.

    Returns:
        CredentialResult with cookies if found.
    """
    try:
        cookies = keyring.get_password(SERVICE_NAME, USERNAME)
        if cookies:
            return CredentialResult(success=True, message="Credential retrieved", cookies=cookies)
        return CredentialResult(success=False, message="No credential stored")
    except NoKeyringError:
        return CredentialResult(success=False, message="No keyring backend available. Use encrypted file storage.")
    except KeyringError as e:
        return CredentialResult(success=False, message=f"Keyring error: {e}")


def clear_credential() -> CredentialResult:
    """Remove MFP cookies from the system keyring.

    Returns:
        CredentialResult with success status.
    """
    try:
        keyring.delete_password(SERVICE_NAME, USERNAME)
        return CredentialResult(success=True, message="Credential cleared")
    except keyring.errors.PasswordDeleteError:
        return CredentialResult(success=True, message="No credential to clear")
    except NoKeyringError:
        return CredentialResult(success=False, message="No keyring backend available")
    except KeyringError as e:
        return CredentialResult(success=False, message=f"Keyring error: {e}")
