from typing import Any

from test_fixtures.integration.helpers import s3_head_bucket_problem


def create_simple_layer1_authentication_tests() -> type:
    class TestAWSAuthentication:
        def test_aws_credentials_valid(self, sts_client: Any) -> None:
            response = sts_client.get_caller_identity()
            assert response["Account"] is not None

        def test_aws_credentials_not_expired(self, sts_client: Any) -> None:
            response = sts_client.get_caller_identity()
            assert "Arn" in response

    return TestAWSAuthentication


def create_layer2_s3_authorization_tests() -> type:
    class TestS3Authorization:
        def test_can_call_s3_head_bucket(self, s3_client: Any, state_bucket_name: str) -> None:
            problem = s3_head_bucket_problem(s3_client, state_bucket_name)
            assert not problem, problem

        def test_bucket_name_is_configured(self, state_bucket_name: str) -> None:
            assert state_bucket_name, "State bucket name is not configured"

    return TestS3Authorization
