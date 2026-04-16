"""Encryption/decryption utilities for securing stored environment variables."""

import base64
import hashlib
import os

from cryptography.fernet import Fernet, InvalidToken


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a Fernet-compatible key from a password and salt."""
    key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations=100_000)
    return base64.urlsafe_b64encode(key)


def generate_salt() -> bytes:
    """Generate a random 16-byte salt."""
    return os.urandom(16)


def encrypt(plaintext: str, password: str, salt: bytes) -> str:
    """Encrypt plaintext string using password. Returns base64-encoded ciphertext."""
    key = derive_key(password, salt)
    f = Fernet(key)
    token = f.encrypt(plaintext.encode())
    return base64.urlsafe_b64encode(token).decode()


def decrypt(ciphertext: str, password: str, salt: bytes) -> str:
    """Decrypt ciphertext string using password. Raises ValueError on failure."""
    key = derive_key(password, salt)
    f = Fernet(key)
    try:
        token = base64.urlsafe_b64decode(ciphertext.encode())
        return f.decrypt(token).decode()
    except (InvalidToken, Exception) as exc:
        raise ValueError("Decryption failed: invalid password or corrupted data.") from exc


def encrypt_vars(vars_dict: dict, password: str) -> dict:
    """Encrypt a dict of env vars. Returns dict with 'salt', 'data' keys."""
    salt = generate_salt()
    import json
    plaintext = json.dumps(vars_dict)
    return {
        "salt": base64.urlsafe_b64encode(salt).decode(),
        "data": encrypt(plaintext, password, salt),
    }


def decrypt_vars(encrypted: dict, password: str) -> dict:
    """Decrypt a dict produced by encrypt_vars. Returns original env vars dict."""
    import json
    salt = base64.urlsafe_b64decode(encrypted["salt"].encode())
    plaintext = decrypt(encrypted["data"], password, salt)
    return json.loads(plaintext)
