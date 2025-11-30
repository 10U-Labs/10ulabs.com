import pytest


def _find_tag_value(tags, key):
    for tag in tags:
        if tag["Key"] == key:
            return tag["Value"]
    return None


def test_promote_ami_can_tag_ami(ec2_client, test_ami_id):
    if not test_ami_id:
        pytest.fail("TEST_AMI_ID not provided")

    test_tag_key = "TestPromotionTag"
    test_tag_value = "test-value"

    ec2_client.create_tags(
        Resources=[test_ami_id],
        Tags=[{"Key": test_tag_key, "Value": test_tag_value}]
    )

    response = ec2_client.describe_images(ImageIds=[test_ami_id])
    tags = response["Images"][0].get("Tags", [])
    actual_value = _find_tag_value(tags, test_tag_key)

    assert actual_value == test_tag_value


def test_promote_ami_can_update_ssm_parameter(ssm_client, test_ami_id):
    if not test_ami_id:
        pytest.fail("TEST_AMI_ID not provided")

    test_parameter_name = "/github-runner/ami/integration-test"

    try:
        ssm_client.delete_parameter(Name=test_parameter_name)
    except ssm_client.exceptions.ParameterNotFound:
        pass

    ssm_client.put_parameter(
        Name=test_parameter_name,
        Value=test_ami_id,
        Type="String",
        Overwrite=True,
        Description="Integration test parameter"
    )

    response = ssm_client.get_parameter(Name=test_parameter_name)
    parameter_value = response["Parameter"]["Value"]

    assert parameter_value == test_ami_id

    ssm_client.delete_parameter(Name=test_parameter_name)
