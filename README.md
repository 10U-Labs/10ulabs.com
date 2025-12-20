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
```

## Deployment Status

- [x] `api_backend.yml`
- [x] `api_shared_ecs_runner.yml`
- [x] `api_shared_runners.yml`
- [x] `bootstrap.yml`
- [x] `operational_health.yml`
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
