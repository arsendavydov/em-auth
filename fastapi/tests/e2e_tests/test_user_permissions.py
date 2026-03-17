import pytest


@pytest.mark.e2e
@pytest.mark.users
@pytest.mark.slow
class TestUserPermissions:
    def test_role_based_visibility_update_and_delete(self, api, created_accounts, account_factory):
        temp_user = account_factory(
            role_name="user",
            prefix="e2e_managed",
            first_name="Managed",
            last_name="Candidate",
        )
        temp_user_email = temp_user["email"]
        temp_user_id = temp_user["user"]["id"]

        user_headers = api.auth_headers(created_accounts["user1"])
        user_me_response = api.get_me(user_headers)
        assert user_me_response.status_code == 200, user_me_response.text
        user1_id = user_me_response.json()["id"]

        user_list_response = api.client.get("/api/v1/users", headers=user_headers)
        assert user_list_response.status_code == 200, user_list_response.text
        listed_ids = [item["id"] for item in user_list_response.json()]
        assert listed_ids == [user1_id]

        forbidden_get_response = api.client.get(
            f"/api/v1/users/{temp_user_id}",
            headers=user_headers,
        )
        assert forbidden_get_response.status_code == 403, forbidden_get_response.text

        forbidden_patch_response = api.client.patch(
            f"/api/v1/users/{temp_user_id}",
            headers=user_headers,
            json={"first_name": "Nope"},
        )
        assert forbidden_patch_response.status_code == 403, forbidden_patch_response.text

        manager_headers = api.auth_headers(created_accounts["manager1"])
        manager_list_response = api.client.get("/api/v1/users", headers=manager_headers)
        assert manager_list_response.status_code == 200, manager_list_response.text
        manager_visible_emails = {item["email"] for item in manager_list_response.json()}
        assert created_accounts["manager1"] in manager_visible_emails
        assert created_accounts["manager2"] in manager_visible_emails
        assert created_accounts["user1"] in manager_visible_emails
        assert created_accounts["user2"] in manager_visible_emails
        assert temp_user_email in manager_visible_emails
        assert created_accounts["admin1"] not in manager_visible_emails
        assert created_accounts["admin2"] not in manager_visible_emails

        manager_can_view_user = api.client.get(
            f"/api/v1/users/{user1_id}",
            headers=manager_headers,
        )
        assert manager_can_view_user.status_code == 200, manager_can_view_user.text

        manager_cannot_patch_other = api.client.patch(
            f"/api/v1/users/{temp_user_id}",
            headers=manager_headers,
            json={"first_name": "Blocked"},
        )
        assert manager_cannot_patch_other.status_code == 403, manager_cannot_patch_other.text

        admin_headers = api.auth_headers(created_accounts["admin1"])
        admin_me_response = api.get_me(admin_headers)
        assert admin_me_response.status_code == 200, admin_me_response.text
        admin1_id = admin_me_response.json()["id"]

        manager_cannot_view_admin = api.client.get(
            f"/api/v1/users/{admin1_id}",
            headers=manager_headers,
        )
        assert manager_cannot_view_admin.status_code == 403, manager_cannot_view_admin.text

        admin_updates_temp_user = api.client.patch(
            f"/api/v1/users/{temp_user_id}",
            headers=admin_headers,
            json={"first_name": "AdminUpdated"},
        )
        assert admin_updates_temp_user.status_code == 200, admin_updates_temp_user.text
        assert admin_updates_temp_user.json()["first_name"] == "AdminUpdated"

        admin2_headers = api.auth_headers(created_accounts["admin2"])
        admin2_me_response = api.get_me(admin2_headers)
        assert admin2_me_response.status_code == 200, admin2_me_response.text
        admin2_id = admin2_me_response.json()["id"]

        admin_cannot_update_admin = api.client.patch(
            f"/api/v1/users/{admin2_id}",
            headers=admin_headers,
            json={"first_name": "Forbidden"},
        )
        assert admin_cannot_update_admin.status_code == 403, admin_cannot_update_admin.text

        admin_cannot_delete_admin = api.client.delete(
            f"/api/v1/users/{admin2_id}",
            headers=admin_headers,
        )
        assert admin_cannot_delete_admin.status_code == 403, admin_cannot_delete_admin.text

        admin_deletes_temp_user = api.client.delete(
            f"/api/v1/users/{temp_user_id}",
            headers=admin_headers,
        )
        assert admin_deletes_temp_user.status_code == 200, admin_deletes_temp_user.text
        assert admin_deletes_temp_user.json() == {"status": "OK"}

        deleted_user_login = api.login(temp_user_email)
        assert deleted_user_login.status_code == 401, deleted_user_login.text
