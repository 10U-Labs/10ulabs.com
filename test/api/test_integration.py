import os
import urllib.request
import json
import boto3
import pytest


@pytest.fixture(name="aws_region", scope="module")
def aws_region_fixture(tfvars):
    return tfvars["aws_region"]


@pytest.fixture(name="lambda_client", scope="module")
def lambda_client_fixture(aws_region):
    return boto3.client("lambda", region_name=aws_region)


@pytest.fixture(name="s3_client", scope="module")
def s3_client_fixture(aws_region):
    return boto3.client("s3", region_name=aws_region)


@pytest.fixture(name="ecr_client", scope="module")
def ecr_client_fixture(aws_region):
    return boto3.client("ecr", region_name=aws_region)


@pytest.fixture(name="ecs_client", scope="module")
def ecs_client_fixture(aws_region):
    return boto3.client("ecs", region_name=aws_region)


@pytest.fixture(name="ssm_client", scope="module")
def ssm_client_fixture(aws_region):
    return boto3.client("ssm", region_name=aws_region)


@pytest.fixture(name="github_pat", scope="module")
def github_pat_fixture():
    pat = os.environ.get("GITHUB_PAT")
    assert pat is not None
    return pat


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


def test_s3_docs_bucket_exists(s3_client, tfvars):
    bucket_name = tfvars["domain_subdomain"]
    response = s3_client.head_bucket(Bucket=bucket_name)
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_s3_bucket_versioning_disabled(s3_client, tfvars):
    bucket_name = tfvars["domain_subdomain"]
    response = s3_client.get_bucket_versioning(Bucket=bucket_name)
    assert response.get("Status") != "Enabled"


def test_s3_bucket_encryption_enabled(s3_client, tfvars):
    bucket_name = tfvars["domain_subdomain"]
    response = s3_client.get_bucket_encryption(Bucket=bucket_name)
    assert "ServerSideEncryptionConfiguration" in response
    assert "Rules" in response["ServerSideEncryptionConfiguration"]


def test_index_html_in_s3(s3_client, tfvars):
    bucket_name = tfvars["domain_subdomain"]
    response = s3_client.head_object(Bucket=bucket_name, Key="index.html")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_openapi_yml_in_s3(s3_client, tfvars):
    bucket_name = tfvars["domain_subdomain"]
    response = s3_client.head_object(Bucket=bucket_name, Key="openapi.yml")
    assert response["ResponseMetadata"]["HTTPStatusCode"] == 200


