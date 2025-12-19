# Lambda Layers for Runners - Per-client AWS SDK layers and common utilities
#
# 5 layers total (Lambda limit is 5 per function):
# - clients/ecs: ECS client for task management
# - clients/ec2: EC2 client for instance management
# - clients/cloudwatch: CloudWatch client for metrics
# - clients/ssm: SSM client for parameter store
# - common: GitHub PAT auth, runner labels, webhook ingress

locals {
  layers_base_dir  = "${path.module}/lambdas/layers"
  layers_build_dir = "${path.module}/.terraform/lambda_layers"
  etc_dir          = "${path.module}/../../../../etc"

  # Client layer source directories
  ecs_layer_source        = "${local.layers_base_dir}/clients/ecs"
  ec2_layer_source        = "${local.layers_base_dir}/clients/ec2"
  cloudwatch_layer_source = "${local.layers_base_dir}/clients/cloudwatch"
  ssm_layer_source        = "${local.layers_base_dir}/clients/ssm"
  common_layer_source     = "${local.layers_base_dir}/common"

  # Content hashes for layer versioning
  ecs_layer_hash        = base64sha256(file("${local.ecs_layer_source}/index.js"))
  ec2_layer_hash        = base64sha256(file("${local.ec2_layer_source}/index.js"))
  cloudwatch_layer_hash = base64sha256(file("${local.cloudwatch_layer_source}/index.js"))
  ssm_layer_hash        = base64sha256(file("${local.ssm_layer_source}/index.js"))
  common_layer_hash = base64sha256(join("", [
    file("${local.common_layer_source}/package.json"),
    file("${local.common_layer_source}/index.js"),
    file("${local.common_layer_source}/github_pat_auth.js"),
    file("${local.common_layer_source}/runner_labels.js"),
    file("${local.common_layer_source}/webhook_ingress.js"),
    file("${local.etc_dir}/runners.json"),
  ]))
}

# =============================================================================
# ECS Client Layer
# =============================================================================
resource "null_resource" "ecs_layer_build" {
  triggers = {
    content_hash = local.ecs_layer_hash
    output_path  = "${local.layers_build_dir}/ecs_layer.zip"
  }

  provisioner "local-exec" {
    command = <<-EOT
      rm -rf ${local.layers_build_dir}/ecs
      mkdir -p ${local.layers_build_dir}/ecs/nodejs/clients/ecs
      cp ${local.ecs_layer_source}/index.js ${local.layers_build_dir}/ecs/nodejs/clients/ecs/
      cat > ${local.layers_build_dir}/ecs/nodejs/clients/ecs/package.json << 'EOF'
{"name":"ecs-client","version":"1.0.0","dependencies":{"@aws-sdk/client-ecs":"^3.0.0"}}
EOF
      (cd ${local.layers_build_dir}/ecs/nodejs/clients/ecs && npm install --omit=dev --silent)
      (cd ${local.layers_build_dir}/ecs && zip -rq ../ecs_layer.zip nodejs)
    EOT
  }
}

resource "aws_lambda_layer_version" "ecs_client" {
  filename                 = "${local.layers_build_dir}/ecs_layer.zip"
  layer_name               = "${local.resource_prefix}EcsClientLayer"
  description              = "AWS ECS client for Lambda handlers"
  compatible_runtimes      = ["nodejs22.x", "nodejs20.x"]
  compatible_architectures = ["arm64"]
  source_code_hash         = local.ecs_layer_hash

  depends_on = [null_resource.ecs_layer_build]

  lifecycle {
    create_before_destroy = true
  }
}

# =============================================================================
# EC2 Client Layer
# =============================================================================
resource "null_resource" "ec2_layer_build" {
  triggers = {
    content_hash = local.ec2_layer_hash
    output_path  = "${local.layers_build_dir}/ec2_layer.zip"
  }

  provisioner "local-exec" {
    command = <<-EOT
      rm -rf ${local.layers_build_dir}/ec2
      mkdir -p ${local.layers_build_dir}/ec2/nodejs/clients/ec2
      cp ${local.ec2_layer_source}/index.js ${local.layers_build_dir}/ec2/nodejs/clients/ec2/
      cat > ${local.layers_build_dir}/ec2/nodejs/clients/ec2/package.json << 'EOF'
{"name":"ec2-client","version":"1.0.0","dependencies":{"@aws-sdk/client-ec2":"^3.0.0"}}
EOF
      (cd ${local.layers_build_dir}/ec2/nodejs/clients/ec2 && npm install --omit=dev --silent)
      (cd ${local.layers_build_dir}/ec2 && zip -rq ../ec2_layer.zip nodejs)
    EOT
  }
}

resource "aws_lambda_layer_version" "ec2_client" {
  filename                 = "${local.layers_build_dir}/ec2_layer.zip"
  layer_name               = "${local.resource_prefix}Ec2ClientLayer"
  description              = "AWS EC2 client for Lambda handlers"
  compatible_runtimes      = ["nodejs22.x", "nodejs20.x"]
  compatible_architectures = ["arm64"]
  source_code_hash         = local.ec2_layer_hash

  depends_on = [null_resource.ec2_layer_build]

  lifecycle {
    create_before_destroy = true
  }
}

