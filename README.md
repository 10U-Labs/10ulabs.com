# 10ulabs.com

## Workflow Dependency Graph

```
bootstrap
    │
    └── www_shared
            │
            └── api_backend
                    │
                    └── endpoint_health
                            │
                            ├── api_shared_runners ─────────────────────────────────┐
                            │       │                                                │
                            │       └── endpoint_v1_image_for_ec2_runners            │
                            │               │                                        │
                            │               └── endpoint_v1_ec2_runner ──────────────┤
                            │                                                        │
                            └── api_shared_ecs_runner ───────────────────────────────┤
                                                                                     │
                                                        endpoint_v1_image_for_ecs_runners
                                                                     │
                                                        endpoint_v1_ecs_runner ──────┤
                                                                                     │
                                                                          endpoint_v1_runners
                                                                                     │
                              ┌──────────────────────────┬───────────────────────────┼───────────────────────────┐
                              │                          │                           │                           │
                      endpoint_v1_echo          endpoint_v1_contact      endpoint_v1_rack_designer      endpoint_v1_simulation_soc
                                                         │
                                                    www_index
                                                                                     │
                                                                        endpoint_v1_agents_shared
                                                                                     │
                                                              endpoint_v1_agents_troubleshooter_of_workflows
                                                                                     │
                    ┌────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────┐
                    │                                                                │                                                                │
    endpoint_v1_agents_*_of_agents                            endpoint_v1_agents_*_of_workflows                            endpoint_v1_agents_*_of_*_tests
    (creator_of_agents, deleter_of_agents,                    (creator_of_workflows, deleter_of_workflows,                 (creator_of_unit_tests, etc.)
     evaluator_of_agents, modifier_of_agents)                  evaluator_of_workflows, modifier_of_workflows)
```

## Deployment Status

- [x] `bootstrap.yml`
- [ ] `endpoint_v1_agents_shared.yml`
- [x] `api_shared_runners.yml`
- [x] `api_shared_ecs_runner.yml`
- [ ] `endpoint_v1_agents_creator_of_agents.yml`
- [ ] `endpoint_v1_agents_deleter_of_agents.yml`
- [ ] `endpoint_v1_agents_evaluator_of_agents.yml`
- [ ] `endpoint_v1_agents_modifier_of_agents.yml`
- [ ] `endpoint_v1_agents_code_reviewer_of_pre_deployment_integration_tests.yml`
- [ ] `endpoint_v1_agents_creator_of_e2e_tests.yml`
- [ ] `endpoint_v1_agents_creator_of_post_deployment_integration_tests.yml`
- [ ] `endpoint_v1_agents_creator_of_pre_deployment_integration_tests.yml`
- [ ] `endpoint_v1_agents_creator_of_unit_tests.yml`
- [ ] `endpoint_v1_agents_deleter_of_e2e_tests.yml`
- [ ] `endpoint_v1_agents_deleter_of_post_deployment_integration_tests.yml`
- [ ] `endpoint_v1_agents_deleter_of_pre_deployment_integration_tests.yml`
- [ ] `endpoint_v1_agents_deleter_of_unit_tests.yml`
- [ ] `endpoint_v1_agents_modifier_of_e2e_tests.yml`
- [ ] `endpoint_v1_agents_modifier_of_post_deployment_integration_tests.yml`
- [ ] `endpoint_v1_agents_modifier_of_pre_deployment_integration_tests.yml`
- [ ] `endpoint_v1_agents_modifier_of_unit_tests.yml`
- [ ] `endpoint_v1_agents_creator_of_workflows.yml`
- [ ] `endpoint_v1_agents_deleter_of_workflows.yml`
- [ ] `endpoint_v1_agents_evaluator_of_workflows.yml`
- [ ] `endpoint_v1_agents_troubleshooter_of_workflows.yml`
- [ ] `endpoint_v1_agents_modifier_of_workflows.yml`
- [x] `www_shared.yml`
- [x] `api_backend.yml`
- [x] `endpoint_health.yml`
- [x] `endpoint_v1_image_for_ec2_runners_post.yml`
- [x] `endpoint_v1_image_for_ec2_runners.yml`
- [x] `endpoint_v1_ec2_runner.yml`
- [x] `endpoint_v1_image_for_ecs_runners_post.yml`
- [x] `endpoint_v1_image_for_ecs_runners.yml`
- [x] `endpoint_v1_ecs_runner.yml`
- [x] `endpoint_v1_runners.yml`
- [x] `endpoint_v1_echo.yml`
- [x] `endpoint_v1_contact.yml`
- [x] `www_index.yml`
- [x] `endpoint_v1_rack_designer.yml`
- [x] `endpoint_v1_simulation_soc.yml`
