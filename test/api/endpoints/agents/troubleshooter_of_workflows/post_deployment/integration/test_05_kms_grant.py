"""Integration tests for KMS grant validity.

These tests verify that the KMS grant used by Lambda to decrypt environment
variables references the correct IAM role ID.

When an IAM role is recreated (e.g., due to Terraform changes), AWS assigns
a new role ID. However, the KMS grant created by Lambda still references the
old role ID, causing KMSAccessDeniedException (502 errors).

This is a regression test for the stale KMS grant bug.
"""

import pytest


LAMBDA_ROLE_NAME = "TenULabsTroubleshooterOfWorkflowsWebhookRole"
LAMBDA_FUNCTION_NAME = "TenULabsTroubleshooterOfWorkflowsWebhook"


class TestKMSGrantValidity:
    """Verify KMS grant references the current IAM role ID."""

    @pytest.fixture
    def kms_client(self, aws_region):
        """Create a KMS client."""
        import boto3

        return boto3.client("kms", region_name=aws_region)

    @pytest.fixture
    def lambda_kms_key_id(self, lambda_client):
        """Get the KMS key ID used by Lambda for environment variable encryption.

        Lambda uses the AWS-managed key for Lambda by default when no
        customer-managed key is specified.
        """
        try:
            # Get the Lambda function configuration
            response = lambda_client.get_function_configuration(
                FunctionName=LAMBDA_FUNCTION_NAME
            )

            # If KMSKeyArn is set, use that; otherwise use the default Lambda key
            kms_key_arn = response.get("KMSKeyArn")
            if kms_key_arn:
                return kms_key_arn

            # Find the default Lambda KMS key
            import boto3

            kms = boto3.client("kms", region_name=response.get("FunctionArn", "").split(":")[3])
            aliases = kms.list_aliases()
            for alias in aliases.get("Aliases", []):
                if alias.get("AliasName") == "alias/aws/lambda":
                    return alias.get("TargetKeyId")

            return None
        except Exception:
            return None

    def test_01_kms_grant_exists_for_lambda(self, kms_client, lambda_kms_key_id):
        """Verify a KMS grant exists for the Lambda function.

        Lambda creates a KMS grant when it needs to decrypt environment variables.
        This grant must exist for the Lambda to function correctly.
        """
        if not lambda_kms_key_id:
            pytest.skip("Could not determine Lambda KMS key ID")

        try:
            response = kms_client.list_grants(KeyId=lambda_kms_key_id)
            grants = response.get("Grants", [])

            # Find grants for our Lambda function
            lambda_grants = [
                g for g in grants if LAMBDA_FUNCTION_NAME in g.get("Name", "")
            ]

            assert len(lambda_grants) > 0, (
                f"No KMS grant found for Lambda function '{LAMBDA_FUNCTION_NAME}'. "
                "Lambda needs a KMS grant to decrypt environment variables. "
                "This usually means the Lambda was not created correctly or "
                "the grant was revoked."
            )
        except kms_client.exceptions.NotFoundException:
            pytest.skip(f"KMS key {lambda_kms_key_id} not found")

    def test_02_kms_grant_references_current_role(
        self, iam_client, kms_client, lambda_kms_key_id
    ):
        """Verify the KMS grant references the current IAM role.

        KMS grants can reference roles in two formats:
        1. Role ID format: AROAXXXXXXXXXX:FunctionName (older grants)
        2. ARN format: arn:aws:sts::...:assumed-role/RoleName/FunctionName (newer grants)

        When a role is recreated, old role-ID-based grants become stale because
        they reference the old role ID. ARN-based grants use the role name and
        are more resilient.

        This test catches stale grants before they cause 502 errors.
        """
        if not lambda_kms_key_id:
            pytest.skip("Could not determine Lambda KMS key ID")

        # Get the current role details
        try:
            role_response = iam_client.get_role(RoleName=LAMBDA_ROLE_NAME)
            current_role_id = role_response["Role"]["RoleId"]
        except iam_client.exceptions.NoSuchEntityException:
            pytest.fail(f"IAM role '{LAMBDA_ROLE_NAME}' not found")

        # Get KMS grants for our Lambda
        try:
            grants_response = kms_client.list_grants(KeyId=lambda_kms_key_id)
            grants = grants_response.get("Grants", [])

            lambda_grants = [
                g for g in grants if LAMBDA_FUNCTION_NAME in g.get("Name", "")
            ]

            if not lambda_grants:
                pytest.skip("No KMS grant found for Lambda function")

            # Check that at least one grant references the current role
            for grant in lambda_grants:
                principal = grant.get("GranteePrincipal", "")

                # ARN format: arn:aws:sts::...:assumed-role/RoleName/FunctionName
                # This format uses role name and is valid as long as role exists
                if "assumed-role" in principal:
                    parts = principal.split("/")
                    if len(parts) >= 2 and parts[1] == LAMBDA_ROLE_NAME:
                        return  # Valid grant using role name

                # Role ID format: AROAXXXXXXXXXX:FunctionName
                # This format uses role ID and must match current role ID
                if current_role_id in principal:
                    return  # Valid grant using current role ID

            # No valid grant found - extract details for error message
            grant_details = []
            for grant in lambda_grants:
                principal = grant.get("GranteePrincipal", "")
                if "assumed-role" in principal:
                    parts = principal.split("/")
                    if len(parts) >= 2:
                        grant_details.append(f"role name: {parts[1]}")
                elif principal.startswith("AROA"):
                    role_id_part = principal.split(":")[0]
                    grant_details.append(f"role ID: {role_id_part}")
                else:
                    grant_details.append(principal)

            pytest.fail(
                f"KMS grant references stale role!\n\n"
                f"Expected role name: {LAMBDA_ROLE_NAME}\n"
                f"Expected role ID: {current_role_id}\n"
                f"Grant references: {', '.join(grant_details)}\n\n"
                "The IAM role was likely recreated, giving it a new role ID, "
                "but the KMS grant still references the old role.\n\n"
                "Fix: Recreate the Lambda function to trigger a new KMS grant:\n"
                "  terraform taint aws_lambda_function.webhook\n"
                "  terraform apply\n\n"
                "Prevention: Add lifecycle { replace_triggered_by = [aws_iam_role.<name>.id] } "
                "to the Lambda resource."
            )

        except kms_client.exceptions.NotFoundException:
            pytest.skip(f"KMS key {lambda_kms_key_id} not found")
