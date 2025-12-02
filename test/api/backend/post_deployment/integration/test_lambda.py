def test_lambda_catchall_handler_exists(lambda_client, config):
    function_name = config["catchall_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    names_match = response["Configuration"]["FunctionName"] == function_name
    assert names_match


def test_lambda_catchall_handler_runtime(lambda_client, config):
    function_name = config["catchall_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    is_python313 = response["Configuration"]["Runtime"] == "python3.13"
    assert is_python313


def test_api_gateway_has_permission_to_invoke_health_lambda(lambda_client, config):
    function_name = config["health_handler_function_name"]
    response = lambda_client.get_policy(FunctionName=function_name)
    has_policy = "Policy" in response
    assert has_policy
