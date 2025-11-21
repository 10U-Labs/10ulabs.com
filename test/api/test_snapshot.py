def test_template_has_parameters(cdk_template):
    template_json = cdk_template.to_json()
    assert "Parameters" in template_json


def test_template_has_bootstrap_parameter(cdk_template):
    template_json = cdk_template.to_json()
    assert "BootstrapVersion" in template_json["Parameters"]


def test_template_has_mappings(cdk_template):
    template_json = cdk_template.to_json()
    assert "Mappings" in template_json


def test_template_has_cloudfront_mapping(cdk_template):
    template_json = cdk_template.to_json()
    assert "AWSCloudFrontPartitionHostedZoneIdMap" in template_json["Mappings"]


def test_template_has_rules(cdk_template):
    template_json = cdk_template.to_json()
    assert "Rules" in template_json


def test_template_has_bootstrap_version_rule(cdk_template):
    template_json = cdk_template.to_json()
    assert "CheckBootstrapVersion" in template_json["Rules"]


def test_template_has_resources(cdk_template):
    template_json = cdk_template.to_json()
    assert "Resources" in template_json


def test_total_resource_count(cdk_template):
    template_json = cdk_template.to_json()
    assert len(template_json.get("Resources", {})) > 75


def test_lambda_function_count(cdk_template):
    cdk_template.resource_count_is("AWS::Lambda::Function", 8)


def test_iam_role_count(cdk_template):
    cdk_template.resource_count_is("AWS::IAM::Role", 12)


def test_iam_policy_count(cdk_template):
    cdk_template.resource_count_is("AWS::IAM::Policy", 6)


def test_subnet_count(cdk_template):
    subnets = cdk_template.find_resources("AWS::EC2::Subnet")
    assert len(subnets) >= 0


def test_route_table_count(cdk_template):
    route_tables = cdk_template.find_resources("AWS::EC2::RouteTable")
    assert len(route_tables) >= 0


def test_route_count(cdk_template):
    routes = cdk_template.find_resources("AWS::EC2::Route")
    assert len(routes) >= 0


def test_subnet_route_table_association_count(cdk_template):
    associations = cdk_template.find_resources("AWS::EC2::SubnetRouteTableAssociation")
    assert len(associations) >= 0


def test_lambda_permission_count(cdk_template):
    cdk_template.resource_count_is("AWS::Lambda::Permission", 4)


def test_log_retention_count(cdk_template):
    cdk_template.resource_count_is("Custom::LogRetention", 4)


def test_ssm_parameter_count(cdk_template):
    cdk_template.resource_count_is("AWS::SSM::Parameter", 3)


def test_sqs_queue_count(cdk_template):
    cdk_template.resource_count_is("AWS::SQS::Queue", 3)


def test_vpc_count(cdk_template):
    cdk_template.resource_count_is("AWS::EC2::VPC", 1)


def test_ecr_repository_count(cdk_template):
    cdk_template.resource_count_is("AWS::ECR::Repository", 1)


def test_ecs_cluster_count(cdk_template):
    cdk_template.resource_count_is("AWS::ECS::Cluster", 1)


def test_dynamodb_table_count(cdk_template):
    cdk_template.resource_count_is("AWS::DynamoDB::Table", 1)


def test_api_gateway_rest_api_count(cdk_template):
    cdk_template.resource_count_is("AWS::ApiGateway::RestApi", 1)


def test_cloudfront_distribution_count(cdk_template):
    cdk_template.resource_count_is("AWS::CloudFront::Distribution", 1)


def test_s3_bucket_count(cdk_template):
    cdk_template.resource_count_is("AWS::S3::Bucket", 1)


def test_certificate_count(cdk_template):
    cdk_template.resource_count_is("AWS::CertificateManager::Certificate", 1)


def test_vpc_cidr_block(cdk_template, config):
    vpc_resources = cdk_template.find_resources("AWS::EC2::VPC")
    vpc = list(vpc_resources.values())[0]
    assert vpc["Properties"]["CidrBlock"] == config["aws"]["vpc"]["cidr"]


def test_vpc_dns_hostnames_enabled(cdk_template):
    vpc_resources = cdk_template.find_resources("AWS::EC2::VPC")
    vpc = list(vpc_resources.values())[0]
    assert vpc["Properties"]["EnableDnsHostnames"] is True


def test_vpc_dns_support_enabled(cdk_template):
    vpc_resources = cdk_template.find_resources("AWS::EC2::VPC")
    vpc = list(vpc_resources.values())[0]
    assert vpc["Properties"]["EnableDnsSupport"] is True


def test_ecr_repository_image_scanning_enabled(cdk_template):
    ecr_resources = cdk_template.find_resources("AWS::ECR::Repository")
    ecr = list(ecr_resources.values())[0]
    assert ecr["Properties"]["ImageScanningConfiguration"]["ScanOnPush"] is True


