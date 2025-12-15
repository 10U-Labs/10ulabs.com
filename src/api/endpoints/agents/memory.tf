# AgentCore Memory - Context persistence across agent sessions
#
# Provides:
# - Session memory: Short-term context within a conversation
# - Semantic memory: Long-term knowledge with vector search
# - Reduces token costs by avoiding repeated context

resource "aws_bedrockagentcore_memory" "agents" {
  name        = "${local.resource_prefix}-agent-memory"
  description = "Shared memory store for all agents - persists context across sessions"

  # Memory configuration
  memory_configuration {
    # Session memory for conversation context
    session_memory_configuration {
      max_session_ttl_seconds = 86400 # 24 hours
    }

    # Semantic memory for long-term knowledge
    semantic_memory_configuration {
      enabled = true
      embedding_model_configuration {
        bedrock_embedding_model_configuration {
          model_arn  = "arn:aws:bedrock:${local.aws_region}::foundation-model/amazon.titan-embed-text-v2:0"
          dimensions = 1024
        }
      }
      storage_configuration {
        # Use OpenSearch Serverless for vector storage
        opensearch_serverless_configuration {
          collection_arn = aws_opensearchserverless_collection.memory.arn
          field_mapping {
            vector_field   = "embedding"
            text_field     = "content"
            metadata_field = "metadata"
          }
        }
      }
    }
  }

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-agent-memory"
  })

  depends_on = [
    aws_opensearchserverless_collection.memory,
  ]
}

# OpenSearch Serverless collection for semantic memory vectors
resource "aws_opensearchserverless_collection" "memory" {
  name = "${local.resource_prefix}-memory"
  type = "VECTORSEARCH"

  tags = merge(local.common_tags, {
    Name = "${local.resource_prefix}-memory"
  })

  depends_on = [
    aws_opensearchserverless_security_policy.memory_encryption,
    aws_opensearchserverless_security_policy.memory_network,
    aws_opensearchserverless_access_policy.memory,
  ]
}

# Encryption policy for OpenSearch Serverless
resource "aws_opensearchserverless_security_policy" "memory_encryption" {
  name = "${local.resource_prefix}-memory-enc"
  type = "encryption"

  policy = jsonencode({
    Rules = [{
      ResourceType = "collection"
      Resource     = ["collection/${local.resource_prefix}-memory"]
    }]
    AWSOwnedKey = true
  })
}

# Network policy for OpenSearch Serverless
resource "aws_opensearchserverless_security_policy" "memory_network" {
  name = "${local.resource_prefix}-memory-net"
  type = "network"

  policy = jsonencode([{
    Rules = [{
      ResourceType = "collection"
      Resource     = ["collection/${local.resource_prefix}-memory"]
    }]
    AllowFromPublic    = false
    SourceVPCEndpoints = []
    # Allow access from AWS services only
  }])
}

# Access policy for OpenSearch Serverless
resource "aws_opensearchserverless_access_policy" "memory" {
  name = "${local.resource_prefix}-memory"
  type = "data"

  policy = jsonencode([{
    Rules = [
      {
        ResourceType = "index"
        Resource     = ["index/${local.resource_prefix}-memory/*"]
        Permission   = ["aoss:*"]
      },
      {
        ResourceType = "collection"
        Resource     = ["collection/${local.resource_prefix}-memory"]
        Permission   = ["aoss:*"]
      }
    ]
    Principal = [
      aws_iam_role.agentcore_execution.arn,
    ]
  }])
}
