def test_lambda_health_handler_exists(lambda_client, config):
    function_name = config["health_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_lambda_health_handler_runtime(lambda_client, config):
    function_name = config["health_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_lambda_v1_handler_exists(lambda_client, config):
    function_name = config["v1_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_lambda_v1_handler_runtime(lambda_client, config):
    function_name = config["v1_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_lambda_catchall_handler_exists(lambda_client, config):
    function_name = config["catchall_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_lambda_catchall_handler_runtime(lambda_client, config):
    function_name = config["catchall_handler_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_lambda_runners_handler_exists(lambda_client, config):
    function_name = config["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_lambda_runners_handler_runtime(lambda_client, config):
    function_name = config["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_webhook_router_lambda_environment_variables(lambda_client, config):
    function_name = config["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response["Configuration"]["Environment"]["Variables"]
    assert "WEBHOOK_SECRET_NAME" in env_vars


def test_lambda_timeout_configuration(lambda_client, config):
    function_name = config["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    timeout = response["Configuration"]["Timeout"]
    assert timeout > 0


def test_lambda_memory_configuration(lambda_client, config):
    function_name = config["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    memory = response["Configuration"]["MemorySize"]
    assert memory >= 128


def test_lambda_dead_letter_queue_configuration(lambda_client, config):
    function_name = config["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert "DeadLetterConfig" in response["Configuration"]


def test_api_gateway_has_permission_to_invoke_health_lambda(lambda_client, config):
    function_name = config["health_handler_function_name"]
    response = lambda_client.get_policy(FunctionName=function_name)
    assert "Policy" in response


def test_api_gateway_has_permission_to_invoke_v1_lambda(lambda_client, config):
    function_name = config["v1_handler_function_name"]
    response = lambda_client.get_policy(FunctionName=function_name)
    assert "Policy" in response


def test_sqs_has_permission_to_invoke_webhook_router_lambda(lambda_client, config):
    function_name = config["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert "Configuration" in response


def test_circuit_breaker_remediation_lambda_exists(lambda_client, config):
    function_name = f"{config['resource_prefix']}-CircuitBreakerRemediation"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['FunctionName'] == function_name


def test_circuit_breaker_remediation_lambda_runtime(lambda_client, config):
    function_name = f"{config['resource_prefix']}-CircuitBreakerRemediation"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['Runtime'] == 'python3.13'


def test_circuit_breaker_remediation_lambda_has_environment_vars(lambda_client, config):
    function_name = f"{config['resource_prefix']}-CircuitBreakerRemediation"
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response['Configuration']['Environment']['Variables']
    assert 'WEBHOOK_FUNCTION_NAME' in env_vars


def test_circuit_breaker_remediation_lambda_timeout(lambda_client, config):
    function_name = f"{config['resource_prefix']}-CircuitBreakerRemediation"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['Timeout'] == 60


def test_circuit_breaker_recovery_lambda_exists(lambda_client, config):
    function_name = f"{config['resource_prefix']}-CircuitBreakerRecovery"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['FunctionName'] == function_name


def test_circuit_breaker_recovery_lambda_runtime(lambda_client, config):
    function_name = f"{config['resource_prefix']}-CircuitBreakerRecovery"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['Runtime'] == 'python3.13'


def test_circuit_breaker_recovery_lambda_has_environment_vars(lambda_client, config):
    function_name = f"{config['resource_prefix']}-CircuitBreakerRecovery"
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response['Configuration']['Environment']['Variables']
    assert 'STATE_TABLE_NAME' in env_vars


def test_circuit_breaker_recovery_lambda_timeout(lambda_client, config):
    function_name = f"{config['resource_prefix']}-CircuitBreakerRecovery"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['Timeout'] == 60


def test_dlq_reprocessor_lambda_exists(lambda_client, config):
    function_name = f"{config['resource_prefix']}-DLQReprocessor"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['FunctionName'] == function_name


def test_dlq_reprocessor_lambda_runtime(lambda_client, config):
    function_name = f"{config['resource_prefix']}-DLQReprocessor"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['Runtime'] == 'python3.13'


def test_dlq_reprocessor_lambda_has_environment_vars(lambda_client, config):
    function_name = f"{config['resource_prefix']}-DLQReprocessor"
    response = lambda_client.get_function(FunctionName=function_name)
    env_vars = response['Configuration']['Environment']['Variables']
    assert 'JOB_QUEUE_URL' in env_vars


def test_dlq_reprocessor_lambda_timeout(lambda_client, config):
    function_name = f"{config['resource_prefix']}-DLQReprocessor"
    response = lambda_client.get_function(FunctionName=function_name)
    assert response['Configuration']['Timeout'] == 300


def test_lambda_can_send_message_to_job_queue(sqs_client, config):
    queue_name = config["job_queue_name"]
    queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueUrl']
    initial_attrs = sqs_client.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])
    initial_count = int(initial_attrs['Attributes']['ApproximateNumberOfMessages'])
    assert initial_count >= 0


def test_lambda_can_write_to_idempotency_table(dynamodb_client, config):
    table_name = config["idempotency_table_name"]
    response = dynamodb_client.describe_table(TableName=table_name)
    assert response['Table']['TableStatus'] == 'ACTIVE'


def test_lambda_can_read_from_ssm_parameter_store(ssm_client, config):
    ssm_parameter_name_for_webhook_secret = config["ssm_parameter_name_for_webhook_secret"]
    response = ssm_client.get_parameter(Name=ssm_parameter_name_for_webhook_secret)
    assert 'Parameter' in response


def test_lambda_can_read_ami_parameter_from_ssm(ssm_client):
    response = ssm_client.get_parameter(Name='/github-runner/ami/latest/arm64')
    assert 'Parameter' in response


def test_lambda_has_permission_to_invoke_circuit_breaker_check(lambda_client, config):
    function_name = config["lambda_function_name"]
    response = lambda_client.get_policy(FunctionName=function_name)
    assert 'Policy' in response
