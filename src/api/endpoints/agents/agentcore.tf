# AgentCore Runtime - Single runtime for all agents (Direct Code Deploy)
#
# Agents are differentiated by the prompt passed at invocation time.
# The runtime loads prompts from S3 dynamically.
#
# Architecture:
# - Direct code deployment (no Docker/ECR)
# - Prompts in S3 (decoupled from runtime)
# - Guardrails for safety
# - Memory for context persistence
# - Cedar policies for access control

# Archive the runtime code for deployment
data "archive_file" "runtime" {
  type        = "zip"
  source_dir  = "${path.module}/runtime"
  output_path = "${path.module}/.terraform/runtime.zip"

  excludes = [
    "__pycache__",
    "*.pyc",
    ".pytest_cache",
    "prompts",
  ]
}

resource "aws_bedrockagentcore_agent_runtime" "runtime" {
  agent_runtime_name = replace(local.stack_name, "-", "_")
  description        = "Unified agent runtime - loads prompts from S3, direct code deploy"
  role_arn           = aws_iam_role.agentcore_execution.arn

  # Direct code deployment (no container)
  agent_runtime_artifact {
    code_configuration {
      s3_location {
        bucket = aws_s3_bucket.runtime_code.id
        key    = aws_s3_object.runtime_code.key
      }
      runtime          = "python3.12"
      handler          = "main.invoke"
      requirements_txt = file("${path.module}/runtime/requirements.txt")
    }
  }

  network_configuration {
    network_mode = "PUBLIC"
  }

  # Guardrail integration
  guardrail_configuration {
    guardrail_id      = aws_bedrock_guardrail.agents.guardrail_id
    guardrail_version = aws_bedrock_guardrail_version.agents.version
  }

  environment_variables = {
    AWS_REGION         = local.aws_region
    AWS_DEFAULT_REGION = local.aws_region
    PROMPTS_BUCKET     = aws_s3_bucket.prompts.id
    GUARDRAIL_ID       = aws_bedrock_guardrail.agents.guardrail_id
    GUARDRAIL_VERSION  = aws_bedrock_guardrail_version.agents.version
    MEMORY_ARN         = aws_bedrockagentcore_memory.agents.arn
  }

  tags = merge(local.common_tags, {
    Name = local.stack_name
  })

  depends_on = [
    aws_iam_role_policy.agentcore_execution,
    aws_iam_role_policy_attachment.agentcore_managed,
    aws_iam_role_policy.agentcore_guardrails,
    aws_iam_role_policy.agentcore_memory,
    aws_iam_role_policy.agentcore_s3,
    aws_s3_object.runtime_code,
  ]
}

# S3 bucket for runtime code deployment
resource "aws_s3_bucket" "runtime_code" {
  bucket = "${local.resource_prefix}-agent-runtime-code"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-agent-runtime-code"
  })
}

resource "aws_s3_bucket_versioning" "runtime_code" {
  bucket = aws_s3_bucket.runtime_code.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "runtime_code" {
  bucket = aws_s3_bucket.runtime_code.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "runtime_code" {
  bucket = aws_s3_bucket.runtime_code.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Upload runtime code to S3
resource "aws_s3_object" "runtime_code" {
  bucket       = aws_s3_bucket.runtime_code.id
  key          = "runtime/${data.archive_file.runtime.output_md5}.zip"
  source       = data.archive_file.runtime.output_path
  etag         = data.archive_file.runtime.output_md5
  content_type = "application/zip"

  tags = local.common_tags
}
