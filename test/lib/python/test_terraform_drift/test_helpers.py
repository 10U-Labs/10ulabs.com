"""Comprehensive tests for terraform_drift.test_helpers module."""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from terraform_drift.test_helpers import create_orphaned_resource_tests


class TestCreateOrphanedResourceTestsReturnValue:
    """Tests for the return value of create_orphaned_resource_tests."""

    def test_returns_a_class(self):
        """create_orphaned_resource_tests returns a class."""
        result = create_orphaned_resource_tests(Path("/tmp/terraform"))
        assert isinstance(result, type)

    def test_returned_class_has_test_terraform_initialized_method(self):
        """Returned class has test_terraform_initialized method."""
        result = create_orphaned_resource_tests(Path("/tmp/terraform"))
        assert hasattr(result, "test_terraform_initialized")

    def test_returned_class_has_test_no_orphaned_resources_method(self):
        """Returned class has test_no_orphaned_resources method."""
        result = create_orphaned_resource_tests(Path("/tmp/terraform"))
        assert hasattr(result, "test_no_orphaned_resources")

    def test_returned_class_methods_are_callable(self):
        """Returned class methods are callable."""
        result = create_orphaned_resource_tests(Path("/tmp/terraform"))
        instance = result()
        assert callable(instance.test_terraform_initialized)

    def test_returned_class_has_correct_name(self):
        """Returned class has the name TestOrphanedResources."""
        result = create_orphaned_resource_tests(Path("/tmp/terraform"))
        assert result.__name__ == "TestOrphanedResources"


class TestTerraformInitialized:
    """Tests for the test_terraform_initialized method."""

    def test_passes_when_lock_file_exists(self, tmp_path):
        """test_terraform_initialized passes when .terraform.lock.hcl exists."""
        # Create the lock file
        lock_file = tmp_path / ".terraform.lock.hcl"
        lock_file.touch()

        TestClass = create_orphaned_resource_tests(tmp_path)
        instance = TestClass()

        # Should not raise any exception
        instance.test_terraform_initialized()

    def test_fails_when_lock_file_missing(self, tmp_path):
        """test_terraform_initialized fails when .terraform.lock.hcl doesn't exist."""
        TestClass = create_orphaned_resource_tests(tmp_path)
        instance = TestClass()

        with pytest.raises(AssertionError, match="Terraform not initialized"):
            instance.test_terraform_initialized()

    def test_error_message_includes_directory_path(self, tmp_path):
        """test_terraform_initialized error message includes the directory path."""
        TestClass = create_orphaned_resource_tests(tmp_path)
        instance = TestClass()

        with pytest.raises(AssertionError, match=str(tmp_path)):
            instance.test_terraform_initialized()


class TestNoOrphanedResourcesNoCreates:
    """Tests for test_no_orphaned_resources when there are no creates."""

    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_passes_when_no_creates(self, mock_get_planned):
        """test_no_orphaned_resources passes when no resources to create."""
        mock_get_planned.return_value = []

        TestClass = create_orphaned_resource_tests(Path("/tmp/terraform"))
        instance = TestClass()

        # Should not raise any exception
        instance.test_no_orphaned_resources()


class TestNoOrphanedResourcesNoOrphans:
    """Tests for test_no_orphaned_resources when there are creates but no orphans."""

    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_passes_when_resources_do_not_exist_in_aws(
        self, mock_get_planned, mock_check_exists
    ):
        """test_no_orphaned_resources passes when planned resources don't exist in AWS."""
        mock_get_planned.return_value = [
            {
                "type": "aws_lambda_function",
                "name": "MyFunction",
                "address": "aws_lambda_function.my_func",
            }
        ]
        mock_check_exists.return_value = False

        TestClass = create_orphaned_resource_tests(Path("/tmp/terraform"))
        instance = TestClass()

        # Should not raise any exception
        instance.test_no_orphaned_resources()

    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_calls_check_resource_exists_with_correct_type(
        self, mock_get_planned, mock_check_exists
    ):
        """test_no_orphaned_resources calls check_resource_exists with correct type."""
        mock_get_planned.return_value = [
            {
                "type": "aws_lambda_function",
                "name": "MyFunction",
                "address": "aws_lambda_function.my_func",
            }
        ]
        mock_check_exists.return_value = False

        TestClass = create_orphaned_resource_tests(
            Path("/tmp/terraform"), region="us-west-2"
        )
        instance = TestClass()
        instance.test_no_orphaned_resources()

        assert mock_check_exists.call_args[0][0] == "aws_lambda_function"

    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_calls_check_resource_exists_with_correct_name(
        self, mock_get_planned, mock_check_exists
    ):
        """test_no_orphaned_resources calls check_resource_exists with correct name."""
        mock_get_planned.return_value = [
            {
                "type": "aws_lambda_function",
                "name": "MyFunction",
                "address": "aws_lambda_function.my_func",
            }
        ]
        mock_check_exists.return_value = False

        TestClass = create_orphaned_resource_tests(
            Path("/tmp/terraform"), region="us-west-2"
        )
        instance = TestClass()
        instance.test_no_orphaned_resources()

        assert mock_check_exists.call_args[0][1] == "MyFunction"

    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_calls_check_resource_exists_with_correct_region(
        self, mock_get_planned, mock_check_exists
    ):
        """test_no_orphaned_resources calls check_resource_exists with correct region."""
        mock_get_planned.return_value = [
            {
                "type": "aws_lambda_function",
                "name": "MyFunction",
                "address": "aws_lambda_function.my_func",
            }
        ]
        mock_check_exists.return_value = False

        TestClass = create_orphaned_resource_tests(
            Path("/tmp/terraform"), region="us-west-2"
        )
        instance = TestClass()
        instance.test_no_orphaned_resources()

        assert mock_check_exists.call_args[0][2] == "us-west-2"

    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_uses_default_region_when_not_specified(
        self, mock_get_planned, mock_check_exists
    ):
        """test_no_orphaned_resources uses default region us-east-2 when not specified."""
        mock_get_planned.return_value = [
            {
                "type": "aws_lambda_function",
                "name": "MyFunction",
                "address": "aws_lambda_function.my_func",
            }
        ]
        mock_check_exists.return_value = False

        TestClass = create_orphaned_resource_tests(Path("/tmp/terraform"))
        instance = TestClass()
        instance.test_no_orphaned_resources()

        assert mock_check_exists.call_args[0][2] == "us-east-2"


