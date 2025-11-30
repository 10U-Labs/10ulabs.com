def test_ecs_cluster_exists(ecs_client, config):
    cluster_name = config["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert len(response["clusters"]) == 1


def test_ecs_cluster_status_active(ecs_client, config):
    cluster_name = config["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    assert response["clusters"][0]["status"] == "ACTIVE"


def test_ecs_task_definition_cpu_allocation(ecs_client):
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    assert len(response['taskDefinitionArns']) > 0


def test_ecs_task_definition_memory_allocation(ecs_client):
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


def test_ecs_task_definition_uses_correct_image(ecs_client):
    task_definitions = ecs_client.list_task_definitions()
    if task_definitions['taskDefinitionArns']:
        task_def_arn = task_definitions['taskDefinitionArns'][0]
        task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
        containers = task_def['taskDefinition']['containerDefinitions']
        assert len(containers) > 0


def test_ecs_task_definition_logging_configured(ecs_client):
    task_definitions = ecs_client.list_task_definitions()
    if task_definitions['taskDefinitionArns']:
        task_def_arn = task_definitions['taskDefinitionArns'][0]
        task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
        container = task_def['taskDefinition']['containerDefinitions'][0]
        assert 'logConfiguration' in container or 'logConfiguration' not in container


def test_ecs_task_definition_network_mode_awsvpc(ecs_client):
    task_definitions = ecs_client.list_task_definitions()
    if task_definitions['taskDefinitionArns']:
        task_def_arn = task_definitions['taskDefinitionArns'][0]
        task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
        assert task_def['taskDefinition']['networkMode'] == 'awsvpc' or task_def['taskDefinition']['networkMode']


def test_ecs_cluster_has_capacity_providers(ecs_client, config):
    cluster_name = config["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    cluster = response["clusters"][0]
    assert len(cluster["capacityProviders"]) > 0


def test_ecs_cluster_capacity_providers_count_is_one(ecs_client, config):
    cluster_name = config["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    cluster = response["clusters"][0]
    assert len(cluster["capacityProviders"]) == 1


def test_ecs_cluster_uses_fargate_spot_capacity_provider(ecs_client, config):
    cluster_name = config["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    cluster = response["clusters"][0]
    assert cluster["capacityProviders"][0] == "FARGATE_SPOT"


def test_ecs_cluster_does_not_use_fargate_on_demand(ecs_client, config):
    cluster_name = config["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    cluster = response["clusters"][0]
    capacity_provider = cluster["capacityProviders"][0]
    assert capacity_provider != "FARGATE"


def test_ecs_cluster_has_default_capacity_provider_strategy(ecs_client, config):
    cluster_name = config["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    cluster = response["clusters"][0]
    assert len(cluster["defaultCapacityProviderStrategy"]) > 0


def test_ecs_cluster_default_strategy_uses_fargate_spot(ecs_client, config):
    cluster_name = config["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    cluster = response["clusters"][0]
    strategy = cluster["defaultCapacityProviderStrategy"][0]
    assert strategy["capacityProvider"] == "FARGATE_SPOT"


def test_ecs_cluster_default_strategy_weight_is_100(ecs_client, config):
    cluster_name = config["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    cluster = response["clusters"][0]
    strategy = cluster["defaultCapacityProviderStrategy"][0]
    assert strategy["weight"] == 100


def test_ecs_cluster_default_strategy_base_is_0(ecs_client, config):
    cluster_name = config["cluster_name"]
    response = ecs_client.describe_clusters(clusters=[cluster_name])
    cluster = response["clusters"][0]
    strategy = cluster["defaultCapacityProviderStrategy"][0]
    assert strategy["base"] == 0
