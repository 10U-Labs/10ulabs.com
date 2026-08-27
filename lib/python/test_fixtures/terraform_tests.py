import re
from pathlib import Path
from typing import Optional

import pytest
from naming_conventions import validate_name
from repo_utils import REPO_ROOT
from terraform_config import extract_iam_role_names, extract_lambda_function_names

API_COMMON_ROUTING_OUTPUTS_FILE = REPO_ROOT / "src" / "api" / "common" / "routing" / "outputs.tf"


def _get_api_common_routing_outputs() -> set:
    with open(API_COMMON_ROUTING_OUTPUTS_FILE, encoding="utf-8") as f:
        content = f.read()
    pattern = r'output\s+"(\w+)"'
    return set(re.findall(pattern, content))


def create_remote_state_contract_tests(
    endpoint_src: Path,
    endpoint_name: str,
    lambda_file: str = "lambda.tf",
    required_outputs: Optional[list] = None,
):
    lambda_path = endpoint_src / lambda_file
    outputs_file = API_COMMON_ROUTING_OUTPUTS_FILE.relative_to(REPO_ROOT)

    def get_api_remote_state_references():
        with open(lambda_path, encoding="utf-8") as f:
            content = f.read()
        pattern = r'data\.terraform_remote_state\.api\.outputs\.(\w+)'
        return set(re.findall(pattern, content))

    class TestRemoteStateContract:
        def test_all_api_remote_state_references_exist_in_api_common_routing_outputs(self):
            references = get_api_remote_state_references()
            outputs = _get_api_common_routing_outputs()
            missing = references - outputs

            assert not missing, (
                f"{endpoint_name}/{lambda_file} references api_common_routing outputs "
                f"that don't exist: {missing}. Add these outputs to {outputs_file}"
            )

        def test_lambda_file_exists(self):
            assert lambda_path.exists(), f"{lambda_file} does not exist in endpoint"

    if required_outputs:
        for output_name in required_outputs:

            def make_test(name):
                def test_output_exists(_self):
                    outputs = _get_api_common_routing_outputs()
                    assert name in outputs, (
                        f"{name} output missing from {outputs_file}. "
                        f"This is required by the {endpoint_name} endpoint."
                    )

                return test_output_exists

            test_method = make_test(output_name)
            test_method.__name__ = f"test_{output_name}_output_exists_in_api_common_routing"
            test_method.__doc__ = f"Verify {output_name} output exists in api_common_routing."
            setattr(TestRemoteStateContract, test_method.__name__, test_method)

    return TestRemoteStateContract


def create_naming_conventions_tests(
    endpoint_src: Path,
    iam_file: str = "iam.tf",
    lambda_file: str = "lambda.tf",
    use_handler_names: bool = False,
):
    iam_path = endpoint_src / iam_file
    lambda_path = endpoint_src / lambda_file

    iam_roles = extract_iam_role_names(iam_path)
    lambda_functions = extract_lambda_function_names(
        lambda_path, use_handler_names=use_handler_names
    )

    class TestIAMRoleNamingConventions:
        @pytest.mark.parametrize(
            "resource_name,role_name",
            iam_roles if iam_roles else [("NONE", "NONE")],
            ids=[f"iam_role_{r[0]}" for r in iam_roles] if iam_roles else ["no_roles_found"],
        )
        def test_iam_role_name_is_pascalcase(self, resource_name, role_name):
            if resource_name == "NONE":
                pytest.fail("No IAM roles found in iam.tf - check Terraform files")
            error = validate_name(role_name)
            assert error is None, (
                f"IAM role '{resource_name}' has invalid name '{role_name}': {error}"
            )

        def test_no_iam_role_names_contain_dashes(self):
            violations = [(r, n) for r, n in iam_roles if '-' in n]
            assert len(violations) == 0, (
                f"Found {len(violations)} IAM roles with dashes:\n"
                + "\n".join(f"  - {r}: '{n}'" for r, n in violations)
            )

    class TestLambdaFunctionNamingConventions:
        @pytest.mark.parametrize(
            "resource_name,function_name",
            lambda_functions if lambda_functions else [("NONE", "NONE")],
            ids=([f"lambda_{f[0]}" for f in lambda_functions]
                 if lambda_functions else ["no_functions_found"]),
        )
        def test_lambda_function_name_is_pascalcase(self, resource_name, function_name):
            if resource_name == "NONE":
                pytest.fail("No Lambda functions found - check Terraform files")
            error = validate_name(function_name)
            assert error is None, (
                f"Lambda function '{resource_name}' has invalid name "
                f"'{function_name}': {error}"
            )

        def test_no_lambda_function_names_contain_dashes(self):
            violations = [(r, n) for r, n in lambda_functions if '-' in n]
            assert len(violations) == 0, (
                f"Found {len(violations)} Lambda functions with dashes:\n"
                + "\n".join(f"  - {r}: '{n}'" for r, n in violations)
            )

    return TestIAMRoleNamingConventions, TestLambdaFunctionNamingConventions


def create_remote_state_config_tests(endpoint_src: Path, endpoint_name: str):
    data_tf_path = endpoint_src / "data.tf"

    class TestRemoteStateConfig:
        def test_data_tf_exists(self):
            assert data_tf_path.exists(), f"data.tf not found in {endpoint_name}"

        def test_no_hardcoded_bucket_name(self):
            content = data_tf_path.read_text()
            hardcoded_patterns = [
                r'bucket\s*=\s*"[a-z0-9]+-terraform-state',
                r'bucket\s*=\s*"tenulabs-',
                r'bucket\s*=\s*"10ulabs-',
            ]
            for pattern in hardcoded_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                assert match is None, (
                    f"{endpoint_name}/data.tf uses hardcoded bucket name. "
                    "Use module.common.name_for_terraform_state_bucket instead."
                )

        def test_no_hardcoded_region(self):
            content = data_tf_path.read_text()
            hardcoded_region = re.search(
                r'region\s*=\s*"[a-z]+-[a-z]+-\d+"', content
            )
            assert hardcoded_region is None, (
                f"{endpoint_name}/data.tf uses hardcoded region. "
                "Use local.aws_region or module.common.aws_region instead."
            )

        def test_uses_correct_state_key_pattern(self):
            content = data_tf_path.read_text()
            if 'terraform_remote_state' in content and '"api"' in content:
                correct_key = re.search(
                    r'key\s*=\s*"api/terraform\.tfstate"', content
                )
                wrong_key = re.search(
                    r'key\s*=\s*"api_common_routing/terraform\.tfstate"', content
                )
                assert wrong_key is None, (
                    f"{endpoint_name}/data.tf uses wrong state key path. "
                    'Use "api/terraform.tfstate" not "api_common_routing/..."'
                )
                assert correct_key is not None, (
                    f"{endpoint_name}/data.tf should use key = "
                    '"api/terraform.tfstate" for API remote state.'
                )

    return TestRemoteStateConfig
