from pathlib import Path
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from terraform_drift.test_helpers import create_orphaned_resource_tests


class TestCreateOrphanedResourceTestsReturnValue:
    def test_returns_a_class(self) -> None:
        result = create_orphaned_resource_tests(Path("/tmp/terraform"))
        assert isinstance(result, type)

    def test_returned_class_has_test_terraform_initialized_method(self) -> None:
        result = create_orphaned_resource_tests(Path("/tmp/terraform"))
        assert hasattr(result, "test_terraform_initialized")

    def test_returned_class_has_test_no_orphaned_resources_method(self) -> None:
        result = create_orphaned_resource_tests(Path("/tmp/terraform"))
        assert hasattr(result, "test_no_orphaned_resources")

    def test_returned_class_methods_are_callable(self) -> None:
        result = create_orphaned_resource_tests(Path("/tmp/terraform"))
        instance = result()
        assert callable(instance.test_terraform_initialized)

    def test_returned_class_has_correct_name(self) -> None:
        result = create_orphaned_resource_tests(Path("/tmp/terraform"))
        assert result.__name__ == "TestOrphanedResources"


class TestTerraformInitialized:
    def test_passes_when_lock_file_exists(self, tmp_path: Path) -> None:
        lock_file = tmp_path / ".terraform.lock.hcl"
        lock_file.touch()

        TestClass = create_orphaned_resource_tests(tmp_path)
        instance = TestClass()

        assert instance.test_terraform_initialized() is None

    def test_fails_when_lock_file_missing(self, tmp_path: Path) -> None:
        TestClass = create_orphaned_resource_tests(tmp_path)
        instance = TestClass()

        with pytest.raises(AssertionError, match="Terraform not initialized"):
            instance.test_terraform_initialized()

    def test_error_message_includes_directory_path(self, tmp_path: Path) -> None:
        TestClass = create_orphaned_resource_tests(tmp_path)
        instance = TestClass()

        with pytest.raises(AssertionError, match=str(tmp_path)):
            instance.test_terraform_initialized()


@patch("terraform_drift.test_helpers.get_planned_creates")
def test_no_orphaned_resources_no_creates(mock_get_planned: MagicMock) -> None:
    mock_get_planned.return_value = []

    TestClass = create_orphaned_resource_tests(Path("/tmp/terraform"))
    instance = TestClass()

    assert instance.test_no_orphaned_resources() is None


def _setup_single_resource_mock(
    mock_get_planned: MagicMock,
    mock_check_exists: MagicMock,
    exists: bool = False
) -> None:
    mock_get_planned.return_value = [
        {
            "type": "aws_lambda_function",
            "name": "MyFunction",
            "address": "aws_lambda_function.my_func",
        }
    ]
    mock_check_exists.return_value = exists


class TestNoOrphanedResourcesNoOrphans:
    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_passes_when_resources_do_not_exist_in_aws(
        self, mock_get_planned: MagicMock, mock_check_exists: MagicMock
    ) -> None:
        _setup_single_resource_mock(mock_get_planned, mock_check_exists)

        TestClass = create_orphaned_resource_tests(Path("/tmp/terraform"))
        instance = TestClass()

        assert instance.test_no_orphaned_resources() is None

    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_calls_check_resource_exists_with_correct_type(
        self, mock_get_planned: MagicMock, mock_check_exists: MagicMock
    ) -> None:
        _setup_single_resource_mock(mock_get_planned, mock_check_exists)

        TestClass = create_orphaned_resource_tests(
            Path("/tmp/terraform"), region="us-west-2"
        )
        instance = TestClass()
        instance.test_no_orphaned_resources()

        assert mock_check_exists.call_args[0][0] == "aws_lambda_function"

    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_calls_check_resource_exists_with_correct_name(
        self, mock_get_planned: MagicMock, mock_check_exists: MagicMock
    ) -> None:
        _setup_single_resource_mock(mock_get_planned, mock_check_exists)

        TestClass = create_orphaned_resource_tests(
            Path("/tmp/terraform"), region="us-west-2"
        )
        instance = TestClass()
        instance.test_no_orphaned_resources()

        assert mock_check_exists.call_args[0][1] == "MyFunction"

    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_calls_check_resource_exists_with_correct_region(
        self, mock_get_planned: MagicMock, mock_check_exists: MagicMock
    ) -> None:
        _setup_single_resource_mock(mock_get_planned, mock_check_exists)

        TestClass = create_orphaned_resource_tests(
            Path("/tmp/terraform"), region="us-west-2"
        )
        instance = TestClass()
        instance.test_no_orphaned_resources()

        assert mock_check_exists.call_args[0][2] == "us-west-2"

    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_uses_default_region_when_not_specified(
        self, mock_get_planned: MagicMock, mock_check_exists: MagicMock
    ) -> None:
        _setup_single_resource_mock(mock_get_planned, mock_check_exists)

        TestClass = create_orphaned_resource_tests(Path("/tmp/terraform"))
        instance = TestClass()
        instance.test_no_orphaned_resources()

        assert mock_check_exists.call_args[0][2] == "us-east-2"


class TestNoOrphanedResourcesWithOrphans:
    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_fails_when_orphaned_resource_detected(
        self, mock_get_planned: MagicMock, mock_check_exists: MagicMock
    ) -> None:
        _setup_single_resource_mock(mock_get_planned, mock_check_exists, exists=True)

        TestClass = create_orphaned_resource_tests(Path("/tmp/terraform"))
        instance = TestClass()

        with pytest.raises(pytest.fail.Exception):
            instance.test_no_orphaned_resources()

    @patch("terraform_drift.test_helpers.check_resource_exists")
    @patch("terraform_drift.test_helpers.get_planned_creates")
    def test_failure_message_includes_orphaned_count(
        self, mock_get_planned: MagicMock, mock_check_exists: MagicMock
    ) -> None:
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
        self, mock_get_planned: MagicMock, mock_check_exists: MagicMock
    ) -> None:
        _setup_single_resource_mock(mock_get_planned, mock_check_exists, exists=True)

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
        self, mock_get_planned: MagicMock, mock_check_exists: MagicMock
    ) -> None:
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
        mock_check_exists.side_effect = [True, False]

        TestClass = create_orphaned_resource_tests(Path("/tmp/terraform"))
        instance = TestClass()

        with pytest.raises(pytest.fail.Exception, match=r"ORPHANED RESOURCES DETECTED \(1\)"):
            instance.test_no_orphaned_resources()


@patch("terraform_drift.test_helpers.get_planned_creates")
def test_get_planned_creates_integration(mock_get_planned: MagicMock) -> None:
    mock_get_planned.return_value = []
    terraform_dir = Path("/tmp/my-terraform")

    TestClass = create_orphaned_resource_tests(terraform_dir)
    instance = TestClass()
    instance.test_no_orphaned_resources()

    assert mock_get_planned.call_args[0][0] == terraform_dir


@patch("terraform_drift.test_helpers.check_resource_exists")
@patch("terraform_drift.test_helpers.get_planned_creates")
def test_multiple_resources(mock_get_planned: MagicMock, mock_check_exists: MagicMock) -> None:
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
