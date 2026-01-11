# README

```
bootstrap
    ├──────────────────────────────────────────────────────────────────────────────────────────────────┐
    ↓                                                                                                  ↓
api_common_routing                                                                                 www_common
    ├── api_operational_health                                                                         │
    ├── api_operational_diagnostics                                                                    │
    ├── api_endpoint_v1_drift_recoveries                                                               │
    │                                                                                                  │
    ├── api_endpoint_v1_contact_submissions ───────────────────────────────────────────────────────────┼─→ www_home
    │                                                                                                  │
    ├── api_endpoint_v1_rack_configurations ─┐                                                         │
    ├── api_endpoint_v1_sessions ────────────┴─────────────────────────────────────────────────────────┼─→ www_rack_designer
    │                                                                                                  │
    ├── api_endpoint_v1_soc_simulations ───────────────────────────────────────────────────────────────┴─→ www_simulations_soc
    │
    ├── api_endpoint_v1_github_workflows_retries ─┬─→ api_endpoint_v1_ec2_spot_interruptions ─┐
    │                                             └─→ api_endpoint_v1_ecs_task_stops ─────────┼────────┐
    │                                                                                         │        │
    ├── api_common_networking                                                                 │        │
    │       └── api_endpoint_v1_runners_ec2_images ───────────────────────────────────────────┴─→ api_endpoint_v1_runners_ec2 ─┐
    │                                                                                                                           │
    └── api_common_docker_repository ─┬─→ api_endpoint_v1_runners_ecs_images ─→ api_endpoint_v1_runners_ecs ◄──────────────────┘
                                      │                                                  ↑
                                      └──────────────────────────────────────────────────┘

                                                             api_endpoint_v1_runners_cleanups ◄── runners_ec2 & runners_ecs
                                                                         │
                                                                         └─→ api_endpoint_v1_runners
                                                                                     │
                                                                                     └─→ api_endpoint_v1_github_workflows_webhooks
```
