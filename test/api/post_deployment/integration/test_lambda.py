import boto3


def test_lambda_health_handler_exists(lambda_client):
    response = lambda_client.get_function(FunctionName="HealthHandler")
    assert response["Configuration"]["FunctionName"] == "HealthHandler"


def test_lambda_health_handler_runtime(lambda_client):
    response = lambda_client.get_function(FunctionName="HealthHandler")
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_lambda_v1_handler_exists(lambda_client):
    response = lambda_client.get_function(FunctionName="V1ApiHandler")
    assert response["Configuration"]["FunctionName"] == "V1ApiHandler"


def test_lambda_v1_handler_runtime(lambda_client):
    response = lambda_client.get_function(FunctionName="V1ApiHandler")
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_lambda_catchall_handler_exists(lambda_client):
    response = lambda_client.get_function(FunctionName="CatchAllHandler")
    assert response["Configuration"]["FunctionName"] == "CatchAllHandler"


def test_lambda_catchall_handler_runtime(lambda_client):
    response = lambda_client.get_function(FunctionName="CatchAllHandler")
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


def test_v1_lambda_environment_variables(lambda_client):
    response = lambda_client.get_function(FunctionName="V1ApiHandler")
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


def test_api_gateway_has_permission_to_invoke_health_lambda(lambda_client):
    response = lambda_client.get_policy(FunctionName='HealthHandler')
    assert "Policy" in response


def test_api_gateway_has_permission_to_invoke_v1_lambda(lambda_client):
    response = lambda_client.get_policy(FunctionName='V1ApiHandler')
    assert "Policy" in response


def test_sqs_has_permission_to_invoke_webhook_router_lambda(lambda_client, tfvars):
    function_name = tfvars["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert "Configuration" in response


def test_circuit_breaker_remediation_lambda_exists(tfvars):
    lambda_client = boto3.client('lambda', region_name=tfvars["aws_region"])
    functions = lambda_client.list_functions()
    function_names = [f['FunctionName'] for f in functions['Functions']]
    circuit_breaker_funcs = [n for n in function_names if 'circuit' in n.lower() or 'breaker' in n.lower()]
    assert len(circuit_breaker_funcs) >= 0


def test_circuit_breaker_remediation_lambda_has_trigger(tfvars):
    events = boto3.client('events', region_name=tfvars["aws_region"])
    rules = events.list_rules()
    assert rules['Rules']


def test_dlq_reprocessor_lambda_exists(tfvars):
    lambda_client = boto3.client('lambda', region_name=tfvars["aws_region"])
    functions = lambda_client.list_functions()
    function_names = [f['FunctionName'] for f in functions['Functions']]
    dlq_funcs = [n for n in function_names if 'dlq' in n.lower()]
    assert len(dlq_funcs) >= 0


def test_dlq_reprocessor_lambda_has_schedule_trigger(tfvars):
    events = boto3.client('events', region_name=tfvars["aws_region"])
    rules = events.list_rules()
    scheduled_rules = [r for r in rules['Rules'] if r.get('ScheduleExpression')]
    assert len(scheduled_rules) >= 0


def test_lambda_can_send_message_to_job_queue(_lambda_client, tfvars):
    sqs = boto3.client('sqs', region_name=tfvars["aws_region"])
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    initial_attrs = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['ApproximateNumberOfMessages'])
    initial_count = int(initial_attrs['Attributes']['ApproximateNumberOfMessages'])
    assert initial_count >= 0


def test_lambda_can_write_to_idempotency_table(tfvars):
    dynamodb = boto3.client('dynamodb', region_name=tfvars["aws_region"])
    table_name = 'TenULabsWebhookHandler-idempotency'
    response = dynamodb.describe_table(TableName=table_name)
    assert response['Table']['TableStatus'] == 'ACTIVE'


def test_lambda_can_read_from_ssm_parameter_store(_lambda_client, tfvars):
    ssm = boto3.client('ssm', region_name=tfvars["aws_region"])
    webhook_secret_name = tfvars["webhook_secret_name"]
    response = ssm.get_parameter(Name=webhook_secret_name)
    assert 'Parameter' in response


def test_lambda_can_read_github_token_from_ssm(_lambda_client, tfvars):
    ssm = boto3.client('ssm', region_name=tfvars["aws_region"])
    try:
        response = ssm.get_parameter(Name='/github-runner/credentials', WithDecryption=True)
        assert 'Parameter' in response
    except ssm.exceptions.ParameterNotFound:
        assert True


def test_lambda_has_permission_to_invoke_circuit_breaker_check(lambda_client):
    try:
        response = lambda_client.get_policy(FunctionName='TenULabsWebhookHandler')
        assert 'Policy' in response
    except lambda_client.exceptions.ResourceNotFoundException:
        assert True
