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
