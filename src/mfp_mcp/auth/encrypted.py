"""Encrypted file-based credential storage for MyFitnessPal authentication.

Fallback for environments where system keyring is not available.

Limitations:
- Without a user password, encryption is bound to machine identity only.
  Anyone with access to the machine and this code can derive the key.
"""

import base64
import contextlib
import os
import platform
import stat
from pathlib import Path

from cryptography.hazmat.primitives import hashes as crypto_hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from mfp_mcp.auth.keyring import CredentialResult

CONFIG_DIR = Path.home() / ".config" / "myfitnesspal-mcp"
CREDENTIALS_FILE = CONFIG_DIR / "credentials.enc"


def _get_machine_id() -> bytes:
    """Get a machine-specific identifier for key derivation."""
    components = [
        platform.node(),
        platform.machine(),
        platform.system(),
    ]

    try:
        if platform.system() == "Darwin":
            import subprocess

            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if "IOPlatformUUID" in result.stdout:
                for line in result.stdout.split("\n"):
                    if "IOPlatformUUID" in line:
                        uuid = line.split("=")[-1].strip().strip('"')
                        components.append(uuid)
                        break
    except Exception:
        pass

    try:
        machine_id_path = Path("/etc/machine-id")
        if machine_id_path.exists():
            components.append(machine_id_path.read_text().strip())
    except Exception:
        pass

    return "|".join(components).encode("utf-8")


_KDF_ITERATIONS = 600_000


def _derive_key(password: str | None = None) -> bytes:
    """Derive an encryption key using PBKDF2-HMAC-SHA256."""
    machine_id = _get_machine_id()
    key_material = password.encode("utf-8") if password else b"mfp-mcp-default"
    kdf = PBKDF2HMAC(
        algorithm=crypto_hashes.SHA256(),
        length=32,
        salt=machine_id,
        iterations=_KDF_ITERATIONS,
    )
    return kdf.derive(key_material)


def _ensure_secure_directory() -> None:
    """Ensure the config directory exists with secure permissions."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with contextlib.suppress(OSError):
        os.chmod(CONFIG_DIR, stat.S_IRWXU)


def _set_file_permissions(path: Path) -> None:
    """Set secure file permissions (600 - owner read/write only)."""
    with contextlib.suppress(OSError):
        os.chmod(path, stat.S_IRUSR | stat.S_IWUSR)


class EncryptedCredentialStore:
    """Encrypted file-based credential storage using AES-256-GCM."""

    def __init__(self, password: str | None = None):
        self._key = _derive_key(password)

    def store(self, cookies: str) -> CredentialResult:
        """Store MFP cookies in an encrypted file."""
        if not cookies or not cookies.strip():
            return CredentialResult(success=False, message="Cookie data cannot be empty")

        try:
            _ensure_secure_directory()
            nonce = os.urandom(12)
            aesgcm = AESGCM(self._key)
            ciphertext = aesgcm.encrypt(nonce, cookies.strip().encode("utf-8"), None)
            encrypted_data = base64.b64encode(nonce + ciphertext)
            CREDENTIALS_FILE.write_bytes(encrypted_data)
            _set_file_permissions(CREDENTIALS_FILE)
            return CredentialResult(success=True, message="Credential stored in encrypted file")
        except Exception as e:
            return CredentialResult(success=False, message=f"Encryption error ({type(e).__name__})")

    def get(self) -> CredentialResult:
        """Retrieve MFP cookies from the encrypted file."""
        if not CREDENTIALS_FILE.exists():
            return CredentialResult(success=False, message="No credential file found")

        try:
            encrypted_data = base64.b64decode(CREDENTIALS_FILE.read_bytes())
            nonce = encrypted_data[:12]
            ciphertext = encrypted_data[12:]
            aesgcm = AESGCM(self._key)
            cookies = aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")
            return CredentialResult(success=True, message="Credential retrieved", cookies=cookies)
        except Exception:
            return CredentialResult(
                success=False,
                message="Decryption failed. Run 'mfp-mcp auth' to re-authenticate.",
            )

    def clear(self) -> CredentialResult:
        """Remove the encrypted credential file."""
        try:
            CREDENTIALS_FILE.unlink(missing_ok=True)
            return CredentialResult(success=True, message="Credential file removed")
        except Exception as e:
            return CredentialResult(success=False, message=f"Error removing file ({type(e).__name__})")


_default_store: EncryptedCredentialStore | None = None


def _get_store() -> EncryptedCredentialStore:
    global _default_store
    if _default_store is None:
        _default_store = EncryptedCredentialStore()
    return _default_store


def store_credential_encrypted(cookies: str) -> CredentialResult:
    return _get_store().store(cookies)


def get_credential_encrypted() -> CredentialResult:
    return _get_store().get()


def clear_credential_encrypted() -> CredentialResult:
    return _get_store().clear()
