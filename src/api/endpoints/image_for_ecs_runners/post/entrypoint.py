#!/usr/bin/env python3
"""Entrypoint script for GitHub Actions self-hosted runner on Fargate.

Uses --ephemeral flag so runner auto-deregisters after one job.
Monitors workflow run status to detect cancelled jobs and exit early.
"""
import argparse
import json
import os
import signal
import subprocess
import sys
import threading
import urllib.error
import urllib.request
from typing import Any

# Module-level state for CloudWatch agent and run monitor
_cw_state: dict[str, Any] = {"stop_event": None, "thread": None}
monitor_state: dict[str, Any] = {"stop_event": None, "should_terminate": False}


def _run_cloudwatch_agent(toml_path: str, stop_event: threading.Event) -> None:
    """Run CloudWatch agent in a thread until stop event is set."""
    with subprocess.Popen(
        ['/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent',
         '-config', toml_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    ) as process:
        # Wait for stop signal, checking periodically
        while not stop_event.wait(timeout=1.0):
            if process.poll() is not None:
                break
        # Stop event received or process exited, terminate if still running
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()


def start_cloudwatch_agent():
    """Start the CloudWatch agent for log collection.

    Run agent directly without systemd (containers don't have systemd).
    """
    print("Starting CloudWatch agent...", flush=True)
    config_path = '/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json'
    toml_path = '/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.toml'

    # Translate JSON config to TOML
    result = subprocess.run(
        ['/opt/aws/amazon-cloudwatch-agent/bin/config-translator',
         '--input', config_path,
         '--output', toml_path,
         '--mode', 'auto'],
        check=False,
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        print(f"Warning: Config translation failed: {result.stderr}", flush=True)
        return

    # Start agent in background thread
    stop_event = threading.Event()
    _cw_state["stop_event"] = stop_event
    thread = threading.Thread(
        target=_run_cloudwatch_agent,
        args=(toml_path, stop_event),
        daemon=True
    )
    thread.start()
    _cw_state["thread"] = thread
    print("CloudWatch agent started successfully", flush=True)


def stop_cloudwatch_agent():
    """Stop the CloudWatch agent and wait for it to terminate."""
    stop_event = _cw_state.get("stop_event")
    thread = _cw_state.get("thread")
    if stop_event is not None:
        stop_event.set()
    if thread is not None:
        thread.join(timeout=5)


def cleanup_runner(token: str) -> None:
    """Remove/deregister the runner from GitHub."""
    print("Deregistering runner...", flush=True)
    subprocess.run(
        ['./config.sh', '--remove', '--token', token],
        check=False,
        capture_output=True
    )


def get_workflow_run_status(repo: str, run_id: str, github_token: str) -> str | None:
    """Check the status of a workflow run.

    Returns:
        Run status ('queued', 'in_progress', 'completed', etc.) or None on error.
    """
    url = f"https://api.github.com/repos/{repo}/actions/runs/{run_id}"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "FargateRunner/1.0",
    }

    request = urllib.request.Request(url, headers=headers, method="GET")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
            return data.get("status")
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as e:
        print(f"Warning: Failed to check workflow run status: {e}", flush=True)
        return None


def monitor_workflow_run(
    repo: str,
    run_id: str,
    github_token: str,
    stop_event: threading.Event,
    check_interval: int = 30,
) -> None:
    """Monitor workflow run status in a background thread.

    Terminates the runner if the workflow run is cancelled or completed
    before the runner picks up a job.
    """
    while not stop_event.wait(timeout=check_interval):
        status = get_workflow_run_status(repo, run_id, github_token)
        if status is None:
            # API error, continue monitoring
            continue

        if status == "completed":
            # Run completed (possibly cancelled) before we got a job
            print(f"Workflow run {run_id} completed, terminating runner...", flush=True)
            monitor_state["should_terminate"] = True
            # Send SIGTERM to self to trigger graceful shutdown
            os.kill(os.getpid(), signal.SIGTERM)
            return

        if status not in ("queued", "in_progress", "waiting", "pending"):
            # Unexpected status, log and continue
            print(f"Workflow run {run_id} has unexpected status: {status}", flush=True)


def start_run_monitor(repo: str, run_id: str, github_token: str, check_interval: int = 30):
    """Start the workflow run status monitor.

    This monitors the workflow run and terminates the runner if the run
    is cancelled before the runner picks up a job.
    """
    if not run_id or not github_token:
        print("Run monitor disabled: missing run_id or github_token", flush=True)
        return

    print(f"Starting workflow run monitor for run {run_id}...", flush=True)
    stop_event = threading.Event()
    monitor_state["stop_event"] = stop_event
    thread = threading.Thread(
        target=monitor_workflow_run,
        args=(repo, run_id, github_token, stop_event, check_interval),
        daemon=True,
    )
    thread.start()


def stop_run_monitor():
    """Stop the workflow run monitor."""
    stop_event = monitor_state.get("stop_event")
    if stop_event is not None:
        stop_event.set()


def extract_run_id_from_name(runner_name: str) -> str | None:
    """Extract run ID from runner name like 'fargate-runner-12345'."""
    if runner_name.startswith("fargate-runner-"):
        return runner_name.replace("fargate-runner-", "")
    return None


def _parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='GitHub Actions self-hosted runner for Fargate')
    parser.add_argument('--repo', required=True, help='GitHub repository (org/repo)')
    parser.add_argument('--name', required=True, help='Runner name')
    parser.add_argument('--labels', required=True, help='Comma-separated runner labels')
    parser.add_argument('--token', required=True, help='GitHub runner registration token')
    parser.add_argument(
        '--check-interval',
        type=int,
        default=30,
        help='Interval in seconds to check workflow run status (default: 30)',
    )
    return parser.parse_args()


