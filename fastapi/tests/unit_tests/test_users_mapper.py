from datetime import UTC, datetime

from src.models.users import User
from src.repositories.mappers.users_mapper import UsersMapper
from src.schemas.users import UserCreate, UserUpdate


def test_to_schema_maps_user_model_to_user_read():
    now = datetime.now(UTC)
    user = User(
        id=10,
        email="mapper@em.ru",
        first_name="Map",
        last_name="Per",
        middle_name="Test",
        password_hash="hashed",
        is_active=True,
        created_at=now,
        updated_at=now,
        deleted_at=None,
    )

    result = UsersMapper.to_schema(user, roles=["admin"])

    assert result.id == 10
    assert result.email == "mapper@em.ru"
    assert result.first_name == "Map"
    assert result.last_name == "Per"
    assert result.middle_name == "Test"
    assert result.is_active is True
    assert result.created_at == now
    assert result.updated_at == now
    assert result.deleted_at is None
    assert result.roles == ["admin"]


def test_from_schema_maps_user_create_with_excludes_and_kwargs():
    schema = UserCreate(
        email="create@em.ru",
        first_name="Create",
        last_name="User",
        middle_name=None,
        password="password123",
        password_confirm="password123",
    )

    result = UsersMapper.from_schema(
        schema,
        exclude={"password", "password_confirm"},
        password_hash="hashed",
    )

    assert result == {
        "email": "create@em.ru",
        "first_name": "Create",
        "last_name": "User",
        "middle_name": None,
        "password_hash": "hashed",
    }


def test_from_schema_respects_exclude_unset_for_user_update():
    schema = UserUpdate(first_name="Updated")

    result = UsersMapper.from_schema(schema)

    assert result == {"first_name": "Updated"}