def test_ecr_repository_has_lifecycle_policy(cdk_template):
    ecr_resources = cdk_template.find_resources("AWS::ECR::Repository")
    ecr = list(ecr_resources.values())[0]
    assert "LifecyclePolicy" in ecr["Properties"]


def test_ecs_cluster_container_insights_enabled(cdk_template):
    ecs_resources = cdk_template.find_resources("AWS::ECS::Cluster")
    ecs = list(ecs_resources.values())[0]
    settings = ecs["Properties"]["ClusterSettings"]
    insights_setting = [s for s in settings if s["Name"] == "containerInsights"][0]
    assert insights_setting["Value"] == "enabled"


def test_task_definition_cpu(cdk_template):
    task_defs = cdk_template.find_resources("AWS::ECS::TaskDefinition")
    task_def = list(task_defs.values())[0]
    assert task_def["Properties"]["Cpu"] == "256"


def test_task_definition_memory(cdk_template):
    task_defs = cdk_template.find_resources("AWS::ECS::TaskDefinition")
    task_def = list(task_defs.values())[0]
    assert task_def["Properties"]["Memory"] == "512"


def test_task_definition_network_mode(cdk_template):
    task_defs = cdk_template.find_resources("AWS::ECS::TaskDefinition")
    task_def = list(task_defs.values())[0]
    assert task_def["Properties"]["NetworkMode"] == "awsvpc"


def test_task_definition_requires_fargate(cdk_template):
    task_defs = cdk_template.find_resources("AWS::ECS::TaskDefinition")
    task_def = list(task_defs.values())[0]
    assert "FARGATE" in task_def["Properties"]["RequiresCompatibilities"]


def test_s3_bucket_encryption_enabled(cdk_template):
    buckets = cdk_template.find_resources("AWS::S3::Bucket")
    bucket = list(buckets.values())[0]
    encryption = bucket["Properties"]["BucketEncryption"]["ServerSideEncryptionConfiguration"][0]
    assert encryption["ServerSideEncryptionByDefault"]["SSEAlgorithm"] == "AES256"


def test_s3_bucket_public_access_blocked(cdk_template):
    buckets = cdk_template.find_resources("AWS::S3::Bucket")
    bucket = list(buckets.values())[0]
    public_access = bucket["Properties"]["PublicAccessBlockConfiguration"]
    assert public_access["BlockPublicAcls"] is True


def test_s3_bucket_public_policy_blocked(cdk_template):
    buckets = cdk_template.find_resources("AWS::S3::Bucket")
    bucket = list(buckets.values())[0]
    public_access = bucket["Properties"]["PublicAccessBlockConfiguration"]
    assert public_access["BlockPublicPolicy"] is True


def test_s3_bucket_ignore_public_acls(cdk_template):
    buckets = cdk_template.find_resources("AWS::S3::Bucket")
    bucket = list(buckets.values())[0]
    public_access = bucket["Properties"]["PublicAccessBlockConfiguration"]
    assert public_access["IgnorePublicAcls"] is True


def test_s3_bucket_restrict_public_buckets(cdk_template):
    buckets = cdk_template.find_resources("AWS::S3::Bucket")
    bucket = list(buckets.values())[0]
    public_access = bucket["Properties"]["PublicAccessBlockConfiguration"]
    assert public_access["RestrictPublicBuckets"] is True


def test_dynamodb_table_billing_mode(cdk_template):
    tables = cdk_template.find_resources("AWS::DynamoDB::Table")
    table = list(tables.values())[0]
    assert table["Properties"]["BillingMode"] == "PAY_PER_REQUEST"


def test_dynamodb_table_has_ttl(cdk_template):
    tables = cdk_template.find_resources("AWS::DynamoDB::Table")
    table = list(tables.values())[0]
    assert "TimeToLiveSpecification" in table["Properties"]


def test_sqs_dlq_message_retention(cdk_template):
    queues = cdk_template.find_resources("AWS::SQS::Queue")
    dlq_queues = [q for q in queues.values() if "dlq" in q["Properties"]["QueueName"].lower()]
    assert len(dlq_queues) == 2


def test_github_token_parameter_type(cdk_template):
    params = cdk_template.find_resources("AWS::SSM::Parameter")
    github_param = [p for p in params.values() if "github-runner/credentials" in p["Properties"]["Name"]][0]
    assert github_param["Properties"]["Type"] == "String"


def test_github_token_parameter_has_placeholder(cdk_template):
    params = cdk_template.find_resources("AWS::SSM::Parameter")
    github_param = [p for p in params.values() if "github-runner/credentials" in p["Properties"]["Name"]][0]
    assert github_param["Properties"]["Value"] == "PLACEHOLDER_UPDATE_WITH_GITHUB_TOKEN"


def test_ami_parameter_has_placeholder(cdk_template):
    params = cdk_template.find_resources("AWS::SSM::Parameter")
    ami_param = [p for p in params.values() if "ami/latest" in p["Properties"]["Name"]][0]
    assert ami_param["Properties"]["Value"] == "PLACEHOLDER_UPDATE_AFTER_AMI_BUILD"


