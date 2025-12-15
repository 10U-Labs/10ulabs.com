"""Post-deployment integration tests: AgentCore Runtime (Direct Code Deploy).

Verifies the AgentCore runtime is deployed with direct code deployment (no Docker).

Five-layer testing model:
- Layer 3: Existence - Does the runtime exist?
- Layer 4: Configuration - Is it using code deployment (not container)?
"""

import pytest
from botocore.exceptions import ClientError


class TestAgentCoreRuntimeExistence:
    """Layer 3: Verify the AgentCore runtime exists."""

    def test_01_runtime_exists(self, bedrock_agentcore_client, agentcore_runtime_name):
        """Verify the AgentCore runtime exists."""
        try:
            response = bedrock_agentcore_client.list_agent_runtimes(maxResults=100)
            runtimes = response.get("agentRuntimeSummaries", [])
            names = [r["agentRuntimeName"] for r in runtimes]
            assert agentcore_runtime_name in names, (
                f"AgentCore runtime '{agentcore_runtime_name}' not found. "
                f"Available runtimes: {names}. "
                "Run terraform apply to create it."
            )
        except ClientError as err:
            pytest.fail(f"Failed to list AgentCore runtimes: {err}")


class TestAgentCoreRuntimeConfiguration:
    """Layer 4: Verify the AgentCore runtime is configured correctly."""

    @pytest.fixture
    def runtime_arn(self, bedrock_agentcore_client, agentcore_runtime_name):
        """Get the runtime ARN by name."""
        response = bedrock_agentcore_client.list_agent_runtimes(maxResults=100)
        for r in response.get("agentRuntimeSummaries", []):
            if r["agentRuntimeName"] == agentcore_runtime_name:
                return r["agentRuntimeArn"]
        pytest.skip(f"Runtime '{agentcore_runtime_name}' not found")

    def test_01_runtime_uses_code_deployment(
        self, bedrock_agentcore_client, runtime_arn, agentcore_runtime_name
    ):
        """Verify the runtime uses code deployment (not container)."""
        try:
            response = bedrock_agentcore_client.get_agent_runtime(
                agentRuntimeArn=runtime_arn
            )
            artifact = response.get("agentRuntimeArtifact", {})
            # Should have code configuration, NOT container configuration
            has_code = "codeConfiguration" in artifact
            has_container = "containerConfiguration" in artifact
            assert has_code and not has_container, (
                f"Runtime '{agentcore_runtime_name}' should use code deployment, "
                f"not container. has_code={has_code}, has_container={has_container}"
            )
        except ClientError as err:
            pytest.fail(f"Failed to get runtime: {err}")

    def test_02_runtime_has_environment_variables(
        self, bedrock_agentcore_client, runtime_arn, agentcore_runtime_name
    ):
        """Verify the runtime has required environment variables."""
        try:
            response = bedrock_agentcore_client.get_agent_runtime(
                agentRuntimeArn=runtime_arn
            )
            env_vars = response.get("environmentVariables", {})
            required_vars = ["PROMPTS_BUCKET", "GUARDRAIL_ID", "MEMORY_ARN"]
            missing = [v for v in required_vars if v not in env_vars]
            assert not missing, (
                f"Runtime '{agentcore_runtime_name}' missing environment variables: {missing}"
            )
        except ClientError as err:
            pytest.fail(f"Failed to get runtime: {err}")

    def test_03_runtime_has_guardrail_configuration(
        self, bedrock_agentcore_client, runtime_arn, agentcore_runtime_name
    ):
        """Verify the runtime has guardrail configuration."""
        try:
            response = bedrock_agentcore_client.get_agent_runtime(
                agentRuntimeArn=runtime_arn
            )
            guardrail_config = response.get("guardrailConfiguration")
            assert guardrail_config is not None, (
                f"Runtime '{agentcore_runtime_name}' should have guardrail configuration."
            )
        except ClientError as err:
            pytest.fail(f"Failed to get runtime: {err}")

    def test_04_runtime_guardrail_has_id(
        self, bedrock_agentcore_client, runtime_arn, agentcore_runtime_name
    ):
        """Verify the runtime guardrail configuration has guardrailId."""
        try:
            response = bedrock_agentcore_client.get_agent_runtime(
                agentRuntimeArn=runtime_arn
            )
            guardrail_config = response.get("guardrailConfiguration", {})
            assert "guardrailId" in guardrail_config, (
                f"Runtime '{agentcore_runtime_name}' guardrail config missing guardrailId."
            )
        except ClientError as err:
            pytest.fail(f"Failed to get runtime: {err}")


class TestRuntimeCodeBucket:
    """Verify the runtime code S3 bucket is configured correctly."""

    def test_01_runtime_code_bucket_exists(
        self, s3_client, s3_runtime_code_bucket_name
    ):
        """Verify the runtime code S3 bucket exists."""
        try:
            s3_client.head_bucket(Bucket=s3_runtime_code_bucket_name)
        except ClientError as err:
            code = err.response["Error"]["Code"]
            if code in ("404", "NoSuchBucket"):
                pytest.fail(
                    f"S3 bucket '{s3_runtime_code_bucket_name}' does not exist. "
                    "Run terraform apply to create it."
                )
            raise

    def test_02_runtime_code_is_uploaded(
        self, s3_client, s3_runtime_code_bucket_name
    ):
        """Verify runtime code zip is uploaded to S3."""
        try:
            response = s3_client.list_objects_v2(
                Bucket=s3_runtime_code_bucket_name,
                Prefix="runtime/",
                MaxKeys=10
            )
            contents = response.get("Contents", [])
            zip_files = [obj["Key"] for obj in contents if obj["Key"].endswith(".zip")]
            assert len(zip_files) >= 1, (
                f"Expected at least 1 runtime zip in '{s3_runtime_code_bucket_name}/runtime/', "
                f"found {len(zip_files)}"
            )
        except ClientError as err:
            if err.response["Error"]["Code"] in ("404", "NoSuchBucket"):
                pytest.skip("Bucket not found - covered by existence test")
            raise
