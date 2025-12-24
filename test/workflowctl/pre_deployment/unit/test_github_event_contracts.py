"""Contract tests documenting GitHub Actions event data shapes.

These tests document the contract between GitHub Actions and our code,
ensuring we handle all event types correctly. They serve as executable
documentation for the expected data shapes from different GitHub events.

GitHub Actions webhook event documentation:
https://docs.github.com/en/webhooks/webhook-events-and-payloads
"""
import json

from get_changed_files import filter_files_by_commits


class TestGitHubEventContracts:
    """Tests verifying expected GitHub Actions event data shapes."""

    def test_push_event_commits_shape(self) -> None:
        """Push events provide commits as array of {id, message, ...}.

        When a push event triggers a workflow, github.event.commits contains
        an array of commit objects. Each commit has id, message, and other
        fields. toJSON() serializes this as a JSON array.

        See: https://docs.github.com/en/webhooks/webhook-events-and-payloads#push
        """
        # Simulates toJSON(github.event.commits) for a push event
        push_commits = json.dumps([
            {"id": "abc123", "message": "Fix bug"},
            {"id": "def456", "message": "Add feature"},
        ])

        # Should process without error (returns empty since no [skip ci])
        result = filter_files_by_commits(push_commits)
        assert result == set()

    def test_workflow_dispatch_commits_is_null(self) -> None:
        """workflow_dispatch events have null commits (serialized as "null").

        When a workflow is triggered manually via workflow_dispatch,
        github.event.commits is null (not an empty array). GitHub's
        toJSON(null) produces the literal string "null".

        This is the edge case that caused the original bug.
        """
        # Simulates toJSON(github.event.commits) for workflow_dispatch
        workflow_dispatch_commits = "null"

        # Should handle gracefully without raising TypeError
        result = filter_files_by_commits(workflow_dispatch_commits)
        assert result == set()

    def test_schedule_event_commits_is_null(self) -> None:
        """Schedule events have null commits (same as workflow_dispatch).

        Scheduled workflows (cron) also have no commits context.
        """
        schedule_commits = "null"
        result = filter_files_by_commits(schedule_commits)
        assert result == set()

    def test_repository_dispatch_commits_is_null(self) -> None:
        """repository_dispatch events have null commits.

        External API triggers via repository_dispatch have no commits.
        """
        repository_dispatch_commits = "null"
        result = filter_files_by_commits(repository_dispatch_commits)
        assert result == set()
