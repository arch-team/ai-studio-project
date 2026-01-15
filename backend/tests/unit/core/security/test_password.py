"""Password Manager Unit Tests."""


from src.core.security.constants import PASSWORD_BCRYPT_COST, PASSWORD_MIN_LENGTH
from src.core.security.password import PasswordHasher, PasswordValidator


class TestPasswordHasher:
    """Tests for PasswordHasher class."""

    def test_hash_password_returns_hash(
        self, fast_password_hasher: PasswordHasher
    ) -> None:
        """Test that hash_password returns a bcrypt hash string."""
        password = "TestP@ssw0rd123!"
        hashed = fast_password_hasher.hash_password(password)

        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60  # bcrypt hash length

    def test_hash_password_different_each_time(
        self, fast_password_hasher: PasswordHasher
    ) -> None:
        """Test that same password produces different hashes (salt randomization)."""
        password = "TestP@ssw0rd123!"
        hash1 = fast_password_hasher.hash_password(password)
        hash2 = fast_password_hasher.hash_password(password)

        assert hash1 != hash2

    def test_verify_password_correct(
        self, fast_password_hasher: PasswordHasher
    ) -> None:
        """Test that correct password verifies successfully."""
        password = "TestP@ssw0rd123!"
        hashed = fast_password_hasher.hash_password(password)

        assert fast_password_hasher.verify_password(password, hashed) is True

    def test_verify_password_incorrect(
        self, fast_password_hasher: PasswordHasher
    ) -> None:
        """Test that incorrect password fails verification."""
        password = "TestP@ssw0rd123!"
        wrong_password = "WrongP@ssw0rd456!"
        hashed = fast_password_hasher.hash_password(password)

        assert fast_password_hasher.verify_password(wrong_password, hashed) is False

    def test_verify_password_case_sensitive(
        self, fast_password_hasher: PasswordHasher
    ) -> None:
        """Test that password verification is case-sensitive."""
        password = "TestP@ssw0rd123!"
        hashed = fast_password_hasher.hash_password(password)

        assert fast_password_hasher.verify_password("testp@ssw0rd123!", hashed) is False
        assert fast_password_hasher.verify_password("TESTP@SSW0RD123!", hashed) is False

    def test_bcrypt_cost_factor_4_for_fast_tests(
        self, fast_password_hasher: PasswordHasher
    ) -> None:
        """Test that fast hasher uses cost factor 4."""
        password = "TestP@ssw0rd123!"
        hashed = fast_password_hasher.hash_password(password)

        # Extract cost from hash: $2b$04$...
        assert "$04$" in hashed

    def test_bcrypt_cost_factor_12_for_production(
        self, password_hasher: PasswordHasher
    ) -> None:
        """Test that production hasher uses cost factor 12."""
        password = "TestP@ssw0rd123!"
        hashed = password_hasher.hash_password(password)

        # Extract cost from hash: $2b$12$...
        # PASSWORD_BCRYPT_COST should be 12
        assert f"${PASSWORD_BCRYPT_COST:02d}$" in hashed

    def test_needs_rehash_false_for_current_cost(
        self, fast_password_hasher: PasswordHasher
    ) -> None:
        """Test needs_rehash returns False for hash with current cost."""
        password = "TestP@ssw0rd123!"
        hashed = fast_password_hasher.hash_password(password)

        assert fast_password_hasher.needs_rehash(hashed) is False

    def test_needs_rehash_true_for_different_cost(self) -> None:
        """Test needs_rehash returns True for hash with different cost."""
        # Create hash with cost 4
        low_cost_hasher = PasswordHasher(cost_factor=4)
        password = "TestP@ssw0rd123!"
        hashed = low_cost_hasher.hash_password(password)

        # Check with cost 6 hasher
        high_cost_hasher = PasswordHasher(cost_factor=6)
        assert high_cost_hasher.needs_rehash(hashed) is True


