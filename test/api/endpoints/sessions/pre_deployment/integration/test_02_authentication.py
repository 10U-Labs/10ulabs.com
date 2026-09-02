from typing import Any
class TestAwsAuthentication:
    def test_aws_credentials_valid(self, sts_client: Any) -> None:
        response = sts_client.get_caller_identity()
        assert response["Account"] is not None

    def test_aws_credentials_not_expired(self, sts_client: Any) -> None:
        response = sts_client.get_caller_identity()
        assert "Arn" in response