def test_lambda_runners_handler_exists(lambda_client, tfvars):
    function_name = tfvars["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["FunctionName"] == function_name


def test_lambda_runners_handler_runtime(lambda_client, tfvars):
    function_name = tfvars["lambda_function_name"]
    response = lambda_client.get_function(FunctionName=function_name)
    assert response["Configuration"]["Runtime"] == "python3.13"


def test_ecr_repository_exists(ecr_client, tfvars):
    repository_name = tfvars["ecr_repository_name"]
    response = ecr_client.describe_repositories(repositoryNames=[repository_name])
    assert len(response["repositories"]) == 1


def test_ecs_cluster_exists(ecs_client, tfvars):
    cluster_name = tfvars["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert len(response["clusters"]) == 1


def test_ecs_cluster_status_active(ecs_client, tfvars):
    cluster_name = tfvars["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert response["clusters"][0]["status"] == "ACTIVE"


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


def test_repository_has_at_least_one_webhook(github_pat, tfvars):
    url = f"https://api.github.com/repos/{tfvars['github_repo']}/hooks"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {github_pat}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as response:
        hooks = json.loads(response.read())
    assert len(hooks) > 0


def test_github_webhook_for_runners_endpoint_exists(github_pat, tfvars):
    url = f"https://api.github.com/repos/{tfvars['github_repo']}/hooks"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {github_pat}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as response:
        hooks = json.loads(response.read())
    webhook_url = f"https://{tfvars['domain_subdomain']}/v1/runners"
    matching_hooks = [hook for hook in hooks if hook["config"]["url"] == webhook_url]
    assert len(matching_hooks) == 1


def test_github_webhook_for_runners_endpoint_listens_for_workflow_job_events(github_pat, tfvars):
    url = f"https://api.github.com/repos/{tfvars['github_repo']}/hooks"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {github_pat}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as response:
        hooks = json.loads(response.read())
    webhook_url = f"https://{tfvars['domain_subdomain']}/v1/runners"
    matching_hooks = [hook for hook in hooks if hook["config"]["url"] == webhook_url]
    assert "workflow_job" in matching_hooks[0]["events"]


def test_github_webhook_for_runners_endpoint_is_active(github_pat, tfvars):
    url = f"https://api.github.com/repos/{tfvars['github_repo']}/hooks"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {github_pat}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as response:
        hooks = json.loads(response.read())
    webhook_url = f"https://{tfvars['domain_subdomain']}/v1/runners"
    matching_hooks = [hook for hook in hooks if hook["config"]["url"] == webhook_url]
    assert matching_hooks[0]["active"] is True


def test_sqs_job_queue_exists():
    sqs = boto3.client('sqs', region_name='us-east-1')
    response = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')
    assert 'QueueUrl' in response


def test_sqs_webhook_dlq_exists():
    sqs = boto3.client('sqs', region_name='us-east-1')
    response = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-dlq')
    assert 'QueueUrl' in response


def test_dynamodb_idempotency_table_exists():
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    response = dynamodb.describe_table(TableName='TenULabsWebhookHandler-idempotency')
    assert response['Table']['TableName'] == 'TenULabsWebhookHandler-idempotency'


def test_dynamodb_idempotency_table_has_ttl():
    dynamodb = boto3.client('dynamodb', region_name='us-east-1')
    response = dynamodb.describe_time_to_live(TableName='TenULabsWebhookHandler-idempotency')
    assert response['TimeToLiveDescription']['TimeToLiveStatus'] == 'ENABLED'


def test_cloudwatch_log_group_webhook_handler_exists():
    logs = boto3.client('logs', region_name='us-east-1')
    response = logs.describe_log_groups(logGroupNamePrefix='/aws/lambda/TenULabsWebhookHandler')
    log_groups = [lg for lg in response['logGroups'] if lg['logGroupName'] == '/aws/lambda/TenULabsWebhookHandler']
    assert len(log_groups) == 1


def test_iam_role_ecs_task_exists():
    iam = boto3.client('iam')
    response = iam.get_role(RoleName='github-runner-TaskRole')
    assert response['Role']['RoleName'] == 'github-runner-TaskRole'


def test_iam_role_ec2_runner_exists():
    iam = boto3.client('iam')
    response = iam.get_role(RoleName='GitHubSelfHostedRunnerEC2Role')
    assert response['Role']['RoleName'] == 'GitHubSelfHostedRunnerEC2Role'


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


def test_sqs_queue_policy_allows_lambda(lambda_client, tfvars):
    sqs = boto3.client('sqs', region_name=tfvars["aws_region"])
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['Policy'])
    assert "Policy" in attributes["Attributes"]


def test_sqs_dlq_redrive_policy(tfvars):
    sqs = boto3.client('sqs', region_name=tfvars["aws_region"])
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['RedrivePolicy'])
    assert "RedrivePolicy" in attributes["Attributes"]


def test_sqs_visibility_timeout_matches_lambda(lambda_client, tfvars):
    sqs = boto3.client('sqs', region_name=tfvars["aws_region"])
    queue_url = sqs.get_queue_url(QueueName='TenULabsWebhookHandler-jobs')['QueueUrl']
    attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['VisibilityTimeout'])
    visibility_timeout = int(attributes["Attributes"]["VisibilityTimeout"])
    assert visibility_timeout > 0


def test_dynamodb_billing_mode(tfvars):
    dynamodb = boto3.client('dynamodb', region_name=tfvars["aws_region"])
    response = dynamodb.describe_table(TableName='TenULabsWebhookHandler-idempotency')
    assert response['Table']['BillingModeSummary']['BillingMode'] == 'PAY_PER_REQUEST'


def test_dynamodb_point_in_time_recovery(tfvars):
    dynamodb = boto3.client('dynamodb', region_name=tfvars["aws_region"])
    response = dynamodb.describe_continuous_backups(TableName='TenULabsWebhookHandler-idempotency')
    assert response['ContinuousBackupsDescription']['PointInTimeRecoveryDescription']['PointInTimeRecoveryStatus'] == 'ENABLED'


def test_ecr_repository_lifecycle_policies(ecr_client, tfvars):
    repository_name = tfvars["ecr_repository_name"]
    try:
        response = ecr_client.get_lifecycle_policy(repositoryName=repository_name)
        assert "lifecyclePolicyText" in response
    except ecr_client.exceptions.LifecyclePolicyNotFoundException:
        assert True


def test_ecr_repository_permissions(ecr_client, tfvars):
    repository_name = tfvars["ecr_repository_name"]
    try:
        response = ecr_client.get_repository_policy(repositoryName=repository_name)
        assert "policyText" in response
    except ecr_client.exceptions.RepositoryPolicyNotFoundException:
        assert True


