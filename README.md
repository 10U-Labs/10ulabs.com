# README

```
bootstrap
    ├──────────────────────────────────────────────────────────────────────────────────────────────────┐
    ↓                                                                                                  ↓
api_common_routing                                                                                 www_common
    ├── api_operational_health                                                                         │
    ├── api_operational_diagnostics                                                                    │
    │                                                                                                  │
    ├── api_endpoint_v1_contact_submissions ───────────────────────────────────────────────────────────┼─→ www_home
    │                                                                                                  │
    ├── api_endpoint_v1_rack_configurations ─┐                                                         │
    ├── api_endpoint_v1_sessions ────────────┴─────────────────────────────────────────────────────────┼─→ www_rack_designer
    │                                                                                                  │
    ├── api_endpoint_v1_soc_simulations ───────────────────────────────────────────────────────────────┴─→ www_simulations_soc
    │
    ├── api_common_networking
    │       └── api_endpoint_v1_runners_ec2_images
    │               └── api_endpoint_v1_runners_ec2 ─┬─────────────────────────────────────┐
    │                                                │                                     ↓
    └── api_common_docker_repository ────────────────┴─→ api_endpoint_v1_runners_ecs_images
                                                                └── api_endpoint_v1_runners_ecs ─┐
                                                                                                 │
                                       api_endpoint_v1_runners_ec2 ──────────────────────────────┴─→ api_endpoint_v1_runners
                                                                                                         └── webhooks_github_jit_runner_requests
```