class TestPasswordValidatorStrength:
    """Tests for password strength validation."""

    def test_validate_strength_valid(
        self, password_validator: PasswordValidator, valid_passwords: list[str]
    ) -> None:
        """Test that valid passwords pass validation."""
        for password in valid_passwords:
            violations = password_validator.validate_strength(password)
            assert violations == [], f"Password '{password}' should be valid"

    def test_validate_strength_too_short(
        self, password_validator: PasswordValidator
    ) -> None:
        """Test that short passwords fail validation."""
        short_password = "Short1!Aa"  # 9 characters
        violations = password_validator.validate_strength(short_password)

        assert len(violations) > 0
        assert any("12" in v or "字符" in v for v in violations)

    def test_validate_strength_exactly_12_chars(
        self, password_validator: PasswordValidator
    ) -> None:
        """Test that exactly 12 character password passes length check."""
        password = "TestP@ss1234"  # Exactly 12 chars
        violations = password_validator.validate_strength(password)

        # Should not have length violation
        assert not any("12" in v or "字符" in v for v in violations)

    def test_validate_strength_11_chars_fails(
        self, password_validator: PasswordValidator
    ) -> None:
        """Test that 11 character password fails length check."""
        password = "TestP@ss123"  # 11 chars
        violations = password_validator.validate_strength(password)

        assert any("12" in v or "字符" in v for v in violations)

    def test_validate_strength_no_lowercase(
        self, password_validator: PasswordValidator
    ) -> None:
        """Test that password without lowercase fails validation."""
        password = "NOLOWERCASE1!@#"
        violations = password_validator.validate_strength(password)

        assert len(violations) > 0
        assert any("小写" in v or "lowercase" in v.lower() for v in violations)

    def test_validate_strength_no_uppercase(
        self, password_validator: PasswordValidator
    ) -> None:
        """Test that password without uppercase fails validation."""
        password = "nouppercase1!@#"
        violations = password_validator.validate_strength(password)

        assert len(violations) > 0
        assert any("大写" in v or "uppercase" in v.lower() for v in violations)

    def test_validate_strength_no_digit(
        self, password_validator: PasswordValidator
    ) -> None:
        """Test that password without digits fails validation."""
        password = "NoDigitHere!@#Ab"
        violations = password_validator.validate_strength(password)

        assert len(violations) > 0
        assert any("数字" in v or "digit" in v.lower() for v in violations)

    def test_validate_strength_no_special(
        self, password_validator: PasswordValidator
    ) -> None:
        """Test that password without special characters fails validation."""
        password = "NoSpecial123ABC"
        violations = password_validator.validate_strength(password)

        assert len(violations) > 0
        assert any("特殊" in v or "special" in v.lower() for v in violations)

    def test_validate_strength_multiple_violations(
        self, password_validator: PasswordValidator
    ) -> None:
        """Test that password with multiple issues returns all violations."""
        # Short, no uppercase, no special
        password = "short123"
        violations = password_validator.validate_strength(password)

        assert len(violations) >= 3

    def test_validate_strength_only_lowercase(
        self, password_validator: PasswordValidator
    ) -> None:
        """Test that password with only lowercase fails multiple checks."""
        password = "onlylowercase"
        violations = password_validator.validate_strength(password)

        # Should fail: uppercase, digit, special
        assert len(violations) >= 3

    def test_validate_strength_only_numbers(
        self, password_validator: PasswordValidator
    ) -> None:
        """Test that password with only numbers fails multiple checks."""
        password = "123456789012"
        violations = password_validator.validate_strength(password)

        # Should fail: lowercase, uppercase, special
        assert len(violations) >= 3

    def test_validate_strength_special_chars_variety(
        self, password_validator: PasswordValidator
    ) -> None:
        """Test that various special characters are accepted."""
        special_chars = "!@#$%^&*(),.?\":{}|<>-_=+[]\\;'`~"
        for char in special_chars:
            password = f"TestP@ss123{char}"
            violations = password_validator.validate_strength(password)
            # Should pass special char check
            assert not any(
                "特殊" in v or "special" in v.lower() for v in violations
            ), f"Special char '{char}' should be accepted"


