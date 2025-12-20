"""Unit tests for agents runtime tools.py."""
from repo_utils import REPO_ROOT

AGENTS_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "agents"
RUNTIME_DIR = AGENTS_SRC / "runtime"


def test_runtime_tools_py_exists():
    """Test that tools.py exists in runtime directory."""
    tools_file = RUNTIME_DIR / "tools.py"
    assert tools_file.exists()


def test_runtime_tools_exports_all_tools():
    """Test that tools.py exports ALL_TOOLS list."""
    tools_file = RUNTIME_DIR / "tools.py"
    content = tools_file.read_text()
    assert "ALL_TOOLS" in content


class TestGitHubTools:
    """Tests for GitHub API tools."""

    def test_get_workflow_logs_tool_exists(self):
        """Test that get_workflow_logs tool is defined."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "def get_workflow_logs" in content

    def test_get_file_content_tool_exists(self):
        """Test that get_file_content tool is defined."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "def get_file_content" in content

    def test_list_directory_tool_exists(self):
        """Test that list_directory tool is defined."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "def list_directory" in content

    def test_create_branch_tool_exists(self):
        """Test that create_branch tool is defined."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "def create_branch" in content

    def test_commit_file_tool_exists(self):
        """Test that commit_file tool is defined."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "def commit_file" in content

    def test_create_pull_request_tool_exists(self):
        """Test that create_pull_request tool is defined."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "def create_pull_request" in content


class TestAWSTools:
    """Tests for AWS SDK tools."""

    def test_aws_ssm_get_tool_exists(self):
        """Test that aws_ssm_get tool is defined."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "def aws_ssm_get" in content

    def test_aws_s3_put_tool_exists(self):
        """Test that aws_s3_put tool is defined."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "def aws_s3_put" in content

    def test_aws_s3_get_tool_exists(self):
        """Test that aws_s3_get tool is defined."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "def aws_s3_get" in content

    def test_aws_lambda_invoke_tool_exists(self):
        """Test that aws_lambda_invoke tool is defined."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "def aws_lambda_invoke" in content


class TestToolsIntegrity:
    """Tests for tools module integrity."""

    def test_tools_contains_get_workflow_logs(self):
        """Test that tools module contains get_workflow_logs."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "get_workflow_logs" in content

    def test_tools_contains_create_pull_request(self):
        """Test that tools module contains create_pull_request."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "create_pull_request" in content

    def test_tools_contains_aws_ssm_get(self):
        """Test that tools module contains aws_ssm_get."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "aws_ssm_get" in content

    def test_tools_contains_aws_s3_put(self):
        """Test that tools module contains aws_s3_put."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "aws_s3_put" in content

    def test_tools_import_strands_decorator(self):
        """Test that tools import the @tool decorator from strands."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "from strands import tool" in content

    def test_tools_has_minimum_tool_decorators(self):
        """Test that tools module has at least 6 @tool decorators."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        tool_count = content.count("@tool")
        assert tool_count >= 6


class TestSSLAndRetry:
    """Tests for SSL certificate handling and retry logic."""

    def test_tools_imports_ssl_module(self):
        """Test that tools.py imports ssl module for HTTPS."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "import ssl" in content

    def test_tools_imports_certifi(self):
        """Test that tools.py imports certifi for CA certificates."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "import certifi" in content

    def test_tools_has_ssl_context_function(self):
        """Test that tools.py has SSL context creation function."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "_create_ssl_context" in content

    def test_github_request_uses_ssl_context(self):
        """Test that GitHub requests use SSL context."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "context=" in content

    def test_github_request_has_max_retries(self):
        """Test that GitHub requests use max retries constant."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "_MAX_RETRIES" in content

    def test_github_request_has_retryable_status_codes(self):
        """Test that GitHub requests define retryable status codes."""
        tools_file = RUNTIME_DIR / "tools.py"
        content = tools_file.read_text()
        assert "_RETRYABLE_STATUS_CODES" in content
