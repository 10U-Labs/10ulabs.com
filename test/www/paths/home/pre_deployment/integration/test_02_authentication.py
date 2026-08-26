from test_fixtures.integration import Layer2EndpointAuthenticationTests


class TestAWSAuthentication(Layer2EndpointAuthenticationTests):
    pass


class TestAWSCredentialsValid:
    def test_aws_credentials_not_expired(self, sts_client):
        response = sts_client.get_caller_identity()
        has_arn = "Arn" in response
        assert has_arn, "AWS credentials may be expired"

    def test_aws_region_configured(self, aws_region):
        region_is_configured = aws_region is not None and len(aws_region) > 0
        assert region_is_configured, "AWS region not configured"