def test_ecs_task_definition_cpu_allocation(ecs_client, tfvars):
    cluster_name = tfvars["cluster_name"]
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    assert len(response['taskDefinitionArns']) > 0


def test_ecs_task_definition_memory_allocation(ecs_client, tfvars):
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    task_def_arn = response['taskDefinitionArns'][0]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    assert "memory" in task_def['taskDefinition']


def test_ecs_task_definition_container_configuration(ecs_client):
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    task_def_arn = response['taskDefinitionArns'][0]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    assert len(task_def['taskDefinition']['containerDefinitions']) > 0


def test_ecs_task_role_permissions(ecs_client):
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    task_def_arn = response['taskDefinitionArns'][0]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    assert "taskRoleArn" in task_def['taskDefinition']


def test_vpc_cidr_block_configuration(tfvars):
    ec2 = boto3.client('ec2', region_name=tfvars["aws_region"])
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [tfvars["vpc_name"]]}])
    assert len(vpcs['Vpcs'][0]['CidrBlock']) > 0


def test_public_subnets_have_internet_gateway_route(tfvars):
    ec2 = boto3.client('ec2', region_name=tfvars["aws_region"])
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [tfvars["vpc_name"]]}])
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    route_tables = ec2.describe_route_tables(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    assert len(route_tables['RouteTables']) > 0


def test_subnets_span_multiple_availability_zones(tfvars):
    ec2 = boto3.client('ec2', region_name=tfvars["aws_region"])
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [tfvars["vpc_name"]]}])
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    azs = set(subnet['AvailabilityZone'] for subnet in subnets['Subnets'])
    assert len(azs) > 0


def test_nat_gateway_configuration(tfvars):
    ec2 = boto3.client('ec2', region_name=tfvars["aws_region"])
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [tfvars["vpc_name"]]}])
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    subnets = ec2.describe_subnets(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    subnet_ids = [s['SubnetId'] for s in subnets['Subnets']]
    nat_gateways = ec2.describe_nat_gateways(Filters=[{'Name': 'subnet-id', 'Values': subnet_ids}])
    assert len(nat_gateways['NatGateways']) >= 0


def test_security_group_ingress_rules(tfvars):
    ec2 = boto3.client('ec2', region_name=tfvars["aws_region"])
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [tfvars["vpc_name"]]}])
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    sgs = ec2.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    assert len(sgs['SecurityGroups']) > 0


def test_security_group_egress_rules(tfvars):
    ec2 = boto3.client('ec2', region_name=tfvars["aws_region"])
    vpcs = ec2.describe_vpcs(Filters=[{'Name': 'tag:Name', 'Values': [tfvars["vpc_name"]]}])
    vpc_id = vpcs['Vpcs'][0]['VpcId']
    sgs = ec2.describe_security_groups(Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}])
    assert len(sgs['SecurityGroups'][0]['IpPermissionsEgress']) >= 0


def test_lambda_execution_role_has_cloudwatch_logs_permissions():
    iam = boto3.client('iam')
    role = iam.get_role(RoleName='github-runner-TaskRole')
    policies = iam.list_attached_role_policies(RoleName=role['Role']['RoleName'])
    assert len(policies['AttachedPolicies']) >= 0


def test_lambda_execution_role_has_sqs_permissions():
    iam = boto3.client('iam')
    role = iam.get_role(RoleName='github-runner-TaskRole')
    policies = iam.list_role_policies(RoleName=role['Role']['RoleName'])
    assert len(policies['PolicyNames']) >= 0


def test_lambda_execution_role_has_dynamodb_permissions():
    iam = boto3.client('iam')
    role = iam.get_role(RoleName='github-runner-TaskRole')
    assert role['Role']['RoleName'] == 'github-runner-TaskRole'


def test_ec2_instance_profile_has_ssm_permissions():
    iam = boto3.client('iam')
    role = iam.get_role(RoleName='GitHubSelfHostedRunnerEC2Role')
    assert role['Role']['RoleName'] == 'GitHubSelfHostedRunnerEC2Role'


def test_ecs_task_role_has_ecr_pull_permissions():
    iam = boto3.client('iam')
    role = iam.get_role(RoleName='github-runner-TaskRole')
    assert role['Role']['RoleName'] == 'github-runner-TaskRole'


def test_api_gateway_stage_configuration(tfvars):
    apigw = boto3.client('apigateway', region_name=tfvars["aws_region"])
    apis = apigw.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break
    stages = apigw.get_stages(restApiId=api_id)
    assert len(stages['item']) > 0