class TestNoOrphanedResourcesWithOrphans:
    """Tests for test_no_orphaned_resources when orphans are detected."""

    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_fails_when_orphaned_resource_detected(
        self, mock_get_planned, mock_check_exists
    ):
        """test_no_orphaned_resources fails when resource exists in AWS."""
        mock_get_planned.return_value = [
            {
                "type": "aws_lambda_function",
                "name": "MyFunction",
                "address": "aws_lambda_function.my_func",
            }
        ]
        mock_check_exists.return_value = True

        TestClass = create_orphaned_resource_tests(Path("/tmp/terraform"))
        instance = TestClass()

        with pytest.raises(pytest.fail.Exception):
            instance.test_no_orphaned_resources()

    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_failure_message_includes_orphaned_count(
        self, mock_get_planned, mock_check_exists
    ):
        """test_no_orphaned_resources failure message includes count of orphaned resources."""
        mock_get_planned.return_value = [
            {
                "type": "aws_lambda_function",
                "name": "MyFunction",
                "address": "aws_lambda_function.my_func",
            },
            {
                "type": "aws_iam_role",
                "name": "MyRole",
                "address": "aws_iam_role.my_role",
            },
        ]
        mock_check_exists.return_value = True

        TestClass = create_orphaned_resource_tests(Path("/tmp/terraform"))
        instance = TestClass()

        with pytest.raises(pytest.fail.Exception, match=r"ORPHANED RESOURCES DETECTED \(2\)"):
            instance.test_no_orphaned_resources()

    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_failure_message_includes_import_commands(
        self, mock_get_planned, mock_check_exists
    ):
        """test_no_orphaned_resources failure message includes terraform import commands."""
        mock_get_planned.return_value = [
            {
                "type": "aws_lambda_function",
                "name": "MyFunction",
                "address": "aws_lambda_function.my_func",
            }
        ]
        mock_check_exists.return_value = True

        TestClass = create_orphaned_resource_tests(Path("/tmp/terraform"))
        instance = TestClass()

        with pytest.raises(
            pytest.fail.Exception,
            match="terraform import aws_lambda_function.my_func MyFunction",
        ):
            instance.test_no_orphaned_resources()

    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_only_fails_for_resources_that_exist(
        self, mock_get_planned, mock_check_exists
    ):
        """test_no_orphaned_resources only reports resources that exist in AWS."""
        mock_get_planned.return_value = [
            {
                "type": "aws_lambda_function",
                "name": "ExistingFunction",
                "address": "aws_lambda_function.existing_func",
            },
            {
                "type": "aws_iam_role",
                "name": "NonExistingRole",
                "address": "aws_iam_role.non_existing_role",
            },
        ]
        # First resource exists, second does not
        mock_check_exists.side_effect = [True, False]

        TestClass = create_orphaned_resource_tests(Path("/tmp/terraform"))
        instance = TestClass()

        with pytest.raises(pytest.fail.Exception, match=r"ORPHANED RESOURCES DETECTED \(1\)"):
            instance.test_no_orphaned_resources()


class TestGetPlannedCreatesIntegration:
    """Tests for get_planned_creates being called correctly."""

    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_calls_get_planned_creates_with_terraform_dir(self, mock_get_planned):
        """test_no_orphaned_resources calls get_planned_creates with terraform dir."""
        mock_get_planned.return_value = []
        terraform_dir = Path("/tmp/my-terraform")

        TestClass = create_orphaned_resource_tests(terraform_dir)
        instance = TestClass()
        instance.test_no_orphaned_resources()

        assert mock_get_planned.call_args[0][0] == terraform_dir


class TestMultipleResources:
    """Tests for handling multiple resources."""

    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_checks_all_resources(self, mock_get_planned, mock_check_exists):
        """test_no_orphaned_resources checks all planned resources."""
        mock_get_planned.return_value = [
            {
                "type": "aws_lambda_function",
                "name": "Function1",
                "address": "aws_lambda_function.func1",
            },
            {
                "type": "aws_lambda_function",
                "name": "Function2",
                "address": "aws_lambda_function.func2",
            },
            {
                "type": "aws_iam_role",
                "name": "Role1",
                "address": "aws_iam_role.role1",
            },
        ]
        mock_check_exists.return_value = False

        TestClass = create_orphaned_resource_tests(Path("/tmp/terraform"))
        instance = TestClass()
        instance.test_no_orphaned_resources()

        assert mock_check_exists.call_count == 3
