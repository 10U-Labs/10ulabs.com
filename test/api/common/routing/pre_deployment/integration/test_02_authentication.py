from test_fixtures.integration import Layer2EndpointAuthenticationTests


class TestAuthentication(Layer2EndpointAuthenticationTests):
    pass


def test_caller_identity_is_role(caller_identity):
    arn = caller_identity.get("Arn", "")
    assert ":assumed-role/" in arn or ":role/" in arn, (
        f"Expected to be running as IAM role, but running as: {arn}. "
        "GitHub Actions should assume the GitHub Actions OIDC role."
    )
