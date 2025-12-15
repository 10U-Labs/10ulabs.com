"""
Scanner Lambda - Scans for unresolved workflow failures from SQS.

Single responsibility: Find and process unresolved GitHub workflow failures
by scanning the repository and invoking the troubleshooter agent.

Trigger: SQS (scanner_queue) <- EventBridge (15 min schedule)

Note: github_auth and agent_utils are Lambda layers. Stubs provided for type checking.
"""

import json
import logging
import os
import random
import time
import urllib.request
import urllib.error
from typing import Any

from botocore.exceptions import ClientError

try:
    from agent_utils import invoke_agent, handle_recommendation, process_sqs_records
    from github_auth import get_github_token
except ImportError:
    # Stubs for when Lambda layer is not available (linting/testing)
    from typing import Callable

    def invoke_agent(agent_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Stub."""
        raise NotImplementedError("agent_utils layer not available")

    def handle_recommendation(
        result: dict[str, Any], github_token: str
    ) -> dict[str, Any]:
        """Stub."""
        raise NotImplementedError("agent_utils layer not available")

    def process_sqs_records(
        event: dict[str, Any],
        github_token: str,
        processor: Callable[[dict[str, Any], str], dict[str, Any]],
    ) -> dict[str, Any]:
        """Stub."""
        raise NotImplementedError("agent_utils layer not available")

    def get_github_token() -> str:
        """Stub."""
        raise NotImplementedError("github_auth layer not available")


logger = logging.getLogger()
logger.setLevel(logging.INFO)

GITHUB_ORG = os.environ.get("GITHUB_ORG", "10U-Labs-LLC")
GITHUB_REPO = os.environ.get("GITHUB_REPO", "10ulabs.com")


def _github_api_request(
    endpoint: str, token: str, method: str = "GET"
) -> dict[str, Any]:
    """Make a request to the GitHub API."""
    url = f"https://api.github.com{endpoint}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "AgentScanner/1.0",
    }

    req = urllib.request.Request(url, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as err:
        error_body = err.read().decode("utf-8") if err.fp else ""
        raise RuntimeError(f"GitHub API error {err.code}: {error_body}") from err


def _get_unresolved_failures(token: str) -> list[dict[str, Any]]:
    """Find workflow runs that failed and haven't been successfully re-run."""
    endpoint = f"/repos/{GITHUB_ORG}/{GITHUB_REPO}/actions/runs?status=failure&per_page=50"
    response = _github_api_request(endpoint, token)

    unresolved = []
    for run in response.get("workflow_runs", []):
        workflow_id = run["workflow_id"]
        head_branch = run["head_branch"]

        check_endpoint = (
            f"/repos/{GITHUB_ORG}/{GITHUB_REPO}/actions/workflows/{workflow_id}/runs"
            f"?branch={head_branch}&status=success&per_page=1"
        )
        try:
            success_response = _github_api_request(check_endpoint, token)
            success_runs = success_response.get("workflow_runs", [])

            if success_runs:
                latest_success = success_runs[0]
                if latest_success["created_at"] > run["created_at"]:
                    continue

            workflow_name = run.get("name", "").lower()
            if "agent" in workflow_name:
                continue

            unresolved.append(run)
        except RuntimeError:
            continue

    return unresolved


def _build_agent_payload_from_run(run: dict[str, Any], github_token: str) -> dict[str, Any]:
    """Build agent payload from a workflow run object."""
    return {
        "github_token": github_token,
        "owner": GITHUB_ORG,
        "repo": GITHUB_REPO,
        "run_id": run.get("id"),
        "workflow_name": run.get("name"),
        "workflow_path": run.get("path", ""),
        "head_sha": run.get("head_sha"),
        "head_branch": run.get("head_branch"),
    }


def _process_unresolved_failure(run: dict[str, Any], github_token: str) -> dict[str, Any]:
    """Process a single unresolved failure with retry logic."""
    run_id = run.get("id")
    logger.info("Processing unresolved failure: %s (run %s)", run["name"], run_id)

    initial_delay = random.uniform(0, 30)
    logger.info("Initial delay of %.1fs before processing run %s", initial_delay, run_id)
    time.sleep(initial_delay)

    max_attempts = 7
    for attempt in range(max_attempts):
        try:
            agent_payload = _build_agent_payload_from_run(run, github_token)
            result = invoke_agent("troubleshooter_of_workflows", agent_payload)
            result = handle_recommendation(result, github_token)

            return {"run_id": run_id, "status": "processed", "result": result}

        except (ClientError, ValueError) as err:
            if attempt < max_attempts - 1:
                backoff = 2 ** (4 + attempt)
                logger.warning(
                    "Attempt %d/%d failed for run %s, retrying in %ds: %s",
                    attempt + 1,
                    max_attempts,
                    run_id,
                    backoff,
                    err,
                )
                time.sleep(backoff)
            else:
                logger.error(
                    "All %d retries exhausted for run %s: %s", max_attempts, run_id, err
                )
                return {"run_id": run_id, "status": "error", "error": str(err)}

    return {"run_id": run_id, "status": "error", "error": "Unknown error"}


def _run_scan(github_token: str, test_mode: bool = False) -> dict[str, Any]:
    """Run the scan for unresolved failures."""
    logger.info("Running scheduled scan for unresolved workflow failures")

    if test_mode:
        logger.info("Test mode enabled, skipping actual scan")
        return {"mode": "scheduled", "processed": 0, "test_mode": True}

    unresolved = _get_unresolved_failures(github_token)
    logger.info("Found %d unresolved failures", len(unresolved))

    results = []
    for run in unresolved:
        result = _process_unresolved_failure(run, github_token)
        results.append(result)

    return {"mode": "scheduled", "processed": len(results), "results": results}


def _process_record(body: dict[str, Any], github_token: str) -> dict[str, Any]:
    """Process a single SQS record body."""
    test_mode = body.get("test_mode", False)
    return _run_scan(github_token, test_mode=test_mode)


def lambda_handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for SQS scanner events."""
    return process_sqs_records(event, get_github_token(), _process_record)
