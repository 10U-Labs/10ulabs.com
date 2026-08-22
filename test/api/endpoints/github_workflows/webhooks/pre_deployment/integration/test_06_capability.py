"""Layer 6: Capability - Can we perform required operations?

These tests verify that we have the capability to perform operations required
for deployment on prerequisite resources.

Six-layer testing model:
- Layer 1: Authentication - Are credentials configured and valid?
- Layer 2: Authorization - Do we have permission to call required APIs?
- Layer 3: State - Does Terraform state match AWS reality?
- Layer 4: Existence - Do the required resources exist?
- Layer 5: Configuration - Are resources configured correctly?
- Layer 6: Capability - Can we perform required operations? (THIS FILE)

Note: The api_endpoint_v1_github_workflows_webhooks deployment relies on the API
Gateway that api_common_routing creates. Capability tests here verify we can
perform operations on those prerequisites.
"""


# === SSM Capability ===


def test_can_decrypt_github_pat_parameter(ssm_client, ssm_github_pat_name):
    """Verify we can decrypt the GitHub PAT SSM parameter.

    This tests KMS key access permissions for the GitHub Actions role.
    Skips if parameter doesn't exist (covered by Layer 4 existence tests).
    """
    response = ssm_client.get_parameter(Name=ssm_github_pat_name, WithDecryption=True)
    assert response.get("Parameter") is not None, (
        f"SSM parameter '{ssm_github_pat_name}' returned empty response"
    )
