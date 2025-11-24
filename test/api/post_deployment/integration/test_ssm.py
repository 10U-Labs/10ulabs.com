def test_webhook_secret_parameter_exists(ssm_client, tfvars):
    webhook_secret_name = tfvars["webhook_secret_name"]
    response = ssm_client.get_parameter(Name=webhook_secret_name)
    assert response["Parameter"]["Name"] == webhook_secret_name


def test_webhook_secret_parameter_type(ssm_client, tfvars):
    webhook_secret_name = tfvars["webhook_secret_name"]
    response = ssm_client.get_parameter(Name=webhook_secret_name)
    assert response["Parameter"]["Type"] == "String"


def test_webhook_secret_parameter_value_not_placeholder(ssm_client, tfvars):
    webhook_secret_name = tfvars["webhook_secret_name"]
    response = ssm_client.get_parameter(Name=webhook_secret_name, WithDecryption=True)
    assert response["Parameter"]["Value"] != "PLACEHOLDER_WILL_BE_UPDATED"
