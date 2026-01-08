"""Unit tests for re-export modules in EC2 runner Lambda."""
import sys


class TestClientsReexport:
    """Tests for clients.py re-export module."""

    def test_clients_imports_get_ec2_client(self, ec2_runner_handler):
        """Verify get_ec2_client is re-exported from aws_clients."""
        _ = ec2_runner_handler  # ensure handler loaded
        from clients import get_ec2_client  # type: ignore[import-not-found]
        assert callable(get_ec2_client)

    def test_clients_imports_get_ssm_client(self, ec2_runner_handler):
        """Verify get_ssm_client is re-exported from aws_clients."""
        _ = ec2_runner_handler
        from clients import get_ssm_client  # type: ignore[import-not-found]
        assert callable(get_ssm_client)

    def test_clients_imports_get_dynamodb_client(self, ec2_runner_handler):
        """Verify get_dynamodb_client is re-exported from aws_clients."""
        _ = ec2_runner_handler
        from clients import get_dynamodb_client  # type: ignore[import-not-found]
        assert callable(get_dynamodb_client)

    def test_clients_imports_set_client(self, ec2_runner_handler):
        """Verify set_client is re-exported from aws_clients."""
        _ = ec2_runner_handler
        from clients import set_client  # type: ignore[import-not-found]
        assert callable(set_client)

    def test_clients_imports_reset_clients(self, ec2_runner_handler):
        """Verify reset_clients is re-exported from aws_clients."""
        _ = ec2_runner_handler
        from clients import reset_clients  # type: ignore[import-not-found]
        assert callable(reset_clients)


class TestGithubReexport:
    """Tests for github.py re-export module."""

    def test_github_imports_build_runner_labels(self, ec2_runner_handler):
        """Verify build_runner_labels is re-exported from github_runner_api."""
        _ = ec2_runner_handler
        from github import build_runner_labels  # type: ignore[import-not-found]
        assert callable(build_runner_labels)

    def test_github_imports_cleanup_offline_runners(self, ec2_runner_handler):
        """Verify cleanup_offline_runners is re-exported from github_runner_api."""
        _ = ec2_runner_handler
        from github import cleanup_offline_runners  # type: ignore[import-not-found]
        assert callable(cleanup_offline_runners)

    def test_github_imports_delete_runner(self, ec2_runner_handler):
        """Verify delete_runner is re-exported from github_runner_api."""
        _ = ec2_runner_handler
        from github import delete_runner  # type: ignore[import-not-found]
        assert callable(delete_runner)

    def test_github_imports_get_existing_runner_for_workflow(self, ec2_runner_handler):
        """Verify get_existing_runner_for_workflow is re-exported from github_runner_api."""
        _ = ec2_runner_handler
        from github import get_existing_runner_for_workflow  # type: ignore[import-not-found]
        assert callable(get_existing_runner_for_workflow)

    def test_github_imports_get_github_token(self, ec2_runner_handler):
        """Verify get_github_token is re-exported from github_runner_api."""
        _ = ec2_runner_handler
        from github import get_github_token  # type: ignore[import-not-found]
        assert callable(get_github_token)

    def test_github_imports_get_runner_registration_token(self, ec2_runner_handler):
        """Verify get_runner_registration_token is re-exported from github_runner_api."""
        _ = ec2_runner_handler
        from github import get_runner_registration_token  # type: ignore[import-not-found]
        assert callable(get_runner_registration_token)

    def test_github_imports_list_repo_runners(self, ec2_runner_handler):
        """Verify list_repo_runners is re-exported from github_runner_api."""
        _ = ec2_runner_handler
        from github import list_repo_runners  # type: ignore[import-not-found]
        assert callable(list_repo_runners)

    def test_github_imports_reset_github_token_cache(self, ec2_runner_handler):
        """Verify reset_github_token_cache is re-exported from github_runner_api."""
        _ = ec2_runner_handler
        from github import reset_github_token_cache  # type: ignore[import-not-found]
        assert callable(reset_github_token_cache)


