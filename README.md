# 10ulabs.com

## Workflow Dependency Graph

```
bootstrap.yml
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
02. www_shared
03. api_backend
04. endpoint_health
05. endpoint_v1_image_for_ec2_runners_post  ┐
06. endpoint_v1_image_for_ec2_runners       ├── EC2 runner chain
07. endpoint_v1_ec2_runner                  ┘
08. api_shared_ecr                          ┐
09. endpoint_v1_image_for_ecs_runners       ├── ECS runner chain
10. endpoint_v1_ecs_runner                  ┘
11. endpoint_v1_runners
12. endpoint_v1_echo
13. endpoint_v1_contact
14. www_index
15. endpoint_v1_rack_designer
16. endpoint_v1_simulation_soc
```

## Deployment Status

- [x] `bootstrap.yml`
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
