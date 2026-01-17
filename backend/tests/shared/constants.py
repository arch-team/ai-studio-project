"""Test constants used across all test levels."""

# JWT Configuration
TEST_JWT_SECRET = "test-secret-key-for-jwt-signing-at-least-32-chars"
TEST_ACCESS_TOKEN_EXPIRE_MINUTES = 30
TEST_REFRESH_TOKEN_EXPIRE_DAYS = 7

# Password Configuration
TEST_PASSWORD_COST = 4  # Low cost for fast tests

# API Configuration
TEST_API_BASE_URL = "http://test"

# Database Configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Sample Valid Passwords
VALID_PASSWORDS = [
    "P@ssw0rd123!",
    "Secure!Pass123",
    "C0mplex#Pass99",
    "Test@User1234",
    "Admin$ecure99",
]

# Sample Invalid Passwords (with violation type as key)
INVALID_PASSWORDS = {
    "too_short": "Short1!",
    "no_lowercase": "NOLOWERCASE1!@#",
    "no_uppercase": "nouppercase1!@#",
    "no_digit": "NoDigitHere!@#Ab",
    "no_special": "NoSpecial123ABC",
    "only_lowercase": "onlylowercase",
    "only_numbers": "123456789012",
}
