"""Unit tests for agents webhook.js Lambda handler."""
from repo_utils import REPO_ROOT

AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"
LAMBDAS_DIR = AGENTS_SRC / "lambdas"


def test_webhook_js_exists():
    """Verify webhook.js file exists."""
    webhook_file = LAMBDAS_DIR / "webhook.js"
    assert webhook_file.exists()


def test_webhook_has_jitter_delay():
    """Verify webhook handler has jitter delay to prevent thundering herd."""
    webhook_file = LAMBDAS_DIR / "webhook.js"
    content = webhook_file.read_text()
    assert "jitterDelay" in content


def test_webhook_jitter_uses_random():
    """Verify jitter delay uses random for distribution."""
    webhook_file = LAMBDAS_DIR / "webhook.js"
    content = webhook_file.read_text()
    assert "Math.random()" in content


def test_webhook_jitter_uses_settimeout():
    """Verify jitter delay uses setTimeout for async wait."""
    webhook_file = LAMBDAS_DIR / "webhook.js"
    content = webhook_file.read_text()
    assert "setTimeout" in content
