"""Seed roles, permissions, resources and mock access rules

Revision ID: 20260317_0004
Revises: 20260317_0003
Create Date: 2026-03-17
"""

from typing import Sequence, Union

from alembic import op


revision: str = "20260317_0004"
down_revision: Union[str, None] = "20260317_0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        INSERT INTO roles (name, description) VALUES
            ('admin', 'Administrator'),
            ('manager', 'Manager'),
            ('user', 'Regular user'),
            ('superadmin', 'Super administrator')
        ON CONFLICT (name) DO NOTHING;
        """
    )

    op.execute(
        """
        INSERT INTO permissions (code, description) VALUES
            ('read', 'Read access'),
            ('create', 'Create access'),
            ('update', 'Update access'),
            ('delete', 'Delete access')
        ON CONFLICT (code) DO NOTHING;
        """
    )

    op.execute(
        """
        INSERT INTO resources (code, description) VALUES
            ('mock:projects:list', 'Read mock projects'),
            ('mock:reports:list', 'Read mock reports'),
            ('mock:documents:list', 'Read mock documents')
        ON CONFLICT (code) DO NOTHING;
        """
    )

    op.execute(
        """
        INSERT INTO access_rules (role_id, resource_id, permission_id, is_allowed)
        SELECT
            roles.id,
            resources.id,
            permissions.id,
            TRUE
        FROM roles
        CROSS JOIN permissions
        JOIN resources ON resources.code IN (
            'mock:projects:list',
            'mock:reports:list',
            'mock:documents:list'
        )
        WHERE roles.name = 'superadmin'
          AND permissions.code = 'read'
          AND NOT EXISTS (
            SELECT 1
            FROM access_rules ar
            WHERE ar.role_id = roles.id
              AND ar.resource_id = resources.id
              AND ar.permission_id = permissions.id
          );
        """
    )

    op.execute(
        """
        INSERT INTO access_rules (role_id, resource_id, permission_id, is_allowed)
        SELECT roles.id, resources.id, permissions.id, TRUE
        FROM roles
        JOIN resources ON resources.code IN (
            'mock:projects:list',
            'mock:reports:list',
            'mock:documents:list'
        )
        JOIN permissions ON permissions.code = 'read'
        WHERE roles.name = 'admin'
          AND NOT EXISTS (
            SELECT 1
            FROM access_rules ar
            WHERE ar.role_id = roles.id
              AND ar.resource_id = resources.id
              AND ar.permission_id = permissions.id
          );
        """
    )

    op.execute(
        """
        INSERT INTO access_rules (role_id, resource_id, permission_id, is_allowed)
        SELECT roles.id, resources.id, permissions.id, TRUE
        FROM roles
        JOIN resources ON resources.code IN (
            'mock:projects:list',
            'mock:reports:list'
        )
        JOIN permissions ON permissions.code = 'read'
        WHERE roles.name = 'manager'
          AND NOT EXISTS (
            SELECT 1
            FROM access_rules ar
            WHERE ar.role_id = roles.id
              AND ar.resource_id = resources.id
              AND ar.permission_id = permissions.id
          );
        """
    )

    op.execute(
        """
        INSERT INTO access_rules (role_id, resource_id, permission_id, is_allowed)
        SELECT roles.id, resources.id, permissions.id, TRUE
        FROM roles
        JOIN resources ON resources.code = 'mock:projects:list'
        JOIN permissions ON permissions.code = 'read'
        WHERE roles.name = 'user'
          AND NOT EXISTS (
            SELECT 1
            FROM access_rules ar
            WHERE ar.role_id = roles.id
              AND ar.resource_id = resources.id
              AND ar.permission_id = permissions.id
          );
        """
    )


def downgrade() -> None:
    op.execute(
        """
        DELETE FROM access_rules
        WHERE resource_id IN (
            SELECT id FROM resources
            WHERE code IN ('mock:projects:list', 'mock:reports:list', 'mock:documents:list')
        );
        """
    )
    op.execute(
        """
        DELETE FROM resources
        WHERE code IN ('mock:projects:list', 'mock:reports:list', 'mock:documents:list');
        """
    )

