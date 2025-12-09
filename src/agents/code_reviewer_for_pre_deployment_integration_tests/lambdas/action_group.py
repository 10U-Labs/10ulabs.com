"""Action group Lambda for Test Auditor Bedrock Agent.

This Lambda handles GitHub operations for the Test Auditor Agent:
- Reading files from the repository
- Listing test directories
- Analyzing terraform dependencies
- Creating pull requests with fixes
"""

import base64
import json
import os
import re
from typing import Any
from urllib import request
from urllib.error import HTTPError

from github_auth import get_github_token


def github_api(
    endpoint: str,
    method: str = "GET",
    data: dict[str, Any] | None = None
) -> Any:
    """Make a GitHub API request."""
    token = get_github_token()
    org = os.environ.get("GITHUB_ORG", "10U-Labs-LLC")
    repo = os.environ.get("GITHUB_REPO", "10ulabs.com")

    if endpoint.startswith("/"):
        url = f"https://api.github.com{endpoint}"
    else:
        url = f"https://api.github.com/repos/{org}/{repo}/{endpoint}"

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "TenULabs-TestAuditor-Agent"
    }

    if data:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"
    else:
        body = None

    req = request.Request(url, data=body, headers=headers, method=method)

    try:
        with request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as err:
        error_body = err.read().decode("utf-8")
        raise RuntimeError(f"GitHub API error {err.code}: {error_body}") from err


def list_test_directories() -> dict[str, Any]:
    """List all pre-deployment integration test directories."""
    directories: list[str] = []

    def search_tree(path: str) -> None:
        """Recursively search for pre_deployment/integration directories."""
        try:
            contents = github_api(f"contents/{path}")
            for item in contents:
                if item["type"] == "dir":
                    if item["path"].endswith("pre_deployment/integration"):
                        directories.append(item["path"])
                    elif "test" in item["path"]:
                        search_tree(item["path"])
        except RuntimeError:
            pass

    search_tree("test")

    return {
        "directories": directories,
        "count": len(directories)
    }


def read_file(path: str) -> dict[str, Any]:
    """Read a file from the repository."""
    try:
        response = github_api(f"contents/{path}")
        if response.get("type") != "file":
            return {"error": f"Path '{path}' is not a file"}

        content = base64.b64decode(response["content"]).decode("utf-8")
        return {
            "path": path,
            "content": content,
            "sha": response["sha"]
        }
    except RuntimeError as err:
        return {"error": str(err)}


def read_terraform_data(directory: str) -> dict[str, Any]:
    """Read terraform data.tf to identify dependencies."""
    data_tf_path = f"{directory}/data.tf"
    result = read_file(data_tf_path)

    if "error" in result:
        return {"error": f"Could not read {data_tf_path}: {result['error']}"}

    content = result["content"]
    dependencies: list[dict[str, str]] = []

    # Parse terraform_remote_state blocks
    remote_state_pattern = re.compile(
        r'data\s+"terraform_remote_state"\s+"(\w+)".*?'
        r'key\s*=\s*"([^"]+)"',
        re.DOTALL
    )
    for match in remote_state_pattern.finditer(content):
        dependencies.append({
            "type": "terraform_remote_state",
            "name": match.group(1),
            "key": match.group(2)
        })

    # Parse data blocks (like aws_ssm_parameter, etc.)
    data_block_pattern = re.compile(
        r'data\s+"(\w+)"\s+"(\w+)"',
        re.MULTILINE
    )
    for match in data_block_pattern.finditer(content):
        if match.group(1) != "terraform_remote_state":
            dependencies.append({
                "type": match.group(1),
                "name": match.group(2)
            })

    return {
        "directory": directory,
        "data_tf_path": data_tf_path,
        "dependencies": dependencies
    }


def analyze_test_compliance(
    test_file_path: str,
    expected_dependencies: str
) -> dict[str, Any]:
    """Analyze if a test file follows the five-layer testing approach."""
    result = read_file(test_file_path)
    if "error" in result:
        return {"compliant": False, "error": result["error"]}

    content = result["content"]
    deps = json.loads(expected_dependencies)
    issues: list[str] = []

    # Check for test class patterns
    has_auth_test = bool(re.search(
        r"class\s+Test\w*(Credentials?|Authentication|IAM)",
        content,
        re.IGNORECASE
    ))
    has_existence_test = bool(re.search(
        r"class\s+Test\w*Existence",
        content,
        re.IGNORECASE
    ))
    has_capability_test = bool(re.search(
        r"class\s+Test\w*Capability",
        content,
        re.IGNORECASE
    ))

    # Check test ordering (tests should be numbered)
    tests = re.findall(r"def\s+(test_\d+_\w+)", content)
    if not tests:
        issues.append("Tests are not numbered (e.g., test_01_, test_02_)")

    # Check for Layer 1 (Authentication)
    if "test_01" in test_file_path.lower() or has_auth_test:
        if not re.search(r"sts.*get_caller_identity|credentials", content, re.I):
            issues.append("Layer 1 (Authentication): Missing credential validation")

    # Check for Layer 2 (Authorization) - HeadBucket, DescribeRole, etc.
    if not re.search(r"head_bucket|describe|list_attached", content, re.I):
        issues.append("Layer 2 (Authorization): Missing API permission checks")

    # Check for Layer 3 (Existence)
    if not has_existence_test:
        issues.append("Layer 3 (Existence): Missing existence verification tests")

    # Check for Layer 5 (Capability)
    if not has_capability_test:
        issues.append("Layer 5 (Capability): Missing capability tests (e.g., put_object)")

    # Check for actionable error messages
    if not re.search(r'pytest\.fail\(.*".*Check|Run|Verify', content):
        issues.append("Missing actionable error messages with remediation steps")

    # Verify dependencies match
    tested_resources: list[str] = []
    if re.search(r"s3.*bucket|bucket_name", content, re.I):
        tested_resources.append("s3_bucket")
    if re.search(r"iam.*role|role_arn", content, re.I):
        tested_resources.append("iam_role")

    return {
        "test_file": test_file_path,
        "compliant": len(issues) == 0,
        "issues": issues,
        "layers_detected": {
            "authentication": has_auth_test,
            "existence": has_existence_test,
            "capability": has_capability_test
        },
        "tested_resources": tested_resources,
        "expected_dependencies": deps
    }


