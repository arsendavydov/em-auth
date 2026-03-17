import time

import pytest


@pytest.mark.e2e
@pytest.mark.auth
@pytest.mark.slow
class TestAuthLifecycle:
    def test_registered_user_full_lifecycle(self, api, account_factory):
        created_account = account_factory(
            prefix="e2e_lifecycle",
            first_name="Lifecycle",
            last_name="User",
        )
        fresh_email = created_account["email"]
        register_response = created_account["response"]

        created_user = register_response.json()
        assert created_user["email"] == fresh_email
        assert created_user["roles"] == []
        assert created_user["deleted_at"] is None

        login_response = api.login(fresh_email)
        assert login_response.status_code == 200, login_response.text
        login_payload = login_response.json()
        access_token = login_payload["access_token"]
        refresh_token = login_payload["refresh_token"]
        headers = {"Authorization": f"Bearer {access_token}"}

        me_response = api.get_me(headers)
        assert me_response.status_code == 200, me_response.text
        assert me_response.json()["email"] == fresh_email

        update_response = api.client.patch(
            "/api/v1/users/me",
            headers=headers,
            json={"first_name": "Updated", "last_name": "Lifecycle"},
        )
        assert update_response.status_code == 200, update_response.text
        assert update_response.json()["first_name"] == "Updated"

        time.sleep(1.1)
        refresh_response = api.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert refresh_response.status_code == 200, refresh_response.text
        refreshed_payload = refresh_response.json()
        refreshed_access_token = refreshed_payload["access_token"]
        refreshed_refresh_token = refreshed_payload["refresh_token"]
        refreshed_headers = {"Authorization": f"Bearer {refreshed_access_token}"}

        reused_refresh_response = api.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert reused_refresh_response.status_code == 401, reused_refresh_response.text

        logout_response = api.client.post(
            "/api/v1/auth/logout",
            headers=refreshed_headers,
        )
        assert logout_response.status_code == 200, logout_response.text
        assert logout_response.json() == {"status": "OK"}

        revoked_refresh_response = api.client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refreshed_refresh_token},
        )
        assert revoked_refresh_response.status_code == 401, revoked_refresh_response.text

        delete_response = api.client.delete(
            "/api/v1/users/me",
            headers=refreshed_headers,
        )
        assert delete_response.status_code == 200, delete_response.text
        assert delete_response.json() == {"status": "OK"}

        me_after_delete_response = api.get_me(refreshed_headers)
        assert me_after_delete_response.status_code == 401, me_after_delete_response.text

        login_after_delete_response = api.login(fresh_email)
        assert login_after_delete_response.status_code == 401, login_after_delete_response.text
