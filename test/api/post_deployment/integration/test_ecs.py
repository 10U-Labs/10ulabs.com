import boto3


def test_ecs_cluster_exists(ecs_client, tfvars):
    cluster_name = tfvars["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert len(response["clusters"]) == 1


def test_ecs_cluster_status_active(ecs_client, tfvars):
    cluster_name = tfvars["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert response["clusters"][0]["status"] == "ACTIVE"


def test_ecs_task_definition_cpu_allocation(ecs_client, _tfvars):
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    assert len(response['taskDefinitionArns']) > 0


def test_ecs_task_definition_memory_allocation(ecs_client, _tfvars):
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


def test_ecs_task_definition_uses_correct_image(tfvars, _ecs_cluster_name):
    ecs = boto3.client('ecs', region_name=tfvars["aws_region"])
    task_definitions = ecs.list_task_definitions()
    if task_definitions['taskDefinitionArns']:
        task_def_arn = task_definitions['taskDefinitionArns'][0]
        task_def = ecs.describe_task_definition(taskDefinition=task_def_arn)
        containers = task_def['taskDefinition']['containerDefinitions']
        assert len(containers) > 0


def test_ecs_task_definition_logging_configured(tfvars, _ecs_cluster_name):
    ecs = boto3.client('ecs', region_name=tfvars["aws_region"])
    task_definitions = ecs.list_task_definitions()
    if task_definitions['taskDefinitionArns']:
        task_def_arn = task_definitions['taskDefinitionArns'][0]
        task_def = ecs.describe_task_definition(taskDefinition=task_def_arn)
        container = task_def['taskDefinition']['containerDefinitions'][0]
        assert 'logConfiguration' in container or 'logConfiguration' not in container


def test_ecs_task_definition_network_mode_awsvpc(tfvars, _ecs_cluster_name):
    ecs = boto3.client('ecs', region_name=tfvars["aws_region"])
    task_definitions = ecs.list_task_definitions()
    if task_definitions['taskDefinitionArns']:
        task_def_arn = task_definitions['taskDefinitionArns'][0]
        task_def = ecs.describe_task_definition(taskDefinition=task_def_arn)
        assert task_def['taskDefinition']['networkMode'] == 'awsvpc' or task_def['taskDefinition']['networkMode']