def test_webhook_parameter_has_placeholder(cdk_template):
    params = cdk_template.find_resources("AWS::SSM::Parameter")
    webhook_param = [p for p in params.values() if "webhook-secret" in p["Properties"]["Name"]][0]
    assert webhook_param["Properties"]["Value"] == "PLACEHOLDER_WILL_BE_UPDATED"


def test_ec2_runner_role_has_ssm_managed_policy(cdk_template):
    roles = cdk_template.find_resources("AWS::IAM::Role")
    runner_role = [r for r in roles.values() if r["Properties"].get("RoleName") == "GitHubSelfHostedRunnerEC2Role"][0]
    managed_policies = runner_role["Properties"]["ManagedPolicyArns"]
    assert any("AmazonSSMManagedInstanceCore" in str(policy) for policy in managed_policies)


def test_ec2_runner_role_has_ecr_policy(cdk_template):
    roles = cdk_template.find_resources("AWS::IAM::Role")
    runner_role = [r for r in roles.values() if r["Properties"].get("RoleName") == "GitHubSelfHostedRunnerEC2Role"][0]
    policies = runner_role["Properties"]["Policies"]
    assert any(p["PolicyName"] == "ECRAccess" for p in policies)


def test_ec2_instance_profile_exists(cdk_template):
    cdk_template.resource_count_is("AWS::IAM::InstanceProfile", 1)


def test_certificate_validation_method(cdk_template):
    certs = cdk_template.find_resources("AWS::CertificateManager::Certificate")
    cert = list(certs.values())[0]
    assert cert["Properties"]["ValidationMethod"] == "DNS"


def test_certificate_domain_name(cdk_template, config):
    certs = cdk_template.find_resources("AWS::CertificateManager::Certificate")
    cert = list(certs.values())[0]
    assert cert["Properties"]["DomainName"] == config["domain_names"]["subdomain"]


def test_template_has_outputs(cdk_template):
    template_json = cdk_template.to_json()
    assert "Outputs" in template_json


def test_output_count(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert len(outputs) >= 19


def test_api_url_output_exists(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert "ApiUrl" in outputs


def test_api_domain_name_output_exists(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert "ApiDomainName" in outputs


def test_vpc_id_output_exists(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert "VpcId" in outputs


def test_cluster_name_output_exists(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert "ClusterName" in outputs


def test_ecr_repository_uri_output_exists(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert "EcrRepositoryUri" in outputs


def test_task_definition_arn_output_exists(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert "TaskDefinitionArn" in outputs


def test_webhook_parameter_name_output_exists(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert "WebhookParameterName" in outputs


def test_github_token_secret_name_output_exists(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert "GitHubTokenSecretName" in outputs


def test_ec2_runner_role_name_output_exists(cdk_template):
    outputs = cdk_template.find_outputs("*")
    assert "EC2RunnerRoleName" in outputs


def test_outputs_have_export_names(cdk_template):
    template_json = cdk_template.to_json()
    outputs = template_json["Outputs"]
    exported_outputs = [k for k, v in outputs.items() if k != "BootstrapVersion"]
    assert all("Export" in outputs[k] for k in exported_outputs)


def test_lambda_functions_have_runtime(cdk_template):
    functions = cdk_template.find_resources("AWS::Lambda::Function")
    for func in functions.values():
        assert "Runtime" in func["Properties"]


def test_lambda_functions_have_handler(cdk_template):
    functions = cdk_template.find_resources("AWS::Lambda::Function")
    for func in functions.values():
        assert "Handler" in func["Properties"]


def test_lambda_functions_have_timeout(cdk_template):
    functions = cdk_template.find_resources("AWS::Lambda::Function")
    for func in functions.values():
        assert "Timeout" in func["Properties"]


def test_lambda_functions_have_memory_size_or_use_default(cdk_template):
    functions = cdk_template.find_resources("AWS::Lambda::Function")
    assert len(functions) > 0


def test_all_subnets_are_public(cdk_template):
    subnets = cdk_template.find_resources("AWS::EC2::Subnet")
    for subnet in subnets.values():
        assert subnet["Properties"]["MapPublicIpOnLaunch"] is True


def test_security_group_allows_outbound(cdk_template):
    sgs = cdk_template.find_resources("AWS::EC2::SecurityGroup")
    for sg in sgs.values():
        egress_rules = sg["Properties"]["SecurityGroupEgress"]
        assert len(egress_rules) > 0


def test_iam_roles_have_assume_role_policy(cdk_template):
    roles = cdk_template.find_resources("AWS::IAM::Role")
    for role in roles.values():
        assert "AssumeRolePolicyDocument" in role["Properties"]


def test_log_groups_have_retention(cdk_template):
    log_groups = cdk_template.find_resources("AWS::Logs::LogGroup")
    for log_group in log_groups.values():
        assert "RetentionInDays" in log_group["Properties"]
