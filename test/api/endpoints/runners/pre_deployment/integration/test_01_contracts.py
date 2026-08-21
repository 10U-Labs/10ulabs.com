"""Layer 1: Contract tests for runners endpoint pre-deployment validation.

Verify cross-file compatibility:
- Lambda handler exports match Terraform references
- Remote state outputs referenced exist in api_common_routing
- The workflow's push paths cover this stack and no sibling stack
- Every stack this one reads state from is deployed by a workflow
"""
import re
from pathlib import Path

import pytest
import yaml

from repo_utils import REPO_ROOT, extract_brace_block
from test_fixtures.terraform_tests import create_remote_state_contract_tests


RUNNERS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "runners"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
WORKFLOW = WORKFLOWS_DIR / "api_endpoint_v1_runners.yml"
SIBLING_STACKS = ("cleanups", "ec2", "ecs")
STATE_KEY = re.compile(r'key\s*=\s*"([^"]+)"')


def _push_paths() -> list:
    """List the path filters that decide whether a push starts this workflow."""
    document = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
    return (document.get(True) or {}).get("push", {}).get("paths", [])


def _glob_matches(glob: str, path: str) -> bool:
    """Say whether a GitHub path filter matches a repository path.

    A single star stops at a directory separator and a double star crosses
    them, which is what separates this stack's own files from a sibling's.
    """
    pattern = re.escape(glob).replace(r"\*\*", "\x00").replace(r"\*", "[^/]*")
    return re.fullmatch(pattern.replace("\x00", ".*"), path) is not None


def _state_keys_read() -> list:
    """List the state files this stack reads, ignoring its own subdirectories."""
    keys = []
    for source in sorted(RUNNERS_SRC.glob("*.tf")):
        text = source.read_text(encoding="utf-8")
        for found in re.finditer(r'data\s+"terraform_remote_state"', text):
            block = extract_brace_block(text, text.index("{", found.end()))
            keys.extend(STATE_KEY.findall(block))
    return keys


def _stack_for(state_key: str) -> str:
    """Name the source directory whose backend writes a state file, if any."""
    for backend in sorted((REPO_ROOT / "src").rglob("backend.tf")):
        if f'key          = "{state_key}"' in backend.read_text(encoding="utf-8"):
            return str(backend.parent.relative_to(REPO_ROOT))
    return ""


class TestLambdaHandlerContracts:
    """Verify Lambda handler exports match Terraform references."""

    def test_handler_exports_lambda_handler(self, handler_content: str):
        """Verify handler.py exports lambda_handler function."""
        assert "def lambda_handler(" in handler_content, (
            "handler.py must export lambda_handler function. "
            "This is required by the Lambda configuration in lambda.tf"
        )

    def test_lambda_tf_references_correct_handler(self, lambda_tf_content: str):
        """Verify lambda.tf references handler.lambda_handler."""
        assert 'handler          = "handler.lambda_handler"' in lambda_tf_content, (
            "lambda.tf must set handler to 'handler.lambda_handler'. "
            "This must match the function exported by handler.py"
        )


class TestLambdaPackageContracts:
    """Verify Lambda package includes all required modules."""

    def test_handler_imports_runner_labels(self, handler_content: str):
        """Verify handler imports runner_labels module."""
        assert "import runner_labels" in handler_content, (
            "handler.py must import runner_labels module. "
            "This is bundled as runner_labels.py in the Lambda package."
        )

    def test_lambda_package_includes_runner_labels(self, lambda_tf_content: str):
        """Verify Lambda package includes runner_labels.py."""
        assert 'runner_labels.py' in lambda_tf_content, (
            "lambda.tf must include runner_labels.py in the archive_file. "
            "The handler imports this module."
        )

    def test_lambda_package_includes_runners_json(self, lambda_tf_content: str):
        """Verify Lambda package includes etc/runners.json."""
        assert 'etc/runners.json' in lambda_tf_content, (
            "lambda.tf must include etc/runners.json in the archive_file. "
            "This is required by the runner_labels module."
        )


# Test that remote state outputs referenced in lambda.tf exist in api backend
TestRemoteStateContract = create_remote_state_contract_tests(
    endpoint_src=RUNNERS_SRC,
    endpoint_name="runners",
    lambda_file="lambda.tf",
    required_outputs=["api_gateway_id", "api_key_ssm_parameter"],
)


class TestWorkflowTriggerContracts:
    """Verify the workflow starts on this stack's own files and no others."""

    def test_push_paths_cover_this_stack_and_no_sibling(self):
        """Verify the path filters reach this stack's Terraform and nothing else."""
        paths = _push_paths()
        own = "src/api/endpoints/runners/backend.tf"
        reached = [
            f"{sibling}: matched by {glob}"
            for sibling in SIBLING_STACKS
            for glob in paths
            if _glob_matches(glob, f"src/api/endpoints/runners/{sibling}/main.tf")
        ]
        assert any(_glob_matches(glob, own) for glob in paths) and not reached, (
            f"paths must match {own} and no sibling stack, but they are "
            f"{paths} and they reach {reached or 'no sibling'}"
        )


class TestRemoteStateOwnershipContracts:
    """Verify every stack this one reads from is deployed by something."""

    def test_each_state_file_read_belongs_to_a_deployed_stack(self):
        """Verify a workflow deploys the stack behind each remote state read."""
        deployed = "\n".join(
            workflow.read_text(encoding="utf-8")
            for workflow in sorted(WORKFLOWS_DIR.glob("*.yml"))
        )
        orphans = [
            f"{key}: written by {_stack_for(key) or 'no backend.tf under src/'}"
            for key in _state_keys_read()
            if not _stack_for(key) or _stack_for(key) not in deployed
        ]
        assert not orphans, (
            "Remote state read from a stack no workflow deploys:\n  "
            + "\n  ".join(orphans)
        )


class TestIAMRemoteStateContracts:
    """Verify IAM references to remote state outputs."""

    def test_iam_tf_exists(self, runners_dir: Path):
        """Verify iam.tf file exists."""
        iam_path = runners_dir / "iam.tf"
        assert iam_path.exists(), f"iam.tf not found at {iam_path}"

    def test_iam_references_api_key_ssm_parameter_arn(self, runners_dir: Path):
        """Verify iam.tf references api_key_ssm_parameter_arn from api backend."""
        iam_path = runners_dir / "iam.tf"
        content = iam_path.read_text()
        assert "api_key_ssm_parameter_arn" in content, (
            "iam.tf must reference data.terraform_remote_state.api.outputs."
            "api_key_ssm_parameter_arn for SSM access policy"
        )
