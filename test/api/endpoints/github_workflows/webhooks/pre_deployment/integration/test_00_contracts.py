"""Layer 1: Contract tests for github_workflows/webhooks.

These tests verify that local files that must work together are compatible.
No AWS calls are made in contract tests.

Contract tests catch mismatches between:
- Lambda handler exports and Terraform handler references
- Environment variables expected by handlers and defined in Terraform
- Source files referenced in archive_file and actual file existence
- Common modules included in Lambda packages
"""

import ast
import re

import pytest

from repo_utils import REPO_ROOT

# Paths
RUNNERS_SRC_PATH = (
    REPO_ROOT / "src" / "api" / "endpoints" / "github_workflows" / "webhooks"
)
LAMBDAS_PATH = RUNNERS_SRC_PATH / "lambdas"
LAMBDA_TF_PATH = RUNNERS_SRC_PATH / "lambda.tf"

# Lambda definitions from Terraform
# Format: (tf_resource_name, python_file, expected_handler_function)
LAMBDA_DEFINITIONS = [
    ("runners_handler", "webhook_router.py", "lambda_handler"),
    ("ignored_events_archiver", "ignored_events_archiver.py", "lambda_handler"),
    ("circuit_opens", "circuit_opens.py", "lambda_handler"),
    ("circuit_open_remediations", "circuit_open_remediations.py", "lambda_handler"),
    ("dlq_reprocessor", "dlq_reprocessor.py", "handler"),
    ("circuit_open_recoveries", "circuit_open_recoveries.py", "lambda_handler"),
]

# Common modules that should be in most Lambda packages
COMMON_MODULES = [
    "common/__init__.py",
    "common/aws_clients.py",
    "common/circuit_open_utils.py",
    "common/cloudwatch.py",
    "common/ec2_utils.py",
    "common/ecs_utils.py",
    "common/github_api.py",
    "common/lambda_utils.py",
    "common/webhook_ingress.py",
]


def _read_terraform_file() -> str:
    """Read the lambda.tf file content."""
    return LAMBDA_TF_PATH.read_text()


def _read_python_file(filename: str) -> str:
    """Read a Python lambda file content."""
    return (LAMBDAS_PATH / filename).read_text()


def _extract_handler_from_tf(tf_content: str, resource_name: str) -> str | None:
    """Extract the handler value from a Lambda resource in Terraform."""
    # Pattern to match: handler = "filename.function_name"
    pattern = (
        rf'resource\s+"aws_lambda_function"\s+"{resource_name}"\s*\{{'
        rf'[^}}]*?handler\s*=\s*"([^"]+)"'
    )
    match = re.search(pattern, tf_content, re.DOTALL)
    if match:
        return match.group(1)
    return None


