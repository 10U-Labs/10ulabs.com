# 10ulabs.com

## Workflow Dependency Graph

```
bootstrap
    ↓
www_shared
    ↓
api_backend
    ↓
operational_health
    ↓
api_shared_runners
    ↓
endpoint_v1_image_for_ec2_runners
    ↓
endpoint_v1_ec2_runner
    ↓
api_shared_ecs_runner
    ↓
endpoint_v1_image_for_ecs_runners
    ↓
endpoint_v1_ecs_runner
    ↓
endpoint_v1_runners
    ↓
endpoint_v1_echo
    ↓
endpoint_v1_contact
    ↓
www_index
    ↓
endpoint_v1_rack_designer
    ↓
endpoint_v1_simulation_soc
    ↓
endpoint_v1_agents_shared
    ↓
endpoint_v1_agents_troubleshooter_of_workflows
    ↓
endpoint_v1_agents_creator_of_agents
    ↓
endpoint_v1_agents_evaluator_of_agents
    ↓
endpoint_v1_agents_modifier_of_agents
    ↓
endpoint_v1_agents_deleter_of_agents
    ↓
endpoint_v1_agents_evaluator_of_workflows
    ↓
endpoint_v1_agents_creator_of_workflows
    ↓
endpoint_v1_agents_modifier_of_workflows
    ↓
endpoint_v1_agents_deleter_of_workflows
    ↓
endpoint_v1_agents_creator_of_unit_tests
    ↓
endpoint_v1_agents_code_reviewer_of_pre_deployment_integration_tests
    ↓
endpoint_v1_agents_creator_of_pre_deployment_integration_tests
    ↓
endpoint_v1_agents_creator_of_post_deployment_integration_tests
    ↓
endpoint_v1_agents_creator_of_e2e_tests
    ↓
endpoint_v1_agents_modifier_of_unit_tests
    ↓
endpoint_v1_agents_modifier_of_pre_deployment_integration_tests
    ↓
endpoint_v1_agents_modifier_of_post_deployment_integration_tests
    ↓
endpoint_v1_agents_modifier_of_e2e_tests
    ↓
endpoint_v1_agents_deleter_of_unit_tests
    ↓
endpoint_v1_agents_deleter_of_pre_deployment_integration_tests
    ↓
endpoint_v1_agents_deleter_of_post_deployment_integration_tests
    ↓
endpoint_v1_agents_deleter_of_e2e_tests
```

## Deployment Status

- [x] `api_backend.yml`
- [x] `api_shared_ecs_runner.yml`
- [x] `api_shared_runners.yml`
- [x] `bootstrap.yml`
- [x] `operational_health.yml`
- [ ] `endpoint_v1_agents_code_reviewer_of_pre_deployment_integration_tests.yml`
- [ ] `endpoint_v1_agents_creator_of_agents.yml`
- [ ] `endpoint_v1_agents_creator_of_e2e_tests.yml`
- [ ] `endpoint_v1_agents_creator_of_post_deployment_integration_tests.yml`
- [ ] `endpoint_v1_agents_creator_of_pre_deployment_integration_tests.yml`
- [ ] `endpoint_v1_agents_creator_of_unit_tests.yml`
- [ ] `endpoint_v1_agents_creator_of_workflows.yml`
- [ ] `endpoint_v1_agents_deleter_of_agents.yml`
- [ ] `endpoint_v1_agents_deleter_of_e2e_tests.yml`
- [ ] `endpoint_v1_agents_deleter_of_post_deployment_integration_tests.yml`
- [ ] `endpoint_v1_agents_deleter_of_pre_deployment_integration_tests.yml`
- [ ] `endpoint_v1_agents_deleter_of_unit_tests.yml`
- [ ] `endpoint_v1_agents_deleter_of_workflows.yml`
- [ ] `endpoint_v1_agents_evaluator_of_agents.yml`
- [ ] `endpoint_v1_agents_evaluator_of_workflows.yml`
- [ ] `endpoint_v1_agents_modifier_of_agents.yml`
- [ ] `endpoint_v1_agents_modifier_of_e2e_tests.yml`
- [ ] `endpoint_v1_agents_modifier_of_post_deployment_integration_tests.yml`
- [ ] `endpoint_v1_agents_modifier_of_pre_deployment_integration_tests.yml`
- [ ] `endpoint_v1_agents_modifier_of_unit_tests.yml`
- [ ] `endpoint_v1_agents_modifier_of_workflows.yml`
- [ ] `endpoint_v1_agents_shared.yml`
- [ ] `endpoint_v1_agents_troubleshooter_of_workflows.yml`
- [x] `endpoint_v1_contact.yml`
- [x] `endpoint_v1_ec2_runner.yml`
- [x] `endpoint_v1_echo.yml`
- [x] `endpoint_v1_ecs_runner.yml`
- [x] `endpoint_v1_image_for_ec2_runners.yml`
- [x] `endpoint_v1_image_for_ec2_runners_post.yml`
- [x] `endpoint_v1_image_for_ecs_runners.yml`
- [x] `endpoint_v1_image_for_ecs_runners_post.yml`
- [x] `endpoint_v1_rack_designer.yml`
- [x] `endpoint_v1_runners.yml`
- [x] `endpoint_v1_simulation_soc.yml`
- [x] `www_index.yml`
- [x] `www_shared.yml`
