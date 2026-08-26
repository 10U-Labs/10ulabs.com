import pytest
from botocore.exceptions import ClientError
from test_fixtures.integration import (
    Layer3APIGatewayAuthorizationTests,
    Layer3LambdaAndIAMAuthorizationTests,
)


class TestAPIGatewayAuthorization(Layer3APIGatewayAuthorizationTests):
    pass
class TestLambdaAndIAMAuthorization(Layer3LambdaAndIAMAuthorizationTests):
    pass
class TestDynamoDBAndS3Authorization:
    def test_can_list_tables(self, dynamodb_client):
        try:
            dynamodb_client.list_tables(Limit=1)
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDeniedException":
                pytest.fail("No permission to list DynamoDB tables")
            raise
        assert True

    def test_can_list_buckets(self, s3_client):
        try:
            s3_client.list_buckets()
        except ClientError as e:
            if e.response["Error"]["Code"] == "AccessDenied":
                pytest.fail("No permission to list S3 buckets")
            raise
        assert True
