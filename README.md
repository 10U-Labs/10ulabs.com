# 10ulabs.com

## Workflow Dependency Graph

```
bootstrap.yml
    ↓
agents_test_auditor.yml
    ↓
www_shared.yml
    ↓
api_backend.yml
    ↓
endpoint_health.yml
    │
    ├──→ endpoint_v1_image_for_ec2_runners_post.yml
    │       ↓
    │    endpoint_v1_image_for_ec2_runners.yml
    │       ↓
    │    endpoint_v1_ec2_runner.yml ─────────────────────┐
    │                                                    │
    └──→ api_shared_ecr.yml                              │
            ↓                                            │
         endpoint_v1_image_for_ecs_runners.yml           │
            ↓                                            │
         endpoint_v1_ecs_runner.yml ─────────────────────┤
                                                         ↓
                              endpoint_v1_runners.yml
                                                         ↓
                              ├──→ endpoint_v1_contact.yml
                              │       ↓
                              │    www_index.yml
                              │
                              ├──→ endpoint_v1_echo.yml
                              │
                              ├──→ endpoint_v1_rack_designer.yml
                              │
                              └──→ endpoint_v1_simulation_soc.yml
```

## Execution Sequence

When the orchestrator dispatches workflows, they execute in this order:

```
01. bootstrap
02. agents_test_auditor
03. www_shared
04. api_backend
05. endpoint_health
06. endpoint_v1_image_for_ec2_runners_post  ┐
07. endpoint_v1_image_for_ec2_runners       ├── EC2 runner chain
08. endpoint_v1_ec2_runner                  ┘
09. api_shared_ecr                          ┐
10. endpoint_v1_image_for_ecs_runners       ├── ECS runner chain
11. endpoint_v1_ecs_runner                  ┘
12. endpoint_v1_runners
13. endpoint_v1_echo
14. endpoint_v1_contact
15. www_index
16. endpoint_v1_rack_designer
17. endpoint_v1_simulation_soc
```

## Deployment Status

- [x] `bootstrap.yml`
- [ ] `agents_test_auditor.yml`
- [x] `www_shared.yml`
- [x] `api_backend.yml`
- [x] `endpoint_health.yml`
- [x] `endpoint_v1_image_for_ec2_runners_post.yml`
- [x] `endpoint_v1_image_for_ec2_runners.yml`
- [ ] `endpoint_v1_ec2_runner.yml`
- [x] `api_shared_ecr.yml`
- [ ] `endpoint_v1_image_for_ecs_runners.yml`
- [ ] `endpoint_v1_ecs_runner.yml`
- [ ] `endpoint_v1_runners.yml`
- [ ] `endpoint_v1_contact.yml`
- [ ] `www_index.yml`
- [ ] `endpoint_v1_echo.yml`
- [ ] `endpoint_v1_rack_designer.yml`
- [ ] `endpoint_v1_simulation_soc.yml`
