locals {
  # Common values from shared module
  aws_region      = module.shared.aws_region
  aws_account_id  = module.shared.aws_account_id
  resource_prefix = module.shared.resource_prefix
  github_org      = module.shared.github_org
  github_repo     = module.shared.name_for_github_repo

  agent_name     = "${local.resource_prefix}TestAuditorAgent"
  image_tag      = "test_auditor-latest"
  lambda_name    = "${local.resource_prefix}TestAuditorActionGroup"
  log_group_name = "/aws/lambda/${local.lambda_name}"

  # SSM parameters
  ssm_github_pat     = module.shared.ssm_github_pat_name
  ssm_github_pat_arn = module.shared.ssm_github_pat_arn

  common_tags = {
    Project     = "10ulabs"
    Environment = "production"
    ManagedBy   = "terraform"
    Component   = "agents"
    Agent       = "test_auditor"
  }

  agent_instruction = <<-EOT
    You are a Test Auditor Agent for the 10ulabs.com repository. Your purpose is to
    ensure that all pre-deployment integration tests follow the documented five-layer
    testing approach.

    When triggered, you will:
    1. Read the documented testing approach from docs/APPROACH_TO_PRE_DEPLOYMENT_INTEGRATION_TESTS.md
    2. Find all pre-deployment integration test directories
    3. Analyze each test file's terraform data.tf to identify actual dependencies
    4. Verify tests follow the five-layer model: Authentication, Authorization, Existence, Configuration, Capability
    5. Create pull requests to fix any tests that don't comply

    The five layers must be tested in order:
    - Layer 1 (Authentication): Verify AWS credentials exist and are valid
    - Layer 2 (Authorization): Verify permission to call APIs (e.g., HeadBucket)
    - Layer 3 (Existence): Verify resources exist
    - Layer 4 (Configuration): Verify resources are configured correctly
    - Layer 5 (Capability): Verify we can perform required operations

    Always identify the ACTUAL terraform dependencies from data.tf, not assumed dependencies.
    Tests must fail fast with precise diagnostic messages.
  EOT
}
