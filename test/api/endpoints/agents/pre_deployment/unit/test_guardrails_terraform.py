"""Unit tests for agents Bedrock Guardrails Terraform configuration."""
from repo_utils import REPO_ROOT

AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"


def test_guardrails_terraform_file_exists():
    """Verify guardrails.tf file exists."""
    guardrails_file = AGENTS_SRC / "guardrails.tf"
    assert guardrails_file.exists()


def test_guardrails_resource_exists():
    """Verify Bedrock Guardrail resource is defined."""
    guardrails_file = AGENTS_SRC / "guardrails.tf"
    with open(guardrails_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_bedrock_guardrail"' in content


def test_guardrails_has_content_policy():
    """Verify guardrails has content policy configuration."""
    guardrails_file = AGENTS_SRC / "guardrails.tf"
    with open(guardrails_file, encoding="utf-8") as f:
        content = f.read()
    assert "content_policy_config" in content


def test_guardrails_has_sensitive_information_policy():
    """Verify guardrails has sensitive information policy."""
    guardrails_file = AGENTS_SRC / "guardrails.tf"
    with open(guardrails_file, encoding="utf-8") as f:
        content = f.read()
    assert "sensitive_information_policy_config" in content


def test_guardrails_blocks_ssn():
    """Verify guardrails blocks social security numbers."""
    guardrails_file = AGENTS_SRC / "guardrails.tf"
    with open(guardrails_file, encoding="utf-8") as f:
        content = f.read()
    assert "US_SOCIAL_SECURITY_NUMBER" in content


def test_guardrails_blocks_credit_cards():
    """Verify guardrails blocks credit card numbers."""
    guardrails_file = AGENTS_SRC / "guardrails.tf"
    with open(guardrails_file, encoding="utf-8") as f:
        content = f.read()
    assert "CREDIT_DEBIT_CARD_NUMBER" in content


def test_guardrails_blocks_aws_access_key():
    """Verify guardrails blocks AWS access keys."""
    guardrails_file = AGENTS_SRC / "guardrails.tf"
    with open(guardrails_file, encoding="utf-8") as f:
        content = f.read()
    assert "AWS_ACCESS_KEY" in content


def test_guardrails_blocks_aws_secret_key():
    """Verify guardrails blocks AWS secret keys."""
    guardrails_file = AGENTS_SRC / "guardrails.tf"
    with open(guardrails_file, encoding="utf-8") as f:
        content = f.read()
    assert "AWS_SECRET_KEY" in content


def test_guardrails_has_topic_policy():
    """Verify guardrails has topic policy configuration."""
    guardrails_file = AGENTS_SRC / "guardrails.tf"
    with open(guardrails_file, encoding="utf-8") as f:
        content = f.read()
    assert "topic_policy_config" in content


def test_guardrails_has_word_policy():
    """Verify guardrails has word policy configuration."""
    guardrails_file = AGENTS_SRC / "guardrails.tf"
    with open(guardrails_file, encoding="utf-8") as f:
        content = f.read()
    assert "word_policy_config" in content


def test_guardrails_blocks_profanity():
    """Verify guardrails blocks profanity."""
    guardrails_file = AGENTS_SRC / "guardrails.tf"
    with open(guardrails_file, encoding="utf-8") as f:
        content = f.read()
    assert "PROFANITY" in content


def test_guardrails_has_contextual_grounding():
    """Verify guardrails has contextual grounding policy."""
    guardrails_file = AGENTS_SRC / "guardrails.tf"
    with open(guardrails_file, encoding="utf-8") as f:
        content = f.read()
    assert "contextual_grounding_policy_config" in content


def test_guardrails_version_exists():
    """Verify guardrails version resource is defined."""
    guardrails_file = AGENTS_SRC / "guardrails.tf"
    with open(guardrails_file, encoding="utf-8") as f:
        content = f.read()
    assert 'resource "aws_bedrock_guardrail_version"' in content
