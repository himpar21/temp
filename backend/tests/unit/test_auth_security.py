"""Tests for password and JWT session primitives."""

import unittest

from core.security import InvalidTokenError, create_access_token, decode_access_token, hash_password, verify_password
from schemas.request.auth_schema import SignupRequest


class AuthSecurityTests(unittest.TestCase):
    def test_password_is_hashed_and_verified(self) -> None:
        password_hash = hash_password("correct horse battery staple")

        self.assertNotIn("correct horse", password_hash)
        self.assertTrue(verify_password("correct horse battery staple", password_hash))
        self.assertFalse(verify_password("wrong password", password_hash))

    def test_access_token_round_trip_and_tamper_detection(self) -> None:
        token, expires_in = create_access_token("user-123")

        self.assertEqual("user-123", decode_access_token(token))
        self.assertGreater(expires_in, 0)
        with self.assertRaises(InvalidTokenError):
            decode_access_token(token + "tampered")

    def test_signup_normalizes_identity_fields(self) -> None:
        request = SignupRequest(
            full_name="  Ada   Lovelace ",
            email=" ADA@Example.COM ",
            password="Password123!",
            confirm_password="Password123!",
        )

        self.assertEqual("Ada Lovelace", request.full_name)
        self.assertEqual("ada@example.com", request.email)

    def test_signup_rejects_weak_or_mismatched_passwords(self) -> None:
        invalid_passwords = ("password!", "Password!", "Password123")
        for password in invalid_passwords:
            with self.subTest(password=password), self.assertRaises(ValueError):
                SignupRequest(
                    full_name="Ada Lovelace",
                    email="ada@example.com",
                    password=password,
                    confirm_password=password,
                )

        with self.assertRaisesRegex(ValueError, "Passwords do not match"):
            SignupRequest(
                full_name="Ada Lovelace",
                email="ada@example.com",
                password="Password123!",
                confirm_password="Different123!",
            )


if __name__ == "__main__":
    unittest.main()
