from botocore.exceptions import ClientError


class TestNoOrphanedLambdaFunctions:
    def test_handler_lambda_not_orphaned(self, lambda_client, sessions_config):
        checked = False
        try:
            lambda_client.get_function(
                FunctionName=sessions_config["lambda_handler_name"]
            )
            checked = True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                checked = True
            else:
                raise
        assert checked

    def test_export_lambda_not_orphaned(self, lambda_client, sessions_config):
        checked = False
        try:
            lambda_client.get_function(
                FunctionName=sessions_config["export_function_name"]
            )
            checked = True
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                checked = True
            else:
                raise
        assert checked


def test_no_orphaned_dynamo_db_tables(dynamodb_client, sessions_config):
    checked = False
    try:
        dynamodb_client.describe_table(
            TableName=sessions_config["dynamodb_table_name"]
        )
        checked = True
    except ClientError as e:
        if e.response["Error"]["Code"] == "ResourceNotFoundException":
            checked = True
        else:
            raise
    assert checked


class TestNoOrphanedIamRoles:
    def test_handler_role_not_orphaned(self, iam_client, sessions_config):
        checked = False
        try:
            iam_client.get_role(RoleName=sessions_config["handler_role_name"])
            checked = True
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                checked = True
            else:
                raise
        assert checked

    def test_export_role_not_orphaned(self, iam_client, sessions_config):
        checked = False
        try:
            iam_client.get_role(RoleName=sessions_config["export_role_name"])
            checked = True
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchEntity":
                checked = True
            else:
                raise
        assert checked
