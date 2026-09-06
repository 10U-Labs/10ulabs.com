from typing import Any


def test_aws_credentials_valid(sts_client: Any) -> None:
    response = sts_client.get_caller_identity()
    assert response["Account"] is not None


def test_aws_credentials_not_expired(sts_client: Any) -> None:
    response = sts_client.get_caller_identity()
    assert "Arn" in response
