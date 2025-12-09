# Import blocks for existing resources
#
# These imports bring existing AWS resources into Terraform state.
# They are one-time operations that can be removed after successful import.

import {
  to = aws_iam_role.agentcore_execution
  id = module.shared.agentcore.execution_role_name
}

import {
  to = aws_iam_role_policy.agentcore_execution
  id = "${module.shared.agentcore.execution_role_name}:AgentCoreExecutionPolicy"
}

import {
  to = aws_iam_role_policy_attachment.agentcore_managed
  id = "${module.shared.agentcore.execution_role_name}/arn:aws:iam::aws:policy/BedrockAgentCoreFullAccess"
}