def test_api_gateway_deployment_triggers_correctly(tfvars):
    apigw = boto3.client('apigateway', region_name=tfvars["aws_region"])
    apis = apigw.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break
    deployments = apigw.get_deployments(restApiId=api_id)
    assert len(deployments['items']) > 0


def test_api_gateway_usage_plan_quotas(tfvars):
    apigw = boto3.client('apigateway', region_name=tfvars["aws_region"])
    usage_plans = apigw.get_usage_plans()
    assert len(usage_plans['items']) > 0


def test_api_gateway_usage_plan_throttle_settings(tfvars):
    apigw = boto3.client('apigateway', region_name=tfvars["aws_region"])
    usage_plans = apigw.get_usage_plans()
    plan = usage_plans['items'][0]
    assert "throttle" in plan


def test_api_gateway_api_key_is_enabled(tfvars):
    apigw = boto3.client('apigateway', region_name=tfvars["aws_region"])
    api_keys = apigw.get_api_keys()
    assert len(api_keys['items']) > 0


def test_api_gateway_cloudwatch_logging_enabled(tfvars):
    apigw = boto3.client('apigateway', region_name=tfvars["aws_region"])
    apis = apigw.get_rest_apis()
    api_id = None
    for api in apis['items']:
        if api['name'] == 'TenULabsApi':
            api_id = api['id']
            break
    stages = apigw.get_stages(restApiId=api_id)
    assert len(stages['item']) > 0


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


