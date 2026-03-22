import pytest


@pytest.mark.e2e
@pytest.mark.access
@pytest.mark.mock
@pytest.mark.slow
class TestAccessAdminFlow:
    def test_access_admin_endpoints_and_rule_lifecycle(self, api, created_accounts, e2e_db):
        e2e_db.delete_access_rule(
            role_name="user",
            resource_code="mock:reports:list",
            permission_code="read",
        )

        admin_headers = api.auth_headers(created_accounts["admin1"])
        user_headers = api.auth_headers(created_accounts["user1"])
        manager_headers = api.auth_headers(created_accounts["manager1"])

        forbidden_access_response = api.client.get("/api/v1/access/rules", headers=user_headers)
        assert forbidden_access_response.status_code == 403, forbidden_access_response.text

        roles_response = api.client.get("/api/v1/access/roles", headers=admin_headers)
        resources_response = api.client.get("/api/v1/access/resources", headers=admin_headers)
        permissions_response = api.client.get("/api/v1/access/permissions", headers=admin_headers)
        rules_response = api.client.get("/api/v1/access/rules", headers=admin_headers)

        assert roles_response.status_code == 200, roles_response.text
        assert resources_response.status_code == 200, resources_response.text
        assert permissions_response.status_code == 200, permissions_response.text
        assert rules_response.status_code == 200, rules_response.text

        roles = roles_response.json()
        resources = resources_response.json()
        permissions = permissions_response.json()

        user_role_id = next(item["id"] for item in roles if item["name"] == "user")
        reports_resource_id = next(item["id"] for item in resources if item["code"] == "mock:reports:list")
        read_permission_id = next(item["id"] for item in permissions if item["code"] == "read")

        user_projects_response = api.client.get("/api/v1/mock/projects", headers=user_headers)
        user_reports_response = api.client.get("/api/v1/mock/reports", headers=user_headers)
        user_documents_response = api.client.get(
            "/api/v1/mock/documents",
            headers=user_headers,
        )
        manager_reports_response = api.client.get(
            "/api/v1/mock/reports",
            headers=manager_headers,
        )
        manager_documents_response = api.client.get(
            "/api/v1/mock/documents",
            headers=manager_headers,
        )

        assert user_projects_response.status_code == 200, user_projects_response.text
        assert user_reports_response.status_code == 403, user_reports_response.text
        assert user_documents_response.status_code == 403, user_documents_response.text
        assert manager_reports_response.status_code == 200, manager_reports_response.text
        assert manager_documents_response.status_code == 403, manager_documents_response.text

        rule_id = None
        try:
            create_rule_response = api.client.post(
                "/api/v1/access/rules",
                headers=admin_headers,
                json={
                    "role_id": user_role_id,
                    "resource_id": reports_resource_id,
                    "permission_id": read_permission_id,
                    "is_allowed": True,
                },
            )
            assert create_rule_response.status_code == 201, create_rule_response.text
            created_rule = create_rule_response.json()
            rule_id = created_rule["id"]
            assert created_rule["role_name"] == "user"
            assert created_rule["resource_code"] == "mock:reports:list"
            assert created_rule["permission_code"] == "read"
            assert created_rule["is_allowed"] is True

            user_reports_allowed = api.client.get("/api/v1/mock/reports", headers=user_headers)
            assert user_reports_allowed.status_code == 200, user_reports_allowed.text

            update_rule_response = api.client.patch(
                f"/api/v1/access/rules/{rule_id}",
                headers=admin_headers,
                json={"is_allowed": False},
            )
            assert update_rule_response.status_code == 200, update_rule_response.text
            assert update_rule_response.json()["is_allowed"] is False

            user_reports_forbidden_again = api.client.get(
                "/api/v1/mock/reports",
                headers=user_headers,
            )
            assert user_reports_forbidden_again.status_code == 403, user_reports_forbidden_again.text
        finally:
            if rule_id is not None:
                delete_rule_response = api.client.delete(
                    f"/api/v1/access/rules/{rule_id}",
                    headers=admin_headers,
                )
                assert delete_rule_response.status_code == 200, delete_rule_response.text
                assert delete_rule_response.json() == {"status": "OK"}
            e2e_db.delete_access_rule(
                role_name="user",
                resource_code="mock:reports:list",
                permission_code="read",
            )

        user_reports_after_delete = api.client.get("/api/v1/mock/reports", headers=user_headers)
        assert user_reports_after_delete.status_code == 403, user_reports_after_delete.text
