import re
from pathlib import Path
from typing import Any, Callable, Optional, Set

from repo_utils import REPO_ROOT

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
) -> type:
    lambda_path = endpoint_src / lambda_file
    outputs_file = API_COMMON_ROUTING_OUTPUTS_FILE.relative_to(REPO_ROOT)

    def get_api_remote_state_references() -> set:
        with open(lambda_path, encoding="utf-8") as f:
            content = f.read()
        pattern = r'data\.terraform_remote_state\.api\.outputs\.(\w+)'
        return set(re.findall(pattern, content))

    class TestRemoteStateContract:
        def test_all_api_remote_state_references_exist_in_api_common_routing_outputs(self) -> None:
            references = get_api_remote_state_references()
            outputs = _get_api_common_routing_outputs()
            missing = references - outputs

            assert not missing, (
                f"{endpoint_name}/{lambda_file} references api_common_routing outputs "
                f"that don't exist: {missing}. Add these outputs to {outputs_file}"
            )

        def test_lambda_file_exists(self) -> None:
            assert lambda_path.exists(), f"{lambda_file} does not exist in endpoint"

    if required_outputs:
        for output_name in required_outputs:

            def make_test(name: str) -> Callable[[Any], None]:
                def test_output_exists(_self: Any) -> None:
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


def create_remote_state_config_tests(endpoint_src: Path, endpoint_name: str) -> type:
    data_tf_path = endpoint_src / "data.tf"

    class TestRemoteStateConfig:
        def test_data_tf_exists(self) -> None:
            assert data_tf_path.exists(), f"data.tf not found in {endpoint_name}"

        def test_no_hardcoded_bucket_name(self) -> None:
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

        def test_no_hardcoded_region(self) -> None:
            content = data_tf_path.read_text()
            hardcoded_region = re.search(
                r'region\s*=\s*"[a-z]+-[a-z]+-\d+"', content
            )
            assert hardcoded_region is None, (
                f"{endpoint_name}/data.tf uses hardcoded region. "
                "Use local.aws_region or module.common.aws_region instead."
            )

        def test_uses_correct_state_key_pattern(self) -> None:
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


def _braced_block(content: str, opening: int) -> str:
    depth = 0
    for position in range(opening, len(content)):
        if content[position] == "{":
            depth += 1
        elif content[position] == "}":
            depth -= 1
            if depth == 0:
                return content[opening + 1:position]
    return content[opening + 1:]


def _block_named(content: str, kind: str, block_type: str, name: str) -> str:
    header = re.search(
        rf'{kind}\s+"{re.escape(block_type)}"\s+"{re.escape(name)}"\s*\{{',
        content,
    )
    return _braced_block(content, header.end() - 1) if header else ""


def _environment_variables_supplied(resource_block: str) -> Set[str]:
    header = re.search(r"variables\s*=\s*\{", resource_block)
    if not header:
        return set()
    variables = _braced_block(resource_block, header.end() - 1)
    return set(re.findall(r"^\s*(\w+)\s*=", variables, re.MULTILINE))


def _environment_variables_read(handler_source: str) -> Set[str]:
    pattern = r"os\.environ(?:\.get)?[\[(]\s*['\"](\w+)['\"]"
    return set(re.findall(pattern, handler_source))


def _packaged_handler_source_path(tf_content: str, resource_block: str) -> Optional[str]:
    archive = re.search(r"data\.archive_file\.(\w+)\.", resource_block)
    if not archive:
        return None
    archive_block = _block_named(tf_content, "data", "archive_file", archive.group(1))
    named = re.search(r'source_file\s*=\s*"([^"]+)"', archive_block)
    if not named:
        named = re.search(r'file\(\s*"([^"]+)"\s*\)', archive_block)
    if not named:
        return None
    return named.group(1).replace("${path.module}/", "")


def create_lambda_source_contract_tests(
    endpoint_src: Path,
    tf_file: str,
    resource_name: str,
) -> type:
    tf_path = endpoint_src / tf_file
    resource = f"aws_lambda_function.{resource_name}"

    def resource_block() -> str:
        content = tf_path.read_text() if tf_path.exists() else ""
        return _block_named(content, "resource", "aws_lambda_function", resource_name)

    def packaged_source() -> Optional[str]:
        content = tf_path.read_text() if tf_path.exists() else ""
        return _packaged_handler_source_path(content, resource_block())

    def packaged_source_name() -> str:
        relative = packaged_source()
        if relative is None:
            return f"the handler source no archive_file in {tf_file} names for {resource}"
        return f"{tf_file.rsplit('.', 1)[0]}'s packaged source {relative}"

    def packaged_source_text() -> str:
        relative = packaged_source()
        if relative is None:
            return ""
        handler_path = endpoint_src / relative
        return handler_path.read_text() if handler_path.exists() else ""

    class TestLambdaSourceContract:
        def test_handler_attribute_names_a_function_the_source_defines(self) -> None:
            attribute = re.search(r'handler\s*=\s*"([^"]+)"', resource_block())
            function_name = attribute.group(1).rsplit(".", 1)[-1] if attribute else ""
            assert f"def {function_name}(" in packaged_source_text(), (
                f"{tf_file} configures {resource} to be entered at "
                f"'{attribute.group(1) if attribute else ''}', and "
                f"{packaged_source_name()} defines no function '{function_name}'"
            )

        def test_environment_variables_supplied_are_the_ones_read(self) -> None:
            supplied = _environment_variables_supplied(resource_block())
            read = _environment_variables_read(packaged_source_text())
            assert supplied == read, (
                f"{packaged_source_name()} reads environment variables {tf_file} "
                f"does not supply to {resource}: {sorted(read - supplied)}; "
                f"{tf_file} supplies environment variables to {resource} that "
                f"{packaged_source_name()} never reads: {sorted(supplied - read)}"
            )

    return TestLambdaSourceContract
