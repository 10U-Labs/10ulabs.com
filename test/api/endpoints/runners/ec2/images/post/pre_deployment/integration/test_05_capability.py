"""Layer 5: Capability tests.

These tests verify that you can perform required operations.
Assumes configuration (Layer 4) has passed.

These tests create temporary test artifacts and clean them up in finally blocks.
"""
from botocore.exceptions import ClientError


def _find_tag_value(tags, key):
    """Find a tag value by key from a list of AWS tags."""
    for tag in tags:
        if tag["Key"] == key:
            return tag["Value"]
    return None


def test_can_create_tag_on_ami(ec2_client, source_ami_id):
    """Verify we can tag an AMI for promotion."""
    test_tag_key = "TestPromotionTag"
    test_tag_value = "integration-test-value"

    try:
        ec2_client.create_tags(
            Resources=[source_ami_id],
            Tags=[{"Key": test_tag_key, "Value": test_tag_value}],
        )

        response = ec2_client.describe_images(ImageIds=[source_ami_id])
        tags = response["Images"][0].get("Tags", [])
        actual_value = _find_tag_value(tags, test_tag_key)

        assert actual_value == test_tag_value
    finally:
        ec2_client.delete_tags(
            Resources=[source_ami_id],
            Tags=[{"Key": test_tag_key}],
        )


def test_can_update_ssm_parameter_with_ami_id(ssm_client, source_ami_id):
    """Verify we can update an SSM parameter with an AMI ID."""
    test_parameter_name = "/ami/ec2-runner/integration-test"

    # Clean up any existing test parameter
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
            Description="Integration test parameter",
        )

        response = ssm_client.get_parameter(Name=test_parameter_name)
        parameter_value = response["Parameter"]["Value"]

        assert parameter_value == source_ami_id
    finally:
        ssm_client.delete_parameter(Name=test_parameter_name)
