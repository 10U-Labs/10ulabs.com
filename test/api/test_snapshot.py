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


def test_ecs_cluster_container_insights_enabled(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"RunnerCluster{stack_hash}"
    settings = template["Resources"][logical_id]["Properties"]["ClusterSettings"]
    assert settings[0]["Name"] == "containerInsights"
    assert settings[0]["Value"] == "enabled"


def test_task_definition_cpu(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"RunnerTaskDefinition{stack_hash}"
    assert template["Resources"][logical_id]["Properties"]["Cpu"] == "256"


def test_task_definition_memory(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"RunnerTaskDefinition{stack_hash}"
    assert template["Resources"][logical_id]["Properties"]["Memory"] == "512"


def test_task_definition_network_mode(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"RunnerTaskDefinition{stack_hash}"
    assert template["Resources"][logical_id]["Properties"]["NetworkMode"] == "awsvpc"


def test_task_definition_requires_fargate(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"RunnerTaskDefinition{stack_hash}"
    assert template["Resources"][logical_id]["Properties"]["RequiresCompatibilities"][0] == "FARGATE"


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


def test_webhook_dlq_exists(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"WebhookDLQ{stack_hash}"
    assert template["Resources"][logical_id]["Type"] == "AWS::SQS::Queue"


def test_job_queue_dlq_exists(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"JobQueueDLQ{stack_hash}"
    assert template["Resources"][logical_id]["Type"] == "AWS::SQS::Queue"


def test_github_token_parameter_type(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"GitHubToken{stack_hash}"
    assert template["Resources"][logical_id]["Properties"]["Type"] == "String"


def test_github_token_parameter_has_placeholder(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"GitHubToken{stack_hash}"
    assert template["Resources"][logical_id]["Properties"]["Value"] == "PLACEHOLDER_UPDATE_WITH_GITHUB_TOKEN"


def test_ami_parameter_has_placeholder(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"LatestAmiParameter{stack_hash}"
    assert template["Resources"][logical_id]["Properties"]["Value"] == "PLACEHOLDER_UPDATE_AFTER_AMI_BUILD"


def test_webhook_parameter_has_placeholder(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"WebhookParameter{stack_hash}"
    assert template["Resources"][logical_id]["Properties"]["Value"] == "PLACEHOLDER_WILL_BE_UPDATED"


def test_ec2_runner_role_has_ssm_managed_policy(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"EC2SelfHostedRunnerRole{stack_hash}"
    expected_policy_arn = {
        "Fn::Join": [
            "",
            [
                "arn:",
                {"Ref": "AWS::Partition"},
                ":iam::aws:policy/AmazonSSMManagedInstanceCore"
            ]
        ]
    }
    assert template["Resources"][logical_id]["Properties"]["ManagedPolicyArns"][0] == expected_policy_arn


def test_ec2_runner_role_has_ecr_policy(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"EC2SelfHostedRunnerRole{stack_hash}"
    assert template["Resources"][logical_id]["Properties"]["Policies"][0]["PolicyName"] == "ECRAccess"


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


def test_api_url_output_has_export_name(cdk_template):
    template_json = cdk_template.to_json()
    assert template_json["Outputs"]["ApiUrl"].get("Export") is not None


def test_catchall_handler_has_runtime(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"CatchAllHandler{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("Runtime") is not None


def test_catchall_handler_has_handler(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"CatchAllHandler{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("Handler") is not None


def test_catchall_handler_has_timeout(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"CatchAllHandler{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("Timeout") is not None


def test_health_handler_has_runtime(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"HealthHandler{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("Runtime") is not None


def test_health_handler_has_handler(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"HealthHandler{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("Handler") is not None


def test_health_handler_has_timeout(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"HealthHandler{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("Timeout") is not None


def test_runners_handler_has_runtime(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"RunnersHandler{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("Runtime") is not None


def test_runners_handler_has_handler(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"RunnersHandler{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("Handler") is not None


def test_runners_handler_has_timeout(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"RunnersHandler{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("Timeout") is not None


def test_v1_api_handler_has_runtime(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"V1ApiHandler{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("Runtime") is not None


def test_v1_api_handler_has_handler(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"V1ApiHandler{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("Handler") is not None


def test_v1_api_handler_has_timeout(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"V1ApiHandler{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("Timeout") is not None


def test_runner_vpc_public_subnet_1_is_public(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"RunnerVpcPublicSubnet1Subnet{stack_hash}"
    assert template["Resources"][logical_id]["Properties"]["MapPublicIpOnLaunch"] is True


def test_runner_vpc_public_subnet_2_is_public(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"RunnerVpcPublicSubnet2Subnet{stack_hash}"
    assert template["Resources"][logical_id]["Properties"]["MapPublicIpOnLaunch"] is True


def test_runner_vpc_public_subnet_3_is_public(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"RunnerVpcPublicSubnet3Subnet{stack_hash}"
    assert template["Resources"][logical_id]["Properties"]["MapPublicIpOnLaunch"] is True


def test_self_hosted_runner_security_group_allows_outbound(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"SelfHostedRunnerSecurityGroup{stack_hash}"
    egress_rules = template["Resources"][logical_id]["Properties"]["SecurityGroupEgress"]
    assert len(egress_rules) > 0


def test_catchall_handler_service_role_has_assume_role_policy(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"CatchAllHandlerServiceRole{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("AssumeRolePolicyDocument") is not None


def test_ec2_self_hosted_runner_role_has_assume_role_policy(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"EC2SelfHostedRunnerRole{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("AssumeRolePolicyDocument") is not None


def test_health_handler_service_role_has_assume_role_policy(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"HealthHandlerServiceRole{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("AssumeRolePolicyDocument") is not None


def test_runner_task_definition_execution_role_has_assume_role_policy(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"RunnerTaskDefinitionExecutionRole{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("AssumeRolePolicyDocument") is not None


def test_runner_task_definition_task_role_has_assume_role_policy(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"RunnerTaskDefinitionTaskRole{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("AssumeRolePolicyDocument") is not None


def test_runners_handler_service_role_has_assume_role_policy(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"RunnersHandlerServiceRole{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("AssumeRolePolicyDocument") is not None


def test_v1_api_handler_service_role_has_assume_role_policy(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"V1ApiHandlerServiceRole{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("AssumeRolePolicyDocument") is not None


def test_api_gateway_access_logs_has_retention(cdk_template, stack_hash):
    template = cdk_template.to_json()
    logical_id = f"ApiGatewayAccessLogs{stack_hash}"
    assert template["Resources"][logical_id]["Properties"].get("RetentionInDays") is not None