# =============================================================================
# CloudWatch Client Layer
# =============================================================================
resource "null_resource" "cloudwatch_layer_build" {
  triggers = {
    content_hash = local.cloudwatch_layer_hash
    output_path  = "${local.layers_build_dir}/cloudwatch_layer.zip"
  }

  provisioner "local-exec" {
    command = <<-EOT
      rm -rf ${local.layers_build_dir}/cloudwatch
      mkdir -p ${local.layers_build_dir}/cloudwatch/nodejs/clients/cloudwatch
      cp ${local.cloudwatch_layer_source}/index.js ${local.layers_build_dir}/cloudwatch/nodejs/clients/cloudwatch/
      cat > ${local.layers_build_dir}/cloudwatch/nodejs/clients/cloudwatch/package.json << 'EOF'
{"name":"cloudwatch-client","version":"1.0.0","dependencies":{"@aws-sdk/client-cloudwatch":"^3.0.0"}}
EOF
      (cd ${local.layers_build_dir}/cloudwatch/nodejs/clients/cloudwatch && npm install --omit=dev --silent)
      (cd ${local.layers_build_dir}/cloudwatch && zip -rq ../cloudwatch_layer.zip nodejs)
    EOT
  }
}

resource "aws_lambda_layer_version" "cloudwatch_client" {
  filename                 = "${local.layers_build_dir}/cloudwatch_layer.zip"
  layer_name               = "${local.resource_prefix}CloudWatchClientLayer"
  description              = "AWS CloudWatch client for Lambda handlers"
  compatible_runtimes      = ["nodejs22.x", "nodejs20.x"]
  compatible_architectures = ["arm64"]
  source_code_hash         = local.cloudwatch_layer_hash

  depends_on = [null_resource.cloudwatch_layer_build]

  lifecycle {
    create_before_destroy = true
  }
}

# =============================================================================
# SSM Client Layer
# =============================================================================
resource "null_resource" "ssm_layer_build" {
  triggers = {
    content_hash = local.ssm_layer_hash
    output_path  = "${local.layers_build_dir}/ssm_layer.zip"
  }

  provisioner "local-exec" {
    command = <<-EOT
      rm -rf ${local.layers_build_dir}/ssm
      mkdir -p ${local.layers_build_dir}/ssm/nodejs/clients/ssm
      cp ${local.ssm_layer_source}/index.js ${local.layers_build_dir}/ssm/nodejs/clients/ssm/
      cat > ${local.layers_build_dir}/ssm/nodejs/clients/ssm/package.json << 'EOF'
{"name":"ssm-client","version":"1.0.0","dependencies":{"@aws-sdk/client-ssm":"^3.0.0"}}
EOF
      (cd ${local.layers_build_dir}/ssm/nodejs/clients/ssm && npm install --omit=dev --silent)
      (cd ${local.layers_build_dir}/ssm && zip -rq ../ssm_layer.zip nodejs)
    EOT
  }
}

resource "aws_lambda_layer_version" "ssm_client" {
  filename                 = "${local.layers_build_dir}/ssm_layer.zip"
  layer_name               = "${local.resource_prefix}SsmClientLayer"
  description              = "AWS SSM client for Lambda handlers"
  compatible_runtimes      = ["nodejs22.x", "nodejs20.x"]
  compatible_architectures = ["arm64"]
  source_code_hash         = local.ssm_layer_hash

  depends_on = [null_resource.ssm_layer_build]

  lifecycle {
    create_before_destroy = true
  }
}

# =============================================================================
# Common Layer (GitHub PAT, runner labels, webhook ingress)
# =============================================================================
resource "null_resource" "common_layer_build" {
  triggers = {
    content_hash = local.common_layer_hash
    output_path  = "${local.layers_build_dir}/common_layer.zip"
  }

  provisioner "local-exec" {
    command = <<-EOT
      rm -rf ${local.layers_build_dir}/common
      mkdir -p ${local.layers_build_dir}/common/nodejs/common/etc
      cp ${local.common_layer_source}/package.json \
         ${local.common_layer_source}/index.js \
         ${local.common_layer_source}/github_pat_auth.js \
         ${local.common_layer_source}/runner_labels.js \
         ${local.common_layer_source}/webhook_ingress.js \
         ${local.layers_build_dir}/common/nodejs/common/
      cp ${local.etc_dir}/runners.json ${local.layers_build_dir}/common/nodejs/common/etc/
      (cd ${local.layers_build_dir}/common/nodejs/common && npm install --omit=dev --silent)
      (cd ${local.layers_build_dir}/common && zip -rq ../common_layer.zip nodejs)
    EOT
  }
}

resource "aws_lambda_layer_version" "common" {
  filename                 = "${local.layers_build_dir}/common_layer.zip"
  layer_name               = "${local.resource_prefix}CommonLayer"
  description              = "Common utilities - GitHub PAT auth, runner labels, webhook ingress"
  compatible_runtimes      = ["nodejs22.x", "nodejs20.x"]
  compatible_architectures = ["arm64"]
  source_code_hash         = local.common_layer_hash

  depends_on = [null_resource.common_layer_build]

  lifecycle {
    create_before_destroy = true
  }
}
