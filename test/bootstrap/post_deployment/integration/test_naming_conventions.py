"""Integration tests to verify deployed IAM roles use PascalCase.

These tests query AWS to validate that deployed resources follow naming conventions.
Names must use PascalCase (no dashes, underscores, or other separators).
"""
import pytest

from naming_conventions import validate_name


class TestDeployedIAMRoleNamingConventions:
    """Tests for deployed IAM role naming conventions in bootstrap."""

    def test_github_actions_role_exists(self, iam_client, config):
        """Verify GitHub Actions IAM role exists."""
        role_name = config.get('name_for_github_actions_role', 'TenULabsGitHubActionsRole')
        try:
            iam_client.get_role(RoleName=role_name)
        except iam_client.exceptions.NoSuchEntityException:
            pytest.fail(f"IAM role '{role_name}' does not exist")

    def test_github_actions_role_name_is_pascalcase(self, iam_client, config):
        """Verify GitHub Actions IAM role name uses PascalCase."""
        role_name = config.get('name_for_github_actions_role', 'TenULabsGitHubActionsRole')
        response = iam_client.get_role(RoleName=role_name)
        actual_name = response['Role']['RoleName']
        error = validate_name(actual_name)
        assert error is None, (
            f"Deployed IAM role has invalid name '{actual_name}': {error}"
        )
