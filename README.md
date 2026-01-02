# README

```
bootstrap
    ├──────────────────────────────────────────────────────────────────────────────────┐
    ↓                                                                                  ↓
api_common_routing                                                                 www_common
    ├── api_operational_health                                                         ├── www_home
    ├── api_operational_diagnostics                                                    └── www_rack_designer
    ├── api_endpoint_v1_contact_submissions
    ├── api_endpoint_v1_rack_configurations
    ├── api_endpoint_v1_sessions
    ├── api_endpoint_v1_soc_simulations
    │       └── www_simulations_soc
    ├── api_common_networking
    │       └── api_endpoint_v1_runners_ec2_images
    │               └── api_endpoint_v1_runners_ec2 ─┐
    └── api_common_docker_repository                 ├── api_endpoint_v1_runners
            └── api_endpoint_v1_runners_ecs_images   │       └── webhooks_github_jit_runner_requests
                    └── api_endpoint_v1_runners_ecs ─┘
```
