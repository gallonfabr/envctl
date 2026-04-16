"""Tests for envctl.crypto encryption utilities."""

import pytest
from envctl.crypto import (
    derive_key,
    generate_salt,
    encrypt,
    decrypt,
    encrypt_vars,
    decrypt_vars,
)


PASSWORD = "s3cr3t!"
SAMPLE_VARS = {"API_KEY": "abc123", "DEBUG": "true", "PORT": "8080"}


def test_generate_salt_length():
    salt = generate_salt()
    assert len(salt) == 16


def test_generate_salt_unique():
    assert generate_salt() != generate_salt()


def test_derive_key_length():
    salt = generate_salt()
    key = derive_key(PASSWORD, salt)
    assert len(key) == 44  # base64-encoded 32-byte key


def test_encrypt_decrypt_roundtrip():
    salt = generate_salt()
    ciphertext = encrypt("hello world", PASSWORD, salt)
    assert ciphertext != "hello world"
    assert decrypt(ciphertext, PASSWORD, salt) == "hello world"


def test_decrypt_wrong_password():
    salt = generate_salt()
    ciphertext = encrypt("secret", PASSWORD, salt)
    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt(ciphertext, "wrongpass", salt)


def test_encrypt_vars_returns_required_keys():
    result = encrypt_vars(SAMPLE_VARS, PASSWORD)
    assert "salt" in result
    assert "data" in result
    assert "vars" not in result


def test_encrypt_vars_decrypt_vars_roundtrip():
    encrypted = encrypt_vars(SAMPLE_VARS, PASSWORD)
    result = decrypt_vars(encrypted, PASSWORD)
    assert result == SAMPLE_VARS


def test_decrypt_vars_wrong_password():
    encrypted = encrypt_vars(SAMPLE_VARS, PASSWORD)
    with pytest.raises(ValueError):
        decrypt_vars(encrypted, "badpassword")
