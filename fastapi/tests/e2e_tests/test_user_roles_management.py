import pytest


@pytest.mark.e2e
@pytest.mark.users
@pytest.mark.slow
class TestUserRolesManagement:
    def test_superadmin_and_admin_can_manage_roles(self, api, account_factory):
        # готовим супер-админа и обычного пользователя
        super_account = account_factory(role_name="superadmin", prefix="e2e_superadmin")
        target_account = account_factory(role_name=None, prefix="e2e_target_user")

        super_email = super_account["email"]
        target_user = target_account["user"]
        target_id = target_user["id"]

        super_headers = api.auth_headers(super_email)

        # назначаем роль admin целевому пользователю
        assign_response = api.client.post(
            f"/api/v1/users/{target_id}/roles/admin",
            headers=super_headers,
        )
        assert assign_response.status_code == 200, assign_response.text
        assigned_payload = assign_response.json()
        assert "admin" in assigned_payload["roles"]

        # логинимся как новый админ и проверяем, что он может видеть список пользователей
        admin_headers = api.auth_headers(target_account["email"])
        list_response = api.client.get("/api/v1/users", headers=admin_headers)
        assert list_response.status_code == 200, list_response.text

        # новый админ может назначить обычную роль пользователю
        another_user = account_factory(role_name=None, prefix="e2e_another_user")
        another_id = another_user["user"]["id"]
        assign_user_role_response = api.client.post(
            f"/api/v1/users/{another_id}/roles/user",
            headers=admin_headers,
        )
        assert assign_user_role_response.status_code == 200, assign_user_role_response.text
        assert "user" in assign_user_role_response.json()["roles"]

    def test_admin_cannot_assign_or_manage_superadmin_role(self, api, account_factory):
        # супер-админ и админ
        super_account = account_factory(role_name="superadmin", prefix="e2e_superadmin2")
        admin_account = account_factory(role_name="admin", prefix="e2e_admin_for_roles")

        super_email = super_account["email"]
        admin_email = admin_account["email"]
        admin_id = admin_account["user"]["id"]

        admin_headers = api.auth_headers(admin_email)
        super_headers = api.auth_headers(super_email)

        # админ не может назначить роль superadmin себе
        assign_super_response = api.client.post(
            f"/api/v1/users/{admin_id}/roles/superadmin",
            headers=admin_headers,
        )
        assert assign_super_response.status_code == 403, assign_super_response.text

        # супер-админ может управлять ролями админа
        remove_admin_role_response = api.client.delete(
            f"/api/v1/users/{admin_id}/roles/admin",
            headers=super_headers,
        )
        assert remove_admin_role_response.status_code == 200, remove_admin_role_response.text
        assert "admin" not in remove_admin_role_response.json()["roles"]

