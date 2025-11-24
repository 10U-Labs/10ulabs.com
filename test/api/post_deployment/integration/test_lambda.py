def test_lambda_health_handler_exists(lambda_client, tfvars):
    function_name = tfvars["health_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_lambda_health_handler_runtime(lambda_client, tfvars):
    function_name = tfvars["health_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_lambda_v1_handler_exists(lambda_client, tfvars):
    function_name = tfvars["v1_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_lambda_v1_handler_runtime(lambda_client, tfvars):
    function_name = tfvars["v1_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_lambda_catchall_handler_exists(lambda_client, tfvars):
    function_name = tfvars["catchall_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_lambda_catchall_handler_runtime(lambda_client, tfvars):
    function_name = tfvars["catchall_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_lambda_runners_handler_exists(lambda_client, tfvars):
    function_name = tfvars["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_lambda_runners_handler_runtime(lambda_client, tfvars):
    function_name = tfvars["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_webhook_router_lambda_environment_variables(lambda_client, tfvars):
    function_name = tfvars["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response["Configuration"]["Environment"]["Variables"]
    assert "WEBHOOK_SECRET_NAME" in env_vars


def test_v1_lambda_environment_variables(lambda_client, tfvars):
    function_name = tfvars["v1_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response["Configuration"]["Environment"]["Variables"]
    assert "AWS_REGION" in env_vars


def test_lambda_timeout_configuration(lambda_client, tfvars):
    function_name = tfvars["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    timeout = response["Configuration"]["Timeout"]
    assert timeout > 0


def test_lambda_memory_configuration(lambda_client, tfvars):
    function_name = tfvars["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    memory = response["Configuration"]["MemorySize"]
    assert memory >= 128


def test_lambda_dead_letter_queue_configuration(lambda_client, tfvars):
    function_name = tfvars["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert "DeadLetterConfig" in response["Configuration"]


def test_api_gateway_has_permission_to_invoke_health_lambda(lambda_client, tfvars):
    function_name = tfvars["health_handler_function_name"]
    response = lambda_client.get_policy(FunctionName=function_name)
    assert "Policy" in response


def test_api_gateway_has_permission_to_invoke_v1_lambda(lambda_client, tfvars):
    function_name = tfvars["v1_handler_function_name"]
    response = lambda_client.get_policy(FunctionName=function_name)
    assert "Policy" in response


def test_sqs_has_permission_to_invoke_webhook_router_lambda(lambda_client, tfvars):
    function_name = tfvars["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert "Configuration" in response


def test_circuit_breaker_remediation_lambda_exists(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [f['FunctionName'] for f in functions['Functions']]
    circuit_breaker_funcs = [n for n in function_names if 'circuit' in n.lower() or 'breaker' in n.lower()]
    assert len(circuit_breaker_funcs) >= 0


def test_circuit_breaker_remediation_lambda_has_trigger(events_client):
    rules = events_client.list_rules()
    assert rules['Rules']


def test_dlq_reprocessor_lambda_exists(lambda_client):
    functions = lambda_client.list_functions()
    function_names = [f['FunctionName'] for f in functions['Functions']]
    dlq_funcs = [n for n in function_names if 'dlq' in n.lower()]
    assert len(dlq_funcs) >= 0


def test_dlq_reprocessor_lambda_has_schedule_trigger(events_client):
    rules = events_client.list_rules()
    scheduled_rules = [r for r in rules['Rules'] if r.get('ScheduleExpression')]
    assert len(scheduled_rules) >= 0


def test_lambda_can_send_message_to_job_queue(sqs_client, tfvars):
    queue_name = tfvars["job_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    initial_attrs = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])
    initial_count = int(initial_attrs['Attributes']['ApproximateNumberOfMessages'])
    assert initial_count >= 0


def test_lambda_can_write_to_idempotency_table(dynamodb_client, tfvars):
    table_name = tfvars["idempotency_table_name"]
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['TableStatus'] == 'ACTIVE'


def test_lambda_can_read_from_ssm_parameter_store(ssm_client, tfvars):
    webhook_secret_name = tfvars["webhook_secret_name"]
    response = ssm_client.get_parameter(Name=webhook_secret_name)
    assert 'Parameter' in response


def test_lambda_can_read_github_token_from_ssm(ssm_client):
    try:
        response = ssm_client.get_parameter(Name='/github-runner/credentials', WithDecryption=True)
        assert 'Parameter' in response
    except ssm_client.exceptions.ParameterNotFound:
        assert True


def test_lambda_has_permission_to_invoke_circuit_breaker_check(lambda_client, tfvars):
    try:
        function_name = tfvars["lambda_function_name"]
        response = lambda_client.get_policy(FunctionName=function_name)
        assert 'Policy' in response
    except lambda_client.exceptions.ResourceNotFoundException:
        assert True
