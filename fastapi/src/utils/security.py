"""
Хеширование паролей через bcrypt (без passlib).

Пароль в БД хранится только как hash + salt внутри строки bcrypt.
"""

import bcrypt


def hash_password(password: str) -> str:
    """Хеширует пароль для сохранения в `users.password_hash`."""

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Сравнивает введённый пароль с сохранённым хешом; при битом хеше — False."""

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except ValueError:
        return False
