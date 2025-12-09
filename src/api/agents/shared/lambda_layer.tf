# Shared Lambda Layer for Agent Webhooks
#
# This layer contains PyJWT and cryptography for GitHub App authentication.
# Used by all agent Lambda webhook handlers.

locals {
  lambda_layer_dir   = "${path.module}/.terraform/lambda_layer"
  github_auth_script = "${path.module}/lambda_layer/build.sh"
  github_auth_reqs   = "${path.module}/lambda_layer/requirements.txt"
  github_auth_module = "${path.module}/lambda_layer/github_auth.py"
  github_auth_zip    = "${local.lambda_layer_dir}/github_auth.zip"

  # Hash of source files - used for layer versioning and computed during plan
  # (the actual zip doesn't exist until apply, but source files do)
  github_auth_content_hash = base64sha256(join("", [
    file(local.github_auth_reqs),
    file(local.github_auth_module),
    file(local.github_auth_script),
  ]))
}

# Build the GitHub Auth layer zip
resource "null_resource" "github_auth_layer_build" {
  triggers = {
    content_hash = local.github_auth_content_hash
    output_path  = local.github_auth_zip
  }

  provisioner "local-exec" {
    command = "${local.github_auth_script} github_auth ${local.github_auth_reqs} ${local.github_auth_zip}"
  }
}

# GitHub Auth layer - contains PyJWT and cryptography for GitHub App authentication
resource "aws_lambda_layer_version" "github_auth" {
  filename            = local.github_auth_zip
  layer_name          = "${local.resource_prefix}GithubAuthLayer"
  description         = "PyJWT and cryptography for GitHub App authentication"
  compatible_runtimes = ["python3.13", "python3.12", "python3.11"]

  # Use source file hash so plan works before zip exists
  source_code_hash = local.github_auth_content_hash

  depends_on = [null_resource.github_auth_layer_build]

  lifecycle {
    create_before_destroy = true
  }
}
