import re
from typing import Optional, Set

from repo_utils import REPO_ROOT


RACK_CONFIGURATIONS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "rack_configurations"
HANDLER_PATH = RACK_CONFIGURATIONS_SRC / "lambda" / "handler.py"
LAMBDA_TF_PATH = RACK_CONFIGURATIONS_SRC / "lambda.tf"


def _get_handler_reference_from_lambda_tf() -> Optional[re.Match[str]]:
    with open(LAMBDA_TF_PATH, encoding="utf-8") as f:
        tf_content = f.read()
    return re.search(r'handler\s*=\s*"([^"]+)"', tf_content)


class TestLambdaHandlerContracts:
    def test_lambda_tf_has_handler_attribute(self) -> None:
        handler_match = _get_handler_reference_from_lambda_tf()
        assert handler_match, "handler attribute not found in lambda.tf"

    def test_handler_py_exports_referenced_function(self) -> None:
        with open(HANDLER_PATH, encoding="utf-8") as f:
            handler_content = f.read()

        handler_match = _get_handler_reference_from_lambda_tf()
        tf_handler_ref = handler_match.group(1)
        expected_function = tf_handler_ref.split(".")[-1]

        assert f"def {expected_function}(" in handler_content, (
            f"handler.py does not export function '{expected_function}' "
            f"referenced in lambda.tf"
        )

    def test_environment_variable_names_match(self) -> None:
        with open(HANDLER_PATH, encoding="utf-8") as f:
            handler_content = f.read()
        with open(LAMBDA_TF_PATH, encoding="utf-8") as f:
            tf_content = f.read()

        handler_env_vars = set(re.findall(
            r"os\.environ\[['\"](\w+)['\"]\]", handler_content
        ))

        env_block = re.search(
            r"environment\s*\{[^}]*variables\s*=\s*\{([^}]+)\}", tf_content, re.DOTALL
        )
        tf_env_vars: Set[str] = set()
        if env_block:
            tf_env_vars = set(re.findall(r"(\w+)\s*=", env_block.group(1)))

        missing_vars = handler_env_vars - tf_env_vars
        assert not missing_vars, (
            f"handler.py uses environment variables not defined in lambda.tf: "
            f"{missing_vars}"
        )


def _get_shared_tf_content() -> str:
    shared_tf_path = RACK_CONFIGURATIONS_SRC / "shared.tf"
    with open(shared_tf_path, encoding="utf-8") as f:
        return f.read()


class TestTerraformModuleContracts:
    def test_shared_tf_has_module_reference(self) -> None:
        content = _get_shared_tf_content()
        module_match = re.search(r'module\s+"(\w+)"\s*\{', content)
        assert module_match, "shared.tf should reference a module"

    def test_shared_tf_module_has_source(self) -> None:
        content = _get_shared_tf_content()
        source_match = re.search(r'source\s*=\s*"([^"]+)"', content)
        assert source_match, "module in shared.tf should have a source"

    def test_shared_tf_module_source_path_exists(self) -> None:
        content = _get_shared_tf_content()
        source_match = re.search(r'source\s*=\s*"([^"]+)"', content)
        source_path = source_match.group(1) if source_match else "(no module source declared)"
        resolved_path = (RACK_CONFIGURATIONS_SRC / source_path).resolve()
        assert resolved_path.exists(), (
            f"Module source path does not exist: {source_path}"
        )

    def test_locals_tf_uses_module_common_outputs(self) -> None:
        locals_tf_path = RACK_CONFIGURATIONS_SRC / "locals.tf"
        with open(locals_tf_path, encoding="utf-8") as f:
            content = f.read()

        assert "module.common" in content, (
            "locals.tf should reference module.common for shared configuration"
        )
