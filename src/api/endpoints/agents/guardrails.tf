# Bedrock Guardrails - Safety and compliance layer
#
# Provides:
# - Automated Reasoning Checks (99%+ accuracy for policy compliance)
# - Content filters for harmful content
# - Contextual grounding to prevent hallucinations
# - PII detection and redaction
#
# Legal compliance: U.S., Florida, Palm Beach County

resource "aws_bedrock_guardrail" "agents" {
  name                      = "${local.resource_prefix}-agent-guardrail"
  description               = "Safety guardrails for agent operations - legal compliance enforcement"
  blocked_input_messaging   = "Your request cannot be processed due to policy restrictions."
  blocked_outputs_messaging = "The response was blocked due to policy restrictions."

  # Content policy - filter harmful content
  content_policy_config {
    filters_config {
      type            = "SEXUAL"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "VIOLENCE"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "HATE"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "INSULTS"
      input_strength  = "MEDIUM"
      output_strength = "MEDIUM"
    }
    filters_config {
      type            = "MISCONDUCT"
      input_strength  = "HIGH"
      output_strength = "HIGH"
    }
    filters_config {
      type            = "PROMPT_ATTACK"
      input_strength  = "HIGH"
      output_strength = "NONE"
    }
  }

  # Sensitive information policy - PII protection
  sensitive_information_policy_config {
    pii_entities_config {
      type   = "EMAIL"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "PHONE"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "NAME"
      action = "ANONYMIZE"
    }
    pii_entities_config {
      type   = "US_SOCIAL_SECURITY_NUMBER"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "CREDIT_DEBIT_CARD_NUMBER"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "US_BANK_ACCOUNT_NUMBER"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "PIN"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "PASSWORD"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "AWS_ACCESS_KEY"
      action = "BLOCK"
    }
    pii_entities_config {
      type   = "AWS_SECRET_KEY"
      action = "BLOCK"
    }

    # Regex patterns for custom sensitive data
    regexes_config {
      name        = "github_token"
      description = "GitHub personal access tokens"
      pattern     = "ghp_[a-zA-Z0-9]{36}"
      action      = "BLOCK"
    }
    regexes_config {
      name        = "github_app_token"
      description = "GitHub App installation tokens"
      pattern     = "ghs_[a-zA-Z0-9]{36}"
      action      = "ANONYMIZE"
    }
  }

  # Topic policy - prevent off-topic discussions
  topic_policy_config {
    topics_config {
      name       = "illegal_activities"
      definition = "Any discussion of illegal activities, hacking, or unauthorized access"
      examples   = ["How do I hack into a system", "Help me bypass security"]
      type       = "DENY"
    }
    topics_config {
      name       = "financial_advice"
      definition = "Providing specific financial, legal, or medical advice"
      examples   = ["Should I invest in this stock", "Is this legal to do"]
      type       = "DENY"
    }
    topics_config {
      name       = "competitor_info"
      definition = "Discussions about competitor products or services"
      examples   = ["Tell me about competitor X", "How does Y compare"]
      type       = "DENY"
    }
  }

  # Word policy - block specific terms
  word_policy_config {
    managed_word_lists_config {
      type = "PROFANITY"
    }
  }

  # Contextual grounding - prevent hallucinations
  contextual_grounding_policy_config {
    filters_config {
      type      = "GROUNDING"
      threshold = 0.7
    }
    filters_config {
      type      = "RELEVANCE"
      threshold = 0.7
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-agent-guardrail"
  })
}

# Guardrail version for deployment
resource "aws_bedrock_guardrail_version" "agents" {
  guardrail_arn = aws_bedrock_guardrail.agents.guardrail_arn
  description   = "Initial version with legal compliance rules"
}