def get_documented_approach() -> dict[str, Any]:
    """Get the documented five-layer testing approach."""
    docs_path = os.environ.get(
        "DOCS_APPROACH",
        "docs/APPROACH_TO_PRE_DEPLOYMENT_INTEGRATION_TESTS.md"
    )
    return read_file(docs_path)


def _create_branch(branch_name: str) -> str | None:
    """Create a new branch from main. Returns error message or None on success."""
    main_ref = github_api("git/ref/heads/main")
    main_sha = main_ref["object"]["sha"]
    try:
        github_api(
            "git/refs",
            method="POST",
            data={"ref": f"refs/heads/{branch_name}", "sha": main_sha}
        )
    except RuntimeError as err:
        if "Reference already exists" not in str(err):
            return f"Failed to create branch: {err}"
    return None


def _update_file(file_path: str, content: str, branch_name: str) -> None:
    """Create or update a file in the repository."""
    try:
        existing = github_api(f"contents/{file_path}?ref={branch_name}")
        file_sha = existing.get("sha")
    except RuntimeError:
        file_sha = None

    payload: dict[str, Any] = {
        "message": f"fix: Update {file_path} to follow five-layer testing approach",
        "content": base64.b64encode(content.encode("utf-8")).decode("utf-8"),
        "branch": branch_name
    }
    if file_sha:
        payload["sha"] = file_sha
    github_api(f"contents/{file_path}", method="PUT", data=payload)


def create_pull_request(
    branch_name: str,
    title: str,
    body: str,
    files: str
) -> dict[str, Any]:
    """Create a pull request with test fixes."""
    files_dict = json.loads(files)

    error = _create_branch(branch_name)
    if error:
        return {"error": error}

    for file_path, content in files_dict.items():
        _update_file(file_path, content, branch_name)

    pr_response = github_api(
        "pulls",
        method="POST",
        data={"title": title, "body": body, "head": branch_name, "base": "main"}
    )

    return {
        "pull_request_url": pr_response["html_url"],
        "pull_request_number": pr_response["number"],
        "branch": branch_name,
        "files_updated": list(files_dict.keys())
    }


def _dispatch_function(function: str, params: dict[str, str]) -> dict[str, Any]:
    """Dispatch to the appropriate handler function."""
    dispatch_table: dict[str, Any] = {
        "list_test_directories": list_test_directories,
        "get_documented_approach": get_documented_approach,
    }
    if function in dispatch_table:
        return dispatch_table[function]()
    if function == "read_file":
        return read_file(params["path"])
    if function == "read_terraform_data":
        return read_terraform_data(params["directory"])
    if function == "analyze_test_compliance":
        return analyze_test_compliance(
            params["test_file_path"], params["expected_dependencies"]
        )
    if function == "create_pull_request":
        return create_pull_request(
            params["branch_name"], params["title"], params["body"], params["files"]
        )
    return {"error": f"Unknown function: {function}"}


def handle_action(
    function: str,
    parameters: list[dict[str, Any]]
) -> dict[str, Any]:
    """Route the action to the appropriate function."""
    params: dict[str, str] = {p["name"]: p["value"] for p in parameters}
    return _dispatch_function(function, params)


def handler(event: dict[str, Any], _context: Any) -> dict[str, Any]:
    """Lambda handler for Bedrock Agent action group."""
    print(f"Received event: {json.dumps(event)}")

    action_group = event.get("actionGroup", "")
    function = event.get("function", "")
    parameters = event.get("parameters", [])

    try:
        result = handle_action(function, parameters)
        response_body = {"TEXT": {"body": json.dumps(result)}}
    except (RuntimeError, KeyError, ValueError, json.JSONDecodeError) as err:
        print(f"Error: {err}")
        response_body = {"TEXT": {"body": json.dumps({"error": str(err)})}}

    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": action_group,
            "function": function,
            "functionResponse": {
                "responseBody": response_body
            }
        }
    }