class TestPasswordValidatorHistory:
    """Tests for password history validation."""

    def test_check_password_history_reused(
        self,
        password_validator: PasswordValidator,
        fast_password_hasher: PasswordHasher,
    ) -> None:
        """Test that reusing a recent password is detected."""
        password = "TestP@ssw0rd123!"
        hashed = fast_password_hasher.hash_password(password)
        history = [hashed]

        is_ok = password_validator.check_password_history(
            new_password=password,
            password_history=history,
            hasher=fast_password_hasher,
        )

        # Returns False when password is in history (violation)
        assert is_ok is False

    def test_check_password_history_new(
        self,
        password_validator: PasswordValidator,
        fast_password_hasher: PasswordHasher,
    ) -> None:
        """Test that new password passes history check."""
        old_password = "OldP@ssw0rd123!"
        new_password = "NewP@ssw0rd456!"
        hashed = fast_password_hasher.hash_password(old_password)
        history = [hashed]

        is_ok = password_validator.check_password_history(
            new_password=new_password,
            password_history=history,
            hasher=fast_password_hasher,
        )

        # Returns True when password is NOT in history (OK)
        assert is_ok is True

    def test_check_password_history_empty(
        self,
        password_validator: PasswordValidator,
        fast_password_hasher: PasswordHasher,
    ) -> None:
        """Test that any password passes with empty history."""
        password = "AnyP@ssw0rd123!"
        history: list[str] = []

        is_ok = password_validator.check_password_history(
            new_password=password,
            password_history=history,
            hasher=fast_password_hasher,
        )

        # Returns True when history is empty (OK)
        assert is_ok is True

    def test_check_password_history_limit_5(
        self,
        password_validator: PasswordValidator,
        fast_password_hasher: PasswordHasher,
    ) -> None:
        """Test that only first 5 passwords in list are checked."""
        # Create 6 password hashes
        passwords = [f"Password{i}@123!" for i in range(6)]
        history = [fast_password_hasher.hash_password(p) for p in passwords]

        # The implementation checks first 5 passwords (indices 0-4)
        # Password at index 5 should NOT be checked
        is_ok = password_validator.check_password_history(
            new_password=passwords[5],
            password_history=history,
            hasher=fast_password_hasher,
        )

        # Password 5 is outside the first 5, should pass (is_ok = True)
        assert is_ok is True

    def test_check_password_history_within_5(
        self,
        password_validator: PasswordValidator,
        fast_password_hasher: PasswordHasher,
    ) -> None:
        """Test that passwords within first 5 are detected."""
        passwords = [f"Password{i}@123!" for i in range(6)]
        history = [fast_password_hasher.hash_password(p) for p in passwords]

        # First password (index 0) should be detected
        is_ok = password_validator.check_password_history(
            new_password=passwords[0],
            password_history=history,
            hasher=fast_password_hasher,
        )

        # Returns False when password IS in history (violation)
        assert is_ok is False

    def test_check_password_history_exactly_5(
        self,
        password_validator: PasswordValidator,
        fast_password_hasher: PasswordHasher,
    ) -> None:
        """Test with exactly 5 passwords in history."""
        passwords = [f"Password{i}@123!" for i in range(5)]
        history = [fast_password_hasher.hash_password(p) for p in passwords]

        # All 5 should be detected
        for i, password in enumerate(passwords):
            is_ok = password_validator.check_password_history(
                new_password=password,
                password_history=history,
                hasher=fast_password_hasher,
            )
            # Returns False when password IS in history (violation)
            assert is_ok is False, f"Password {i} should be in history"


class TestPasswordConstants:
    """Tests for password-related constants."""

    def test_password_min_length_is_12(self) -> None:
        """Test that minimum password length is 12."""
        assert PASSWORD_MIN_LENGTH == 12

    def test_password_bcrypt_cost_is_12(self) -> None:
        """Test that bcrypt cost factor is 12."""
        assert PASSWORD_BCRYPT_COST == 12


class TestPasswordEdgeCases:
    """Tests for edge cases in password handling."""

    def test_hash_empty_password(self, fast_password_hasher: PasswordHasher) -> None:
        """Test hashing empty password (validation should catch this first)."""
        hashed = fast_password_hasher.hash_password("")
        assert isinstance(hashed, str)
        assert fast_password_hasher.verify_password("", hashed) is True

    def test_hash_unicode_password(self, fast_password_hasher: PasswordHasher) -> None:
        """Test hashing password with unicode characters."""
        password = "TestP@ss密码123!"
        hashed = fast_password_hasher.hash_password(password)

        assert fast_password_hasher.verify_password(password, hashed) is True
        assert fast_password_hasher.verify_password("TestP@ss123!", hashed) is False

    def test_hash_very_long_password(
        self, fast_password_hasher: PasswordHasher
    ) -> None:
        """Test hashing very long password."""
        # bcrypt truncates at 72 bytes
        password = "A" * 100 + "@1a"
        hashed = fast_password_hasher.hash_password(password)

        assert fast_password_hasher.verify_password(password, hashed) is True

    def test_validate_password_with_spaces(
        self, password_validator: PasswordValidator
    ) -> None:
        """Test password with spaces is validated correctly."""
        password = "Test P@ss 123!"
        violations = password_validator.validate_strength(password)

        # Spaces should not cause issues if other requirements met
        assert violations == []

    def test_validate_password_leading_trailing_spaces(
        self, password_validator: PasswordValidator
    ) -> None:
        """Test password with leading/trailing spaces."""
        password = " TestP@ss123! "
        violations = password_validator.validate_strength(password)

        # Should still be valid
        assert violations == []
