import json
import urllib.request


def test_repository_has_at_least_one_webhook(github_pat, config):
    url = f"https://api.github.com/repos/{config['github_repo']}/hooks"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {github_pat}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as response:
        hooks = json.loads(response.read())
    assert len(hooks) > 0


def test_github_webhook_for_runners_endpoint_exists(github_pat, config):
    url = f"https://api.github.com/repos/{config['github_repo']}/hooks"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {github_pat}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as response:
        hooks = json.loads(response.read())
    webhook_url = f"https://{config['domain_subdomain']}/v1/runners"
    matching_hooks = [hook for hook in hooks if hook["config"]["url"] == webhook_url]
    assert len(matching_hooks) == 1


def test_github_webhook_for_runners_endpoint_listens_for_workflow_job_events(github_pat, config):
    url = f"https://api.github.com/repos/{config['github_repo']}/hooks"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {github_pat}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as response:
        hooks = json.loads(response.read())
    webhook_url = f"https://{config['domain_subdomain']}/v1/runners"
    matching_hooks = [hook for hook in hooks if hook["config"]["url"] == webhook_url]
    assert "workflow_job" in matching_hooks[0]["events"]


def test_github_webhook_for_runners_endpoint_is_active(github_pat, config):
    url = f"https://api.github.com/repos/{config['github_repo']}/hooks"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {github_pat}", "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req) as response:
        hooks = json.loads(response.read())
    webhook_url = f"https://{config['domain_subdomain']}/v1/runners"
    matching_hooks = [hook for hook in hooks if hook["config"]["url"] == webhook_url]
    assert matching_hooks[0]["active"] is True