class TestResponsesReexport:
    """Tests for responses.py re-export module."""

    def test_responses_imports_json_response(self, ec2_runner_handler):
        """Verify json_response is re-exported from lambda_http."""
        _ = ec2_runner_handler
        from responses import json_response  # type: ignore[import-not-found]
        assert callable(json_response)

    def test_responses_imports_success_response(self, ec2_runner_handler):
        """Verify success_response is re-exported from lambda_http."""
        _ = ec2_runner_handler
        from responses import success_response  # type: ignore[import-not-found]
        assert callable(success_response)

    def test_responses_imports_error_response(self, ec2_runner_handler):
        """Verify error_response is re-exported from lambda_http."""
        _ = ec2_runner_handler
        from responses import error_response  # type: ignore[import-not-found]
        assert callable(error_response)

    def test_responses_imports_parse_body(self, ec2_runner_handler):
        """Verify parse_body is re-exported from lambda_http."""
        _ = ec2_runner_handler
        from responses import parse_body  # type: ignore[import-not-found]
        assert callable(parse_body)

    def test_responses_imports_is_capacity_error(self, ec2_runner_handler):
        """Verify is_capacity_error is re-exported from lambda_http."""
        _ = ec2_runner_handler
        from responses import is_capacity_error  # type: ignore[import-not-found]
        assert callable(is_capacity_error)


class TestValidationReexport:
    """Tests for validation.py re-export module."""

    def test_validation_imports_get_api_key(self, ec2_runner_handler):
        """Verify get_api_key is re-exported from infra_validation."""
        _ = ec2_runner_handler
        from validation import get_api_key  # type: ignore[import-not-found]
        assert callable(get_api_key)

    def test_validation_imports_validate_security_groups(self, ec2_runner_handler):
        """Verify validate_security_groups is re-exported from infra_validation."""
        _ = ec2_runner_handler
        from validation import validate_security_groups  # type: ignore[import-not-found]
        assert callable(validate_security_groups)

    def test_validation_imports_validate_subnets(self, ec2_runner_handler):
        """Verify validate_subnets is re-exported from infra_validation."""
        _ = ec2_runner_handler
        from validation import validate_subnets  # type: ignore[import-not-found]
        assert callable(validate_subnets)

    def test_validation_imports_validate_vpc(self, ec2_runner_handler):
        """Verify validate_vpc is re-exported from infra_validation."""
        _ = ec2_runner_handler
        from validation import validate_vpc  # type: ignore[import-not-found]
        assert callable(validate_vpc)

    def test_validation_imports_validate_all_dependencies(self, ec2_runner_handler):
        """Verify validate_all_dependencies is re-exported from infra_validation."""
        _ = ec2_runner_handler
        from validation import validate_all_dependencies  # type: ignore[import-not-found]
        assert callable(validate_all_dependencies)

    def test_validation_imports_ensure_dependencies_valid(self, ec2_runner_handler):
        """Verify ensure_dependencies_valid is re-exported from infra_validation."""
        _ = ec2_runner_handler
        from validation import ensure_dependencies_valid  # type: ignore[import-not-found]
        assert callable(ensure_dependencies_valid)

    def test_validation_imports_reset_dependency_validation(self, ec2_runner_handler):
        """Verify reset_dependency_validation is re-exported from infra_validation."""
        _ = ec2_runner_handler
        from validation import reset_dependency_validation  # type: ignore[import-not-found]
        assert callable(reset_dependency_validation)

    def test_validation_imports_get_dependencies_status(self, ec2_runner_handler):
        """Verify get_dependencies_status is re-exported from infra_validation."""
        _ = ec2_runner_handler
        from validation import get_dependencies_status  # type: ignore[import-not-found]
        assert callable(get_dependencies_status)

    def test_validation_imports_set_dependencies_status(self, ec2_runner_handler):
        """Verify set_dependencies_status is re-exported from infra_validation."""
        _ = ec2_runner_handler
        from validation import set_dependencies_status  # type: ignore[import-not-found]
        assert callable(set_dependencies_status)

    def test_validation_imports_reset_api_key_cache(self, ec2_runner_handler):
        """Verify reset_api_key_cache is re-exported from infra_validation."""
        _ = ec2_runner_handler
        from validation import reset_api_key_cache  # type: ignore[import-not-found]
        assert callable(reset_api_key_cache)
