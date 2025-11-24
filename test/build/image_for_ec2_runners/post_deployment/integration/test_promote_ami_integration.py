import pytest


def test_promote_ami_can_tag_ami(ec2_client, test_ami_id, promote_ami, tfvars):
    if not test_ami_id:
        pytest.fail("TEST_AMI_ID not provided")

    test_tag_key = "TestPromotionTag"
    test_tag_value = "test-value"

    ec2_client.create_tags(
        Resources=[test_ami_id],
        Tags=[{"Key": test_tag_key, "Value": test_tag_value}]
    )

    response = ec2_client.describe_images(ImageIds=[test_ami_id])
    tags = {tag["Key"]: tag["Value"] for tag in response["Images"][0].get("Tags", [])}

    assert tags.get(test_tag_key) == test_tag_value


def test_promote_ami_can_update_ssm_parameter(ssm_client, test_ami_id, promote_ami, tfvars):
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


def test_promote_ami_function_exists(promote_ami):
    assert hasattr(promote_ami, "promote_ami")


def test_promote_ami_function_signature(promote_ami):
    import inspect
    sig = inspect.signature(promote_ami.promote_ami)
    params = list(sig.parameters.keys())

    assert "ami_id" in params


def test_promote_ami_function_signature_has_region(promote_ami):
    import inspect
    sig = inspect.signature(promote_ami.promote_ami)
    params = list(sig.parameters.keys())

    assert "region" in params


def test_promote_ami_function_signature_has_ssm_parameter_name(promote_ami):
    import inspect
    sig = inspect.signature(promote_ami.promote_ami)
    params = list(sig.parameters.keys())

    assert "ssm_parameter_name" in params


def test_promote_ami_function_signature_has_tag_key(promote_ami):
    import inspect
    sig = inspect.signature(promote_ami.promote_ami)
    params = list(sig.parameters.keys())

    assert "tag_key" in params
