def test_ecs_task_definition_has_runtime_platform(ecs_client):
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    task_def_arn = response['taskDefinitionArns'][-1]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    assert 'runtimePlatform' in task_def['taskDefinition']


def test_ecs_task_definition_runtime_platform_not_none(ecs_client):
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    task_def_arn = response['taskDefinitionArns'][-1]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    assert task_def['taskDefinition']['runtimePlatform'] is not None


def test_ecs_task_definition_runtime_platform_has_cpu_architecture(ecs_client):
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    task_def_arn = response['taskDefinitionArns'][-1]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    assert 'cpuArchitecture' in task_def['taskDefinition']['runtimePlatform']


def test_ecs_task_definition_runtime_platform_has_operating_system_family(ecs_client):
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    task_def_arn = response['taskDefinitionArns'][-1]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    assert 'operatingSystemFamily' in task_def['taskDefinition']['runtimePlatform']


def test_ecs_task_definition_cpu_architecture_is_arm64(ecs_client):
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    task_def_arn = response['taskDefinitionArns'][-1]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    assert task_def['taskDefinition']['runtimePlatform']['cpuArchitecture'] == 'ARM64'


def test_ecs_task_definition_operating_system_family_is_linux(ecs_client):
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    task_def_arn = response['taskDefinitionArns'][-1]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    assert task_def['taskDefinition']['runtimePlatform']['operatingSystemFamily'] == 'LINUX'


def test_ecs_task_definition_has_cpu_value(ecs_client):
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    task_def_arn = response['taskDefinitionArns'][-1]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    assert 'cpu' in task_def['taskDefinition']


def test_ecs_task_definition_cpu_is_valid_fargate_value(ecs_client):
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    task_def_arn = response['taskDefinitionArns'][-1]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    cpu = task_def['taskDefinition']['cpu']
    assert cpu in ['256', '512', '1024', '2048', '4096']


def test_ecs_task_definition_has_memory_value(ecs_client):
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    task_def_arn = response['taskDefinitionArns'][-1]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    assert 'memory' in task_def['taskDefinition']


def test_ecs_task_definition_memory_is_valid_for_cpu(ecs_client):
    response = ecs_client.list_task_definitions(familyPrefix='github-runner', status='ACTIVE')
    task_def_arn = response['taskDefinitionArns'][-1]
    task_def = ecs_client.describe_task_definition(taskDefinition=task_def_arn)
    cpu = int(task_def['taskDefinition']['cpu'])
    memory = int(task_def['taskDefinition']['memory'])
    assert memory >= cpu * 2
