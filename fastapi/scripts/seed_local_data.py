"""
Локальное заполнение тестовых пользователей по переменным TEST_*_EMAIL из .env.

Запуск из корня проекта; нужны TEST_PASSWORD и хотя бы один email. Не для продакшена.
"""

import asyncio
import os

from sqlalchemy import select

from src.models.roles import Role
from src.models.user_roles import UserRole
from src.models.users import User
from src.utils.db import AsyncSessionLocal
from src.utils.security import hash_password

SEEDED_USERS = (
    ("TEST_ADMIN_EMAIL", "admin", "Admin", "One"),
    ("TEST_ADMIN2_EMAIL", "admin", "Admin", "Two"),
    ("TEST_MANAGER_EMAIL", "manager", "Manager", "One"),
    ("TEST_MANAGER2_EMAIL", "manager", "Manager", "Two"),
    ("TEST_USER_EMAIL", "user", "User", "One"),
    ("TEST_USER2_EMAIL", "user", "User", "Two"),
)


async def seed_local_data() -> None:
    test_password = os.getenv("TEST_PASSWORD")
    if not test_password:
        raise ValueError("В .env должен быть задан TEST_PASSWORD для локального сида")

    async with AsyncSessionLocal() as session:
        roles_result = await session.execute(select(Role))
        roles = {role.name: role for role in roles_result.scalars().all()}

        for env_name, role_name, first_name, last_name in SEEDED_USERS:
            email = os.getenv(env_name)
            if not email:
                continue

            user_result = await session.execute(select(User).where(User.email == email))
            user = user_result.scalar_one_or_none()
            if user is None:
                user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password_hash=hash_password(test_password),
                    is_active=True,
                    deleted_at=None,
                )
                session.add(user)
                await session.flush()
            else:
                user.first_name = first_name
                user.last_name = last_name
                user.password_hash = hash_password(test_password)
                user.is_active = True
                user.deleted_at = None

            role = roles.get(role_name)
            if role is None:
                continue

            user_role_result = await session.execute(
                select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id)
            )
            user_role = user_role_result.scalar_one_or_none()
            if user_role is None:
                session.add(UserRole(user_id=user.id, role_id=role.id))

        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed_local_data())
