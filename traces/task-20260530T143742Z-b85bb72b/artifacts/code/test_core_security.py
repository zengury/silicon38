"""
Unit tests for core.security — password hashing utilities.
"""

import pytest
from core.security import hash_password, verify_password


class TestCoreSecurity:
    """Verify SHA-256 password hashing round-trips."""

    def test_hash_produces_hex_string(self):
        result = hash_password("test123")
        assert isinstance(result, str)
        assert len(result) == 64  # SHA-256 hex digest
        assert all(c in "0123456789abcdef" for c in result)

    def test_same_input_same_hash(self):
        h1 = hash_password("password1")
        h2 = hash_password("password1")
        assert h1 == h2

    def test_different_input_different_hash(self):
        h1 = hash_password("password1")
        h2 = hash_password("password2")
        assert h1 != h2

    def test_verify_correct_password(self):
        hashed = hash_password("my-secret")
        assert verify_password("my-secret", hashed) is True

    def test_verify_wrong_password(self):
        hashed = hash_password("my-secret")
        assert verify_password("wrong-secret", hashed) is False

    def test_verify_empty_password(self):
        assert verify_password("", "somehash") is False

    def test_verify_empty_hash(self):
        assert verify_password("plain", "") is False

    def test_hash_empty_raises(self):
        with pytest.raises(ValueError):
            hash_password("")
