# Lambda Layer for GitHub App Authentication and Agent Utilities
#
# Contains jsonwebtoken and Bedrock Agent Runtime SDK for GitHub App token generation
# and agent invocation. Used by agent Lambda handlers.

locals {
  lambda_layer_dir        = "${path.module}/.terraform/lambda_layer"
  agents_layer_source_dir = "${path.module}/lambdas/layer"
  agents_layer_zip        = "${local.lambda_layer_dir}/agents_layer.zip"

  # Hash of source files for layer versioning
  agents_layer_content_hash = base64sha256(join("", [
    file("${local.agents_layer_source_dir}/package.json"),
    file("${local.agents_layer_source_dir}/index.js"),
    file("${local.agents_layer_source_dir}/github_app_auth.js"),
    file("${local.agents_layer_source_dir}/agent_utils.js"),
  ]))
}

# Build the agents layer zip
resource "null_resource" "agents_layer_build" {
  triggers = {
    content_hash = local.agents_layer_content_hash
    output_path  = local.agents_layer_zip
  }

  provisioner "local-exec" {
    working_dir = local.agents_layer_source_dir
    command     = <<-EOT
      rm -rf ${local.lambda_layer_dir}/nodejs
      mkdir -p ${local.lambda_layer_dir}/nodejs/agents-layer
      cp package.json index.js github_app_auth.js agent_utils.js ${local.lambda_layer_dir}/nodejs/agents-layer/
      cd ${local.lambda_layer_dir}/nodejs/agents-layer && npm install --production
      cd ${local.lambda_layer_dir} && zip -r ${local.agents_layer_zip} nodejs
    EOT
  }
}

# Agents layer
resource "aws_lambda_layer_version" "github_auth" {
  filename                 = local.agents_layer_zip
  layer_name               = "${local.resource_prefix}AgentsLayer"
  description              = "Node.js utilities for GitHub App authentication and agent invocation"
  compatible_runtimes      = ["nodejs22.x", "nodejs20.x"]
  compatible_architectures = ["arm64"]

  source_code_hash = local.agents_layer_content_hash

  depends_on = [null_resource.agents_layer_build]

  lifecycle {
    create_before_destroy = true
  }
}