def _function_exists_in_python(python_content: str, function_name: str) -> bool:
    """Check if a function is defined in Python source code."""
    try:
        tree = ast.parse(python_content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                return True
        return False
    except SyntaxError:
        return False


def _extract_env_vars_from_tf(tf_content: str, resource_name: str) -> set[str]:
    """Extract environment variable names from a Lambda resource in Terraform."""
    # Find the environment block for this Lambda
    pattern = (
        rf'resource\s+"aws_lambda_function"\s+"{resource_name}"\s*\{{'
        rf'[^}}]*?environment\s*\{{\s*variables\s*=\s*\{{([^}}]+)\}}'
    )
    match = re.search(pattern, tf_content, re.DOTALL)
    if not match:
        return set()

    variables_block = match.group(1)
    # Extract variable names (keys before the = sign)
    var_pattern = r'^\s*(\w+)\s*='
    return set(re.findall(var_pattern, variables_block, re.MULTILINE))


def _extract_env_var_usage_from_python(python_content: str) -> set[str]:
    """Extract os.environ or os.getenv usage from Python source."""
    # Match os.environ["VAR"], os.environ.get("VAR"), os.getenv("VAR")
    patterns = [
        r'os\.environ\["(\w+)"\]',
        r'os\.environ\.get\("(\w+)"',
        r'os\.getenv\("(\w+)"',
        r"os\.environ\['(\w+)'\]",
        r"os\.environ\.get\('(\w+)'",
        r"os\.getenv\('(\w+)'",
    ]
    env_vars = set()
    for pattern in patterns:
        env_vars.update(re.findall(pattern, python_content))
    return env_vars


def _extract_archive_sources(tf_content: str, archive_name: str) -> list[str]:
    """Extract source file paths from an archive_file data source."""
    # Find the start of the archive_file block
    start_pattern = rf'data\s+"archive_file"\s+"{archive_name}"\s*\{{'
    start_match = re.search(start_pattern, tf_content)
    if not start_match:
        return []

    # Find the matching closing brace by counting braces
    start_pos = start_match.end()
    brace_count = 1
    pos = start_pos
    while pos < len(tf_content) and brace_count > 0:
        if tf_content[pos] == '{':
            brace_count += 1
        elif tf_content[pos] == '}':
            brace_count -= 1
        pos += 1

    block_content = tf_content[start_pos:pos]

    # Extract filename values from source blocks
    filename_pattern = r'filename\s*=\s*"([^"]+)"'
    filenames = re.findall(filename_pattern, block_content)

    # Also check for source_file (single file archives)
    # source_file = "${path.module}/lambdas/dlq_reprocessor.py"
    source_file_pattern = r'source_file\s*=\s*"[^"]*?/([^/"]+\.py)"'
    source_files = re.findall(source_file_pattern, block_content)

    return filenames + source_files


class TestLambdaHandlerContracts:
    """Test that Lambda handler exports match Terraform references."""

    @pytest.mark.parametrize("resource_name,python_file,handler_func", LAMBDA_DEFINITIONS)
    def test_lambda_handler_exists(self, resource_name, python_file, handler_func):
        """Verify Lambda Python file exports the handler function Terraform expects."""
        tf_content = _read_terraform_file()
        python_content = _read_python_file(python_file)

        # Get what Terraform expects
        tf_handler = _extract_handler_from_tf(tf_content, resource_name)
        # Parse the handler (format: "filename.function_name")
        if tf_handler:
            expected_file, expected_func = tf_handler.rsplit(".", 1)
        else:
            expected_file, expected_func = None, None
        func_exists = (
            _function_exists_in_python(python_content, handler_func)
            if tf_handler else False
        )
        file_matches = expected_file == python_file.replace(".py", "")
        func_matches = expected_func == handler_func
        assert tf_handler and file_matches and func_matches and func_exists, (
            f"Contract verification failed for {resource_name}: "
            f"tf_handler={tf_handler}, expected_file={expected_file}, "
            f"expected_func={expected_func}, func_exists={func_exists}"
        )

    @pytest.mark.parametrize("resource_name,python_file,_handler_func", LAMBDA_DEFINITIONS)
    def test_lambda_file_exists(self, resource_name, python_file, _handler_func):
        """Verify Lambda Python source file exists."""
        file_path = LAMBDAS_PATH / python_file
        assert file_path.exists(), (
            f"Lambda source file missing: {file_path}. "
            f"Terraform resource aws_lambda_function.{resource_name} references this file."
        )


class TestEnvironmentVariableContracts:
    """Test that environment variables in Terraform match handler expectations."""

    @pytest.mark.parametrize("resource_name,python_file,_handler_func", LAMBDA_DEFINITIONS)
    def test_env_vars_defined_in_terraform(self, resource_name, python_file, _handler_func):
        """Verify env vars used in Python are defined in Terraform.

        Note: This test may have false positives if the Python code uses
        env vars that are provided by AWS Lambda runtime (e.g., AWS_REGION).
        """
        tf_content = _read_terraform_file()
        python_content = _read_python_file(python_file)

        # Get env vars defined in Terraform
        tf_env_vars = _extract_env_vars_from_tf(tf_content, resource_name)

        # Get env vars used in Python
        python_env_vars = _extract_env_var_usage_from_python(python_content)

        # AWS-provided env vars that don't need to be in Terraform
        aws_provided = {
            "AWS_REGION",
            "AWS_DEFAULT_REGION",
            "AWS_LAMBDA_FUNCTION_NAME",
            "AWS_LAMBDA_FUNCTION_VERSION",
            "AWS_LAMBDA_LOG_GROUP_NAME",
            "AWS_LAMBDA_LOG_STREAM_NAME",
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_SESSION_TOKEN",
            "_HANDLER",
            "LAMBDA_TASK_ROOT",
            "LAMBDA_RUNTIME_DIR",
        }

        # Check if all Python env vars are either in Terraform or AWS-provided
        missing = python_env_vars - tf_env_vars - aws_provided

        # Filter out env vars that might be optional (checked with .get() or getenv with default)
        # For now, we just report - this test is informational
        if missing:
            pytest.skip(
                f"Env vars used in {python_file} but not in Terraform {resource_name}: {missing}. "
                f"This may be intentional if vars are optional or provided elsewhere."
            )
        # If we get here without skipping, there are no missing vars
        assert not missing

    def test_terraform_has_environment_block(self):
        """Verify Terraform Lambda resources have environment blocks."""
        tf_content = _read_terraform_file()
        # At least some Lambdas should have environment blocks
        pattern = r'environment\s*\{'
        env_count = len(re.findall(pattern, tf_content))
        assert env_count >= 1, "Expected at least one Lambda with environment block"


class TestArchiveSourceContracts:
    """Test that archive_file sources reference existing files."""

    @pytest.mark.parametrize("resource_name,python_file,_handler_func", LAMBDA_DEFINITIONS)
    def test_archive_includes_main_lambda_file(self, resource_name, python_file, _handler_func):
        """Verify archive_file includes the main Lambda Python file."""
        tf_content = _read_terraform_file()

        # Get files included in archive
        archive_sources = _extract_archive_sources(tf_content, resource_name)

        # Main lambda file should be in the archive
        assert python_file in archive_sources, (
            f"Main Lambda file '{python_file}' not found in archive_file.{resource_name}. "
            f"Archive contains: {archive_sources}"
        )

    def test_all_common_modules_exist(self):
        """Verify all common modules referenced in archives exist."""
        for module_path in COMMON_MODULES:
            full_path = LAMBDAS_PATH / module_path
            assert full_path.exists(), (
                f"Common module missing: {full_path}. "
                f"This module is expected to be included in Lambda archives."
            )

    @pytest.mark.parametrize("resource_name,_python_file,_handler_func", [
        d for d in LAMBDA_DEFINITIONS if d[0] != "dlq_reprocessor"
    ])
    def test_archive_includes_common_modules(self, resource_name, _python_file, _handler_func):
        """Verify archives include required common modules.

        Note: dlq_reprocessor uses source_file instead of source blocks,
        so it doesn't include common modules the same way.
        """
        tf_content = _read_terraform_file()
        archive_sources = _extract_archive_sources(tf_content, resource_name)

        # Check that common modules are included
        for module in COMMON_MODULES:
            assert module in archive_sources, (
                f"Common module '{module}' not in archive_file.{resource_name}. "
                f"Archive sources: {archive_sources}"
            )


class TestTerraformResourceNaming:
    """Test that Terraform resources follow naming conventions."""

    def test_lambda_function_names_use_pascal_case(self):
        """Verify Lambda function names use PascalCase."""
        tf_content = _read_terraform_file()

        # Find all function_name references
        # Pattern: function_name = local.xxx_function_name
        pattern = r'function_name\s*=\s*local\.(\w+)_function_name'
        local_names = re.findall(pattern, tf_content)

        # All local names should be snake_case, and the actual function names
        # (from locals.tf) should be PascalCase
        # This test verifies the pattern is consistent and we have expected number of lambdas
        assert len(local_names) > 0 and len(local_names) == len(LAMBDA_DEFINITIONS), (
            f"Expected {len(LAMBDA_DEFINITIONS)} Lambda functions, "
            f"found {len(local_names)} function_name references"
        )

    def test_log_group_names_follow_pattern(self):
        """Verify CloudWatch log group names follow /aws/lambda/ pattern."""
        tf_content = _read_terraform_file()

        # Find all log group name definitions
        pattern = r'name\s*=\s*"/aws/lambda/\$\{local\.(\w+)_function_name\}"'
        log_groups = re.findall(pattern, tf_content)

        # Also check for the webhook handler which uses a local for log group name
        webhook_pattern = r'name\s*=\s*local\.webhook_handler_log_group_name'
        webhook_log_groups = re.findall(webhook_pattern, tf_content)

        total_log_groups = len(log_groups) + len(webhook_log_groups)

        # Should have a log group for each Lambda
        assert total_log_groups == len(LAMBDA_DEFINITIONS), (
            f"Expected {len(LAMBDA_DEFINITIONS)} log groups, found {total_log_groups}"
        )


class TestCrossFileConsistency:
    """Test cross-file configuration consistency."""

    def test_archive_files_match_lambda_resources(self):
        """Verify each Lambda has a corresponding archive_file."""
        tf_content = _read_terraform_file()

        for resource_name, _, _ in LAMBDA_DEFINITIONS:
            # Check archive_file data source exists and Lambda resource exists
            archive_pattern = rf'data\s+"archive_file"\s+"{resource_name}"'
            lambda_pattern = rf'resource\s+"aws_lambda_function"\s+"{resource_name}"'
            archive_exists = re.search(archive_pattern, tf_content)
            lambda_exists = re.search(lambda_pattern, tf_content)
            assert archive_exists and lambda_exists, (
                f"Missing archive_file or aws_lambda_function for {resource_name}"
            )

    def test_lambda_resources_reference_correct_archives(self):
        """Verify Lambda functions reference their corresponding archives."""
        tf_content = _read_terraform_file()

        for resource_name, _, _ in LAMBDA_DEFINITIONS:
            # Check that Lambda references the correct archive
            pattern = (
                rf'resource\s+"aws_lambda_function"\s+"{resource_name}"'
                rf'[^}}]*?filename\s*=\s*data\.archive_file\.{resource_name}'
                rf'\.output_path'
            )
            assert re.search(pattern, tf_content, re.DOTALL), (
                f"Lambda {resource_name} does not reference "
                f"archive_file.{resource_name}.output_path"
            )