def _configure_runner(repo: str, registration_token: str, runner_name: str, runner_labels: str):
    """Configure the GitHub Actions runner."""
    config_result = subprocess.run([
        './config.sh',
        '--url', f'https://github.com/{repo}',
        '--token', registration_token,
        '--name', runner_name,
        '--labels', runner_labels,
        '--work', '_work',
        '--unattended',
        '--ephemeral'
    ], check=False)
    return config_result.returncode


def _create_signal_handler(state: dict):
    """Create signal handler for graceful shutdown."""
    def signal_handler(_signum, _frame):
        reason = "run cancelled" if monitor_state.get("should_terminate") else "signal received"
        print(f"Shutting down ({reason}), cleaning up...", flush=True)
        stop_run_monitor()
        if state["process"] is not None:
            state["process"].terminate()
            try:
                state["process"].wait(timeout=3)
            except subprocess.TimeoutExpired:
                print("Runner did not exit, sending SIGKILL...", flush=True)
                state["process"].kill()
                try:
                    state["process"].wait(timeout=2)
                except subprocess.TimeoutExpired:
                    print("Runner still not dead after SIGKILL", flush=True)
        stop_cloudwatch_agent()
        print("Shutdown complete", flush=True)
        sys.exit(0)
    return signal_handler


def main():
    """Main entry point for the runner script."""
    args = _parse_args()
    repo = args.repo
    runner_name = args.name
    github_token = os.environ.get("GITHUB_TOKEN", "")
    run_id = extract_run_id_from_name(runner_name)

    print("Registering GitHub Actions runner...", flush=True)
    print(f"Repository: {repo}", flush=True)
    print(f"Runner Name: {runner_name}", flush=True)
    print(f"Labels: {args.labels}", flush=True)
    if run_id:
        print(f"Run ID: {run_id}", flush=True)
    print(f"Run monitor: {'enabled' if github_token and run_id else 'disabled'}", flush=True)

    state = {"process": None}
    signal.signal(signal.SIGTERM, _create_signal_handler(state))
    signal.signal(signal.SIGINT, _create_signal_handler(state))

    if _configure_runner(repo, args.token, runner_name, args.labels) != 0:
        print("Error: config.sh failed", flush=True)
        sys.exit(1)

    start_cloudwatch_agent()
    if run_id and github_token:
        start_run_monitor(repo, run_id, github_token, args.check_interval)

    print("Starting runner...", flush=True)
    with subprocess.Popen(['./run.sh']) as process:
        state["process"] = process
        returncode = process.wait()

    stop_run_monitor()
    stop_cloudwatch_agent()
    print(f"Runner exited with code {returncode}", flush=True)
    sys.exit(returncode)


if __name__ == '__main__':
    main()
