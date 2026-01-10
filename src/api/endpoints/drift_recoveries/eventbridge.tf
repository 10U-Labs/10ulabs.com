resource "aws_cloudwatch_event_rule" "config_compliance_change" {
  name        = "${local.resource_prefix}-config-compliance-change"
  description = "Triggers on AWS Config compliance changes for infrastructure drift detection"

  event_pattern = jsonencode({
    source      = ["aws.config"]
    detail-type = ["Config Rules Compliance Change"]
    detail = {
      configRuleName = [aws_config_config_rule.required_tags.name]
      newEvaluationResult = {
        complianceType = ["NON_COMPLIANT"]
      }
    }
  })

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-config-compliance-change"
  })
}

resource "aws_cloudwatch_event_target" "drift_recovery" {
  rule      = aws_cloudwatch_event_rule.config_compliance_change.name
  target_id = "drift-recovery-sqs"
  arn       = aws_sqs_queue.handler.arn

  sqs_target {
    message_group_id = "drift-recovery"
  }

  input_transformer {
    input_paths = {
      configRuleName = "$.detail.configRuleName"
      resourceType   = "$.detail.resourceType"
      resourceId     = "$.detail.resourceId"
      awsRegion      = "$.detail.awsRegion"
    }
    input_template = <<EOF
{
  "source": "drift-recovery-trigger",
  "configRuleName": <configRuleName>,
  "resourceType": <resourceType>,
  "resourceId": <resourceId>,
  "awsRegion": <awsRegion>
}
EOF
  }
}
