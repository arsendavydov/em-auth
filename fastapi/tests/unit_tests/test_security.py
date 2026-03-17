from src.utils.security import hash_password, verify_password


def test_hash_password_returns_non_plain_value():
    password = "secret_password"

    hashed = hash_password(password)

    assert hashed != password
    assert hashed.startswith("$2")


def test_verify_password_returns_true_for_matching_password():
    password = "secret_password"
    hashed = hash_password(password)

    assert verify_password(password, hashed) is True


def test_verify_password_returns_false_for_wrong_password():
    hashed = hash_password("secret_password")

    assert verify_password("wrong_password", hashed) is False


def test_verify_password_returns_false_for_invalid_hash():
    assert verify_password("secret_password", "not-a-bcrypt-hash") is False
