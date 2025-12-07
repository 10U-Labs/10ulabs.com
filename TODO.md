# Workflow Deployment - Atomic Task List

## Workflow Dependency Graph

```
bootstrap.yml
    ↓
www_shared.yml (github_hosted)
    ↓
api.yml (github_hosted)
    ↓
health.yml (github_hosted)
    ├──→ image_for_ec2_runners_endpoint.yml (github_hosted)
    │        ↓
    │    image_for_ec2_runners_post.yml (github_hosted)
    │        ↓
    │    runners.yml (github_hosted)
    │        ↓
    │    ec2_runner.yml (github_hosted) ────────────┐
    │                                               │
    └──→ ecr.yml (github_hosted) ───────────────────┤
                                                    ↓
                            image_for_ecs_runners.yml (github_hosted)
                                                    ↓
                            ecs_runner.yml (github_hosted)
                                                    ↓
             ├──→ contact.yml (ECS on-demand)
             │        ↓
             │    www_index.yml (ECS on-demand)
             │
             ├──→ echo.yml (ECS on-demand)
             └──→ rack_designer.yml (ECS on-demand)
```

See RTL.md for simulation_soc.yml.

---

## Tasks

- [x] Task 1: Ensure bootstrap.yml runs without problems
- [x] Task 2: Ensure www_shared.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run www_shared.yml --field github_hosted=true`
- [x] Task 3: Ensure api.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run api.yml --field github_hosted=true`
- [ ] Task 4: Ensure health.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run health.yml --field github_hosted=true`
- [ ] Task 5: Ensure image_for_ec2_runners_endpoint.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run image_for_ec2_runners_endpoint.yml --field github_hosted=true`
- [ ] Task 6: Ensure image_for_ec2_runners_post.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run image_for_ec2_runners_post.yml --field github_hosted=true`
- [ ] Task 7: Ensure runners.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run runners.yml --field github_hosted=true`
- [ ] Task 8: Ensure ec2_runner.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run ec2_runner.yml --field github_hosted=true`
- [ ] Task 9: Ensure ecr.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run ecr.yml --field github_hosted=true`
- [ ] Task 10: Ensure image_for_ecs_runners.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run image_for_ecs_runners.yml --field github_hosted=true`
- [ ] Task 11: Ensure ecs_runner.yml runs without problems
  - Uses: `github_hosted=true` or `[github-hosted]`
  - Trigger: `gh workflow run ecs_runner.yml --field github_hosted=true`
- [ ] Task 12: Ensure contact.yml runs without problems
  - Uses: ECS fargate on-demand
  - Trigger: `gh workflow run contact.yml`
- [ ] Task 13: Ensure echo.yml runs without problems
  - Uses: ECS fargate on-demand
  - Trigger: `gh workflow run echo.yml`
- [ ] Task 14: Ensure rack_designer.yml runs without problems
  - Uses: ECS fargate on-demand
  - Trigger: `gh workflow run rack_designer.yml`
- [ ] Task 15: Ensure www_index.yml runs without problems
  - Uses: ECS fargate on-demand
  - Trigger: `gh workflow run www_index.yml`
- [ ] Task 16: STOP AND ASK USER for next steps

---

## Orchestrator Pattern (Implemented)

All workflows now use the Orchestrator Pattern:

1. **orchestrator.yml** is the ONLY workflow with a `push` trigger
2. It analyzes changed files and determines which root workflows to trigger
3. Root workflows cascade to descendants via `workflow_run` triggers
4. The dependency graph is defined in `etc/workflow-dependencies.yml`
5. The logic is in `scripts/compute_root_workflows.py` with tests in `test/orchestrator/`

**How it works:**
```
Push to main
    ↓
orchestrator.yml (only push trigger)
    ↓
Computes root workflows from changed files
    ↓
Dispatches root workflows (workflow_dispatch)
    ↓
Descendants cascade via workflow_run
```

**Benefits:**
- No duplicate workflow runs when multiple dependencies change in one commit
- Centralized dependency logic in `etc/workflow-dependencies.yml`
- Scales to any depth without manual pattern maintenance

---

## Notes

- Workflows up to and including ecs_runner.yml support `github_hosted=true` and `[github-hosted]`
- Workflows after ecs_runner.yml run on ECS fargate on-demand only
- Complete each task fully before starting the next
- All workflows are triggered via orchestrator.yml on push to main

---

## USE_GITHUB_HOSTED Repository Variable

Until ECS runners are operational, workflows can use GitHub-hosted runners via the `USE_GITHUB_HOSTED` repository variable.

**How it works:**
- All workflows check `vars.USE_GITHUB_HOSTED == 'true'` in addition to `github_hosted` input and `[github-hosted]` commit message
- Set: `gh variable set USE_GITHUB_HOSTED --body "true"`
- The variable cascades to all descendant workflows (no need for `[github-hosted]` in commit messages)
- Once ecs_runner.yml completes successfully, it automatically sets `USE_GITHUB_HOSTED=false`

**Usage:**
```bash
# Enable GitHub-hosted runners for all workflows
gh variable set USE_GITHUB_HOSTED --body "true"

# Disable GitHub-hosted runners (use ECS)
gh variable set USE_GITHUB_HOSTED --body "false"

# Check current value
gh variable list
```
