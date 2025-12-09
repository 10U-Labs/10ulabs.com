# 10ulabs.com

## Workflow Dependency Graph

```
bootstrap
    │
    ├── www_shared
    │       │
    │       └── api_backend
    │               │
    │               └── endpoint_health
    │                       │
    │                       ├── api_shared_runners ─────────────────────────────────┐
    │                       │       │                                                │
    │                       │       └── endpoint_v1_image_for_ec2_runners_post       │
    │                       │               │                                        │
    │                       │               └── endpoint_v1_image_for_ec2_runners    │
    │                       │                       │                                │
    │                       │                       └── endpoint_v1_ec2_runner ──────┤
    │                       │                                                        │
    │                       └── api_shared_ecs_runner ───────────────────────────────┤
    │                                                                                │
    │                                               endpoint_v1_image_for_ecs_runners
    │                                                            │
    │                                               endpoint_v1_ecs_runner ──────────┤
    │                                                                                │
    │                                                                     endpoint_v1_runners
    │                                                                                │
    │                                 ┌───────────────────────────┬──────────────────┼──────────────────────┐
    │                                 │                           │                  │                      │
    │                         endpoint_v1_echo           endpoint_v1_contact         │         endpoint_v1_rack_designer
    │                                                             │                  │                      │
    │                                                        www_index               │         endpoint_v1_simulation_soc
    │                                                                                │
    └────────────────────────────────────────────────────────────────────────────────┤
                                                                                     │
                                                                              agents_shared
                                                                                     │
                                                              agents_troubleshooter_of_workflows
                                                                                     │
                    ┌────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────┐
                    │                                                                │                                                                │
            agents_agent_*                                                   agents_workflow_*                                               agents_*_of_*_tests
    (agent_creator, agent_deleter,                                   (workflow_creator, workflow_deleter,                            (creator_of_unit_tests, etc.)
     agent_evaluator, agent_modifier)                                 workflow_evaluator, workflow_modifier)
```

## Deployment Status

- [x] `bootstrap.yml`
- [ ] `agents_shared.yml`
- [ ] `api_shared_runners.yml`
- [ ] `api_shared_ecs_runner.yml`
- [ ] `agents_agent_creator.yml`
- [ ] `agents_agent_deleter.yml`
- [ ] `agents_agent_evaluator.yml`
- [ ] `agents_agent_modifier.yml`
- [ ] `agents_code_reviewer_for_pre_deployment_integration_tests.yml`
- [ ] `agents_creator_of_e2e_tests.yml`
- [ ] `agents_creator_of_post_deployment_integration_tests.yml`
- [ ] `agents_creator_of_pre_deployment_integration_tests.yml`
- [ ] `agents_creator_of_unit_tests.yml`
- [ ] `agents_deleter_of_e2e_tests.yml`
- [ ] `agents_deleter_of_post_deployment_integration_tests.yml`
- [ ] `agents_deleter_of_pre_deployment_integration_tests.yml`
- [ ] `agents_deleter_of_unit_tests.yml`
- [ ] `agents_modifier_of_e2e_tests.yml`
- [ ] `agents_modifier_of_post_deployment_integration_tests.yml`
- [ ] `agents_modifier_of_pre_deployment_integration_tests.yml`
- [ ] `agents_modifier_of_unit_tests.yml`
- [ ] `agents_workflow_creator.yml`
- [ ] `agents_workflow_deleter.yml`
- [ ] `agents_workflow_evaluator.yml`
- [ ] `agents_troubleshooter_of_workflows.yml`
- [ ] `agents_workflow_modifier.yml`
- [x] `www_shared.yml`
- [x] `api_backend.yml`
- [x] `endpoint_health.yml`
- [x] `endpoint_v1_image_for_ec2_runners_post.yml`
- [x] `endpoint_v1_image_for_ec2_runners.yml`
- [ ] `endpoint_v1_ec2_runner.yml`
- [ ] `endpoint_v1_image_for_ecs_runners.yml`
- [ ] `endpoint_v1_ecs_runner.yml`
- [ ] `endpoint_v1_runners.yml`
- [ ] `endpoint_v1_echo.yml`
- [ ] `endpoint_v1_contact.yml`
- [ ] `www_index.yml`
- [ ] `endpoint_v1_rack_designer.yml`
- [ ] `endpoint_v1_simulation_soc.yml`
