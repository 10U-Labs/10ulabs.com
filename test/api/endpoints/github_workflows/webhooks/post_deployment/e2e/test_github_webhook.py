"""Unit tests for test github webhook."""
import json
import urllib.request


def _fetch_github_hooks(github_pat, github_repo):
    """Fetch repository webhooks from GitHub API."""
    url = f"https://api.github.com/repos/{github_repo}/hooks"
    headers = {"Authorization": f"Bearer {github_pat}", "Accept": "application/vnd.github+json"}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read())


def _get_github_workflows_webhook(hooks, api_fqdn):
    """Get the webhook for the github-workflows/webhooks endpoint from a list of hooks."""
    webhook_url = f"https://{api_fqdn}/v1/github-workflows/webhooks"
    matching = [hook for hook in hooks if hook["config"]["url"] == webhook_url]
    return matching[0] if matching else None


def test_repository_has_at_least_one_webhook(github_pat, config):
    """Test repository has at least one webhook."""
    hooks = _fetch_github_hooks(github_pat, config['github_repo'])
    assert len(hooks) > 0


def test_github_webhook_for_github_workflows_webhooks_endpoint_exists(github_pat, config):
    """Test github webhook for github-workflows/webhooks endpoint exists."""
    hooks = _fetch_github_hooks(github_pat, config['github_repo'])
    webhook = _get_github_workflows_webhook(hooks, config['api_fqdn'])
    assert webhook is not None


def test_github_webhook_github_workflows_webhooks_listens_for_workflow_job_events(github_pat, config):
    """Test github webhook for github-workflows/webhooks endpoint listens for workflow_job."""
    hooks = _fetch_github_hooks(github_pat, config['github_repo'])
    webhook = _get_github_workflows_webhook(hooks, config['api_fqdn'])
    assert "workflow_job" in webhook["events"]


def test_github_webhook_for_github_workflows_webhooks_endpoint_is_active(github_pat, config):
    """Test github webhook for github-workflows/webhooks endpoint is active."""
    hooks = _fetch_github_hooks(github_pat, config['github_repo'])
    webhook = _get_github_workflows_webhook(hooks, config['api_fqdn'])
    assert webhook["active"] is True
