"""Pre-deployment integration tests for AMI promotion functionality.

These tests verify that AWS permissions allow tagging AMIs and updating
SSM parameters, using a generic AWS-provided base AMI (e.g., Debian).
"""
from botocore.exceptions import ClientError


def _find_tag_value(tags, key):
    """Find a tag value by key from a list of AWS tags."""
    for tag in tags:
        if tag["Key"] == key:
            return tag["Value"]
    return None


def test_can_create_tag_on_ami(ec2_client, source_ami_id):
    """Test that AMI can be tagged for promotion."""
    test_tag_key = "TestPromotionTag"
    test_tag_value = "integration-test-value"

    try:
        ec2_client.create_tags(
            Resources=[source_ami_id],
            Tags=[{"Key": test_tag_key, "Value": test_tag_value}]
        )

        response = ec2_client.describe_images(ImageIds=[source_ami_id])
        tags = response["Images"][0].get("Tags", [])
        actual_value = _find_tag_value(tags, test_tag_key)

        assert actual_value == test_tag_value
    finally:
        try:
            ec2_client.delete_tags(
                Resources=[source_ami_id],
                Tags=[{"Key": test_tag_key}]
            )
        except ClientError:
            pass


def test_can_update_ssm_parameter_with_ami_id(ssm_client, source_ami_id):
    """Test that SSM parameter can be updated with AMI ID."""
    test_parameter_name = "/ami/ec2-runner/integration-test"

    try:
        ssm_client.delete_parameter(Name=test_parameter_name)
    except ssm_client.exceptions.ParameterNotFound:
        pass

    try:
        ssm_client.put_parameter(
            Name=test_parameter_name,
            Value=source_ami_id,
            Type="String",
            Overwrite=True,
            Description="Integration test parameter"
        )

        response = ssm_client.get_parameter(Name=test_parameter_name)
        parameter_value = response["Parameter"]["Value"]

        assert parameter_value == source_ami_id
    finally:
        try:
            ssm_client.delete_parameter(Name=test_parameter_name)
        except ClientError:
            pass
