# Lambda Layer for Runners - Shared utilities for runner Lambda handlers
#
# Contains AWS SDK clients, GitHub PAT auth, runner label parsing, and webhook ingress handling.
# Used by webhook_router, stale_runner_cleanup, spot_interruption_handler, and drift_recovery.

locals {
  runners_layer_dir        = "${path.module}/.terraform/lambda_layer"
  runners_layer_source_dir = "${path.module}/lambdas/layer"
  runners_layer_zip        = "${local.runners_layer_dir}/runners_layer.zip"
  etc_dir                  = "${path.module}/../../../../etc"

  # Hash of source files for layer versioning
  runners_layer_content_hash = base64sha256(join("", [
    file("${local.runners_layer_source_dir}/package.json"),
    file("${local.runners_layer_source_dir}/index.js"),
    file("${local.runners_layer_source_dir}/github_pat_auth.js"),
    file("${local.runners_layer_source_dir}/aws_clients.js"),
    file("${local.runners_layer_source_dir}/runner_labels.js"),
    file("${local.runners_layer_source_dir}/webhook_ingress.js"),
    file("${local.etc_dir}/runners.json"),
  ]))
}

# Build the runners layer zip
resource "null_resource" "runners_layer_build" {
  triggers = {
    content_hash = local.runners_layer_content_hash
    output_path  = local.runners_layer_zip
  }

  provisioner "local-exec" {
    command = <<-EOT
      rm -rf ${local.runners_layer_dir}/nodejs
      mkdir -p ${local.runners_layer_dir}/nodejs/runners-layer/etc
      cp ${local.runners_layer_source_dir}/package.json \
         ${local.runners_layer_source_dir}/index.js \
         ${local.runners_layer_source_dir}/github_pat_auth.js \
         ${local.runners_layer_source_dir}/aws_clients.js \
         ${local.runners_layer_source_dir}/runner_labels.js \
         ${local.runners_layer_source_dir}/webhook_ingress.js \
         ${local.runners_layer_dir}/nodejs/runners-layer/
      cp ${local.etc_dir}/runners.json ${local.runners_layer_dir}/nodejs/runners-layer/etc/
      (cd ${local.runners_layer_dir}/nodejs/runners-layer && npm install --omit=dev)
      (cd ${local.runners_layer_dir} && zip -r runners_layer.zip nodejs)
    EOT
  }
}

# Runners layer
resource "aws_lambda_layer_version" "runners_layer" {
  filename                 = local.runners_layer_zip
  layer_name               = "${local.resource_prefix}RunnersLayer"
  description              = "Node.js utilities for runner Lambda handlers - PAT auth, AWS clients, label parsing"
  compatible_runtimes      = ["nodejs22.x", "nodejs20.x"]
  compatible_architectures = ["arm64"]

  source_code_hash = local.runners_layer_content_hash

  depends_on = [null_resource.runners_layer_build]

  lifecycle {
    create_before_destroy = true
  }
}
