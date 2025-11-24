def test_webhook_secret_parameter_exists(ssm_client, tfvars):
    ssm_parameter_name_for_webhook_secret = tfvars["ssm_parameter_name_for_webhook_secret"]
    response = ssm_client.get_parameter(Name=ssm_parameter_name_for_webhook_secret)
    assert response["Parameter"]["Name"] == ssm_parameter_name_for_webhook_secret


def test_webhook_secret_parameter_type(ssm_client, tfvars):
    ssm_parameter_name_for_webhook_secret = tfvars["ssm_parameter_name_for_webhook_secret"]
    response = ssm_client.get_parameter(Name=ssm_parameter_name_for_webhook_secret)
    assert response["Parameter"]["Type"] == "String"


def test_webhook_secret_parameter_value_not_placeholder(ssm_client, tfvars):
    ssm_parameter_name_for_webhook_secret = tfvars["ssm_parameter_name_for_webhook_secret"]
    response = ssm_client.get_parameter(Name=ssm_parameter_name_for_webhook_secret, WithDecryption=True)
    assert response["Parameter"]["Value"] != "PLACEHOLDER_WILL_BE_UPDATED"
