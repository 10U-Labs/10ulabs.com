# Workflow Deployment - Atomic Task List

## Tasks

- [x] `bootstrap.yml`
- [x] `www_shared.yml`
- [x] `api_backend.yml`
- [x] `endpoint_health.yml`
- [ ] `endpoint_v1_image_for_ec2_runners.yml`
- [ ] `endpoint_v1_image_for_ec2_runners_post.yml`
- [ ] `endpoint_v1_runners.yml`
- [ ] `endpoint_v1_ec2_runner.yml`
- [ ] `api_shared_ecr.yml`
- [ ] `endpoint_v1_image_for_ecs_runners.yml`
- [ ] `endpoint_v1_ecs_runner.yml`
- [ ] `endpoint_v1_contact.yml`
- [ ] `endpoint_v1_echo.yml`
- [ ] `endpoint_v1_rack_designer.yml`
- [ ] `www_index.yml`

---

## Workflow Dependency Graph

```
bootstrap.yml
    ↓
www_shared.yml (github_hosted)
    ↓
api_backend.yml (github_hosted)
    ↓
endpoint_health.yml (github_hosted)
    ├──→ endpoint_v1_image_for_ec2_runners.yml (github_hosted)
    │        ↓
    │    endpoint_v1_image_for_ec2_runners_post.yml (github_hosted)
    │        ↓
    │    endpoint_v1_runners.yml (github_hosted)
    │        ↓
    │    endpoint_v1_ec2_runner.yml (github_hosted) ────────────┐
    │                                               │
    └──→ api_shared_ecr.yml (github_hosted) ───────────────────┤
                                                    ↓
                            endpoint_v1_image_for_ecs_runners.yml (github_hosted)
                                                    ↓
                            endpoint_v1_ecs_runner.yml (github_hosted)
                                                    ↓
             ├──→ endpoint_v1_contact.yml (ECS on-demand)
             │        ↓
             │    www_index.yml (ECS on-demand)
             │
             ├──→ endpoint_v1_echo.yml (ECS on-demand)
             └──→ endpoint_v1_rack_designer.yml (ECS on-demand)
```

See RTL.md for endpoint_v1_simulation_soc.yml.