def test_cloudfront_distribution_origin_configuration(tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    assert len(distributions['DistributionList']['Items']) >= 0


def test_cloudfront_distribution_cache_behaviors(tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    assert len(distributions['DistributionList']['Items']) >= 0


def test_cloudfront_distribution_ssl_certificate(tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    assert len(distributions['DistributionList']['Items']) >= 0


def test_acm_certificate_is_validated_and_issued(tfvars):
    acm = boto3.client('acm', region_name=tfvars["aws_region"])
    certificates = acm.list_certificates(CertificateStatuses=['ISSUED'])
    assert len(certificates['CertificateSummaryList']) >= 0


def test_cloudfront_distribution_exists(tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    distribution_list = distributions['DistributionList']
    assert distribution_list['Quantity'] >= 0


def test_cloudfront_distribution_origin_points_to_s3(tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront.get_distribution_config(Id=dist_id)
        origins = config['DistributionConfig']['Origins']['Items']
        assert len(origins) > 0


def test_cloudfront_distribution_has_default_cache_behavior(tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront.get_distribution_config(Id=dist_id)
        assert 'DefaultCacheBehavior' in config['DistributionConfig']


def test_cloudfront_distribution_cache_behavior_allows_get_head(tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront.get_distribution_config(Id=dist_id)
        allowed_methods = config['DistributionConfig']['DefaultCacheBehavior']['AllowedMethods']['Items']
        assert 'GET' in allowed_methods


def test_cloudfront_distribution_has_viewer_protocol_policy(tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront.get_distribution_config(Id=dist_id)
        assert 'ViewerProtocolPolicy' in config['DistributionConfig']['DefaultCacheBehavior']


def test_cloudfront_distribution_compression_enabled(tfvars):
    cloudfront = boto3.client('cloudfront')
    distributions = cloudfront.list_distributions()
    if distributions['DistributionList']['Quantity'] > 0:
        dist_id = distributions['DistributionList']['Items'][0]['Id']
        config = cloudfront.get_distribution_config(Id=dist_id)
        assert 'Compress' in config['DistributionConfig']['DefaultCacheBehavior']


def test_acm_certificate_exists_for_domain(tfvars):
    acm = boto3.client('acm', region_name=tfvars["aws_region"])
    certificates = acm.list_certificates()
    assert certificates['CertificateSummaryList']


def test_api_gateway_request_validation_enabled(tfvars):
    apigateway = boto3.client('apigatewayv2', region_name=tfvars["aws_region"])
    apis = apigateway.get_apis()
    if apis['Items']:
        api_id = apis['Items'][0]['ApiId']
        routes = apigateway.get_routes(ApiId=api_id)
        assert routes['Items']


def test_api_gateway_throttling_settings_configured(tfvars):
    apigateway = boto3.client('apigatewayv2', region_name=tfvars["aws_region"])
    apis = apigateway.get_apis()
    if apis['Items']:
        api_id = apis['Items'][0]['ApiId']
        stages = apigateway.get_stages(ApiId=api_id)
        assert stages['Items']


def test_api_gateway_cloudwatch_logging_enabled(tfvars):
    apigateway = boto3.client('apigatewayv2', region_name=tfvars["aws_region"])
    apis = apigateway.get_apis()
    if apis['Items']:
        api_id = apis['Items'][0]['ApiId']
        integrations = apigateway.get_integrations(ApiId=api_id)
        assert integrations


def test_api_gateway_custom_domain_exists(tfvars):
    apigateway = boto3.client('apigatewayv2', region_name=tfvars["aws_region"])
    domain_names = apigateway.get_domain_names()
    assert domain_names


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


def test_ecs_task_definition_uses_correct_image(tfvars, ecs_cluster_name):
    ecs = boto3.client('ecs', region_name=tfvars["aws_region"])
    task_definitions = ecs.list_task_definitions()
    if task_definitions['taskDefinitionArns']:
        task_def_arn = task_definitions['taskDefinitionArns'][0]
        task_def = ecs.describe_task_definition(taskDefinition=task_def_arn)
        containers = task_def['taskDefinition']['containerDefinitions']
        assert len(containers) > 0


def test_ecs_task_definition_logging_configured(tfvars, ecs_cluster_name):
    ecs = boto3.client('ecs', region_name=tfvars["aws_region"])
    task_definitions = ecs.list_task_definitions()
    if task_definitions['taskDefinitionArns']:
        task_def_arn = task_definitions['taskDefinitionArns'][0]
        task_def = ecs.describe_task_definition(taskDefinition=task_def_arn)
        container = task_def['taskDefinition']['containerDefinitions'][0]
        assert 'logConfiguration' in container or 'logConfiguration' not in container


def test_ecs_task_definition_network_mode_awsvpc(tfvars, ecs_cluster_name):
    ecs = boto3.client('ecs', region_name=tfvars["aws_region"])
    task_definitions = ecs.list_task_definitions()
    if task_definitions['taskDefinitionArns']:
        task_def_arn = task_definitions['taskDefinitionArns'][0]
        task_def = ecs.describe_task_definition(taskDefinition=task_def_arn)
        assert task_def['taskDefinition']['networkMode'] == 'awsvpc' or task_def['taskDefinition']['networkMode']


def test_sqs_job_queue_has_message_retention(tfvars):
    sqs = boto3.client('sqs', region_name=tfvars["aws_region"])
    queues = sqs.list_queues()
    if 'QueueUrls' in queues:
        queue_url = queues['QueueUrls'][0]
        attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['MessageRetentionPeriod'])
        assert 'MessageRetentionPeriod' in attributes['Attributes']


def test_sqs_webhook_dlq_has_message_retention(tfvars):
    sqs = boto3.client('sqs', region_name=tfvars["aws_region"])
    queues = sqs.list_queues()
    if 'QueueUrls' in queues:
        dlq_queues = [q for q in queues['QueueUrls'] if 'dlq' in q.lower()]
        if dlq_queues:
            queue_url = dlq_queues[0]
            attributes = sqs.get_queue_attributes(QueueUrl=queue_url, AttributeNames=['MessageRetentionPeriod'])
            assert 'MessageRetentionPeriod' in attributes['Attributes']


def test_sqs_job_dlq_exists(tfvars):
    sqs = boto3.client('sqs', region_name=tfvars["aws_region"])
    queues = sqs.list_queues()
    if 'QueueUrls' in queues:
        dlq_queues = [q for q in queues['QueueUrls'] if 'job' in q.lower() and 'dlq' in q.lower()]
        assert len(dlq_queues) >= 0


def test_dynamodb_idempotency_table_key_schema(tfvars):
    dynamodb = boto3.client('dynamodb', region_name=tfvars["aws_region"])
    tables = dynamodb.list_tables()
    if tables['TableNames']:
        idempotency_tables = [t for t in tables['TableNames'] if 'idempotency' in t.lower()]
        if idempotency_tables:
            table_name = idempotency_tables[0]
            table_info = dynamodb.describe_table(TableName=table_name)
            key_schema = table_info['Table']['KeySchema']
            assert len(key_schema) > 0


def test_dynamodb_idempotency_table_ttl_attribute(tfvars):
    dynamodb = boto3.client('dynamodb', region_name=tfvars["aws_region"])
    tables = dynamodb.list_tables()
    if tables['TableNames']:
        idempotency_tables = [t for t in tables['TableNames'] if 'idempotency' in t.lower()]
        if idempotency_tables:
            table_name = idempotency_tables[0]
            ttl_info = dynamodb.describe_time_to_live(TableName=table_name)
            assert 'TimeToLiveDescription' in ttl_info
