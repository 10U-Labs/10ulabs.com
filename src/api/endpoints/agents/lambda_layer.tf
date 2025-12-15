# Lambda Layer for GitHub App Authentication
#
# Contains PyJWT and cryptography for GitHub App token generation.
# Used by the agent webhook Lambda.

locals {
  lambda_layer_dir   = "${path.module}/.terraform/lambda_layer"
  github_auth_script = "${path.module}/lambdas/layer/build.py"
  github_auth_reqs   = "${path.module}/lambdas/layer/requirements.txt"
  github_auth_module = "${path.module}/lambdas/layer/github_auth.py"
  github_auth_zip    = "${local.lambda_layer_dir}/github_auth.zip"

  # Hash of source files for layer versioning
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
    command = "python3 ${local.github_auth_script} github_auth ${local.github_auth_reqs} ${local.github_auth_zip}"
  }
}

# GitHub Auth layer
resource "aws_lambda_layer_version" "github_auth" {
  filename                 = local.github_auth_zip
  layer_name               = "${local.resource_prefix}GithubAuthLayer"
  description              = "PyJWT and cryptography for GitHub App authentication"
  compatible_runtimes      = ["python3.13", "python3.12", "python3.11"]
  compatible_architectures = ["arm64"]

  source_code_hash = local.github_auth_content_hash

  depends_on = [null_resource.github_auth_layer_build]

  lifecycle {
    create_before_destroy = true
  }
}
