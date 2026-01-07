"""Unit tests for workflowctl_mocks module."""
from workflowctl_mocks import create_subprocess_result, create_gh_workflow_list_result


class TestCreateSubprocessResult:
    """Tests for create_subprocess_result function."""

    def test_default_returncode_is_zero(self):
        """Test that default returncode is 0."""
        result = create_subprocess_result()
        assert result.returncode == 0

    def test_custom_returncode(self):
        """Test that custom returncode is set."""
        result = create_subprocess_result(returncode=1)
        assert result.returncode == 1

    def test_default_stdout_is_empty(self):
        """Test that default stdout is empty string."""
        result = create_subprocess_result()
        assert result.stdout == ""

    def test_custom_stdout(self):
        """Test that custom stdout is set."""
        result = create_subprocess_result(stdout="output text")
        assert result.stdout == "output text"

    def test_default_stderr_is_empty(self):
        """Test that default stderr is empty string."""
        result = create_subprocess_result()
        assert result.stderr == ""

    def test_custom_stderr(self):
        """Test that custom stderr is set."""
        result = create_subprocess_result(stderr="error text")
        assert result.stderr == "error text"

    def test_all_parameters_together(self):
        """Test all parameters set together."""
        result = create_subprocess_result(
            returncode=2,
            stdout="out",
            stderr="err"
        )
        assert result.returncode == 2
        assert result.stdout == "out"
        assert result.stderr == "err"

    def test_stdout_with_newline(self):
        """Test stdout with newline character."""
        result = create_subprocess_result(stdout="12345\n")
        assert result.stdout == "12345\n"


class TestCreateGhWorkflowListResult:
    """Tests for create_gh_workflow_list_result function."""

    def test_no_workflows_returns_success(self):
        """Test that no workflows returns success returncode."""
        result = create_gh_workflow_list_result()
        assert result.returncode == 0

    def test_no_workflows_returns_empty_stdout(self):
        """Test that no workflows returns empty stdout."""
        result = create_gh_workflow_list_result()
        assert result.stdout == ""

    def test_empty_list_returns_empty_stdout(self):
        """Test that empty list returns empty stdout."""
        result = create_gh_workflow_list_result([])
        assert result.stdout == ""

    def test_single_workflow_in_output(self):
        """Test that single workflow name appears in output."""
        result = create_gh_workflow_list_result(["Bootstrap"])
        assert "Bootstrap" in result.stdout

    def test_multiple_workflows_in_output(self):
        """Test that multiple workflow names appear in output."""
        result = create_gh_workflow_list_result(["Bootstrap", "WWW Shared"])
        assert "Bootstrap" in result.stdout
        assert "WWW Shared" in result.stdout

    def test_output_contains_in_progress_status(self):
        """Test that output contains in_progress status."""
        result = create_gh_workflow_list_result(["Test"])
        assert "in_progress" in result.stdout

    def test_output_contains_main_branch(self):
        """Test that output contains main branch."""
        result = create_gh_workflow_list_result(["Test"])
        assert "main" in result.stdout

    def test_output_contains_push_event(self):
        """Test that output contains push event."""
        result = create_gh_workflow_list_result(["Test"])
        assert "push" in result.stdout

    def test_output_contains_run_id(self):
        """Test that output contains a run ID."""
        result = create_gh_workflow_list_result(["Test"])
        assert "100000" in result.stdout

    def test_multiple_workflows_have_different_run_ids(self):
        """Test that multiple workflows have different run IDs."""
        result = create_gh_workflow_list_result(["First", "Second", "Third"])
        assert "100000" in result.stdout
        assert "100001" in result.stdout
        assert "100002" in result.stdout

    def test_output_lines_are_newline_separated(self):
        """Test that output lines are separated by newlines."""
        result = create_gh_workflow_list_result(["First", "Second"])
        lines = result.stdout.strip().split("\n")
        assert len(lines) == 2

    def test_output_fields_are_tab_separated(self):
        """Test that output fields are tab separated."""
        result = create_gh_workflow_list_result(["Test"])
        assert "\t" in result.stdout
