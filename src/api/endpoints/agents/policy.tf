# AgentCore Policy - Cedar-based deterministic rules enforcement
#
# Provides:
# - Deterministic access control (unlike probabilistic guardrails)
# - Tool-level permissions
# - Resource-level restrictions
# - Action whitelisting/blacklisting
#
# Cedar policies are evaluated BEFORE model invocation for fast, reliable enforcement

resource "aws_bedrockagentcore_agent_runtime_policy" "agents" {
  agent_runtime_arn = aws_bedrockagentcore_agent_runtime.runtime.agent_runtime_arn
  name              = "${local.resource_prefix}-agent-policy"
  description       = "Cedar policy for agent tool and resource access control"

  # Cedar policy document
  policy = <<-CEDAR
    // ===========================================================
    // 10U Labs Agent Policy - Cedar Authorization Rules
    // ===========================================================

    // Allow all agents to use GitHub tools within our organization
    permit (
      principal,
      action == Action::"tool:github:*",
      resource
    ) when {
      resource.owner == "10U-Labs-LLC"
    };

    // Allow agents to read any file in the repository
    permit (
      principal,
      action == Action::"tool:file:read",
      resource
    );

    // Allow agents to write files only in specific directories
    permit (
      principal,
      action == Action::"tool:file:write",
      resource
    ) when {
      resource.path like "src/*" ||
      resource.path like "tests/*" ||
      resource.path like ".github/*"
    };

    // Allow agents to execute bash commands (limited)
    permit (
      principal,
      action == Action::"tool:bash:execute",
      resource
    ) when {
      // Only allow safe commands
      resource.command like "git *" ||
      resource.command like "npm *" ||
      resource.command like "pytest *" ||
      resource.command like "python *" ||
      resource.command like "ls *" ||
      resource.command like "cat *"
    };

    // Deny dangerous bash commands
    forbid (
      principal,
      action == Action::"tool:bash:execute",
      resource
    ) when {
      resource.command like "rm -rf *" ||
      resource.command like "sudo *" ||
      resource.command like "curl * | bash" ||
      resource.command like "wget * | bash"
    };

    // Allow agents to create branches
    permit (
      principal,
      action == Action::"tool:github:branch:create",
      resource
    ) when {
      resource.owner == "10U-Labs-LLC" &&
      resource.branch like "agent/*"
    };

    // Allow agents to create pull requests
    permit (
      principal,
      action == Action::"tool:github:pr:create",
      resource
    ) when {
      resource.owner == "10U-Labs-LLC" &&
      resource.base == "main"
    };

    // Deny force pushes
    forbid (
      principal,
      action == Action::"tool:github:push",
      resource
    ) when {
      resource.force == true
    };

    // Deny direct pushes to main
    forbid (
      principal,
      action == Action::"tool:github:push",
      resource
    ) when {
      resource.branch == "main" ||
      resource.branch == "master"
    };

    // Allow memory operations
    permit (
      principal,
      action == Action::"memory:*",
      resource
    );

    // Allow agents to invoke other agents (for orchestration)
    permit (
      principal,
      action == Action::"agent:invoke",
      resource
    ) when {
      resource.agent_type in ["troubleshooter_of_workflows", "creator_of_agents"]
    };

    // Deny invocation of unknown agent types
    forbid (
      principal,
      action == Action::"agent:invoke",
      resource
    ) unless {
      resource.agent_type in ["troubleshooter_of_workflows", "creator_of_agents"]
    };

    // Rate limiting - deny if too many requests
    forbid (
      principal,
      action,
      resource
    ) when {
      context.request_count > 100
    };
  CEDAR

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-agent-policy"
  })
}
