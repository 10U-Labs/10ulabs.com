"""Unit tests for github_runner_api module."""
import json
import urllib.error
from unittest.mock import MagicMock, patch

from github_runner_api import (
    get_runner_registration_token,
    list_repo_runners,
    delete_runner,
    cleanup_offline_runners,
    get_existing_runner_for_workflow,
    build_runner_labels,
)


def _create_mock_json_response(data):
    """Create a mock urlopen response that returns JSON data."""
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(data).encode()
    mock_response.__enter__ = MagicMock(return_value=mock_response)
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


def _create_runner_with_labels(runner_id, name, status, label_names):
    """Create a runner dict with the given labels."""
    return {
        'id': runner_id,
        'name': name,
        'status': status,
        'labels': [{'name': label} for label in label_names]
    }


class TestGetRunnerRegistrationToken:
    """Tests for get_runner_registration_token function."""

    @patch('urllib.request.urlopen')
    def test_returns_token_on_success(self, mock_urlopen):
        """Test returns token from successful API response."""
        mock_urlopen.return_value = _create_mock_json_response({'token': 'test-token-123'})

        result = get_runner_registration_token('github-token', 'owner/repo')
        assert result == 'test-token-123'

    @patch('urllib.request.urlopen')
    def test_returns_empty_string_on_error(self, mock_urlopen):
        """Test returns empty string on API error."""
        mock_urlopen.side_effect = urllib.error.URLError('API error')

        result = get_runner_registration_token('github-token', 'owner/repo')
        assert result == ''

    @patch('urllib.request.urlopen')
    def test_uses_repo_in_url(self, mock_urlopen):
        """Test includes repo in GitHub API URL."""
        mock_urlopen.return_value = _create_mock_json_response({'token': 'token'})

        get_runner_registration_token('github-token', 'owner/repo')

        request = mock_urlopen.call_args[0][0]
        assert 'owner/repo' in request.full_url

    @patch('urllib.request.urlopen')
    def test_uses_registration_token_endpoint(self, mock_urlopen):
        """Test calls registration-token endpoint."""
        mock_urlopen.return_value = _create_mock_json_response({'token': 'token'})

        get_runner_registration_token('github-token', 'owner/repo')

        request = mock_urlopen.call_args[0][0]
        assert 'registration-token' in request.full_url


class TestListRepoRunners:
    """Tests for list_repo_runners function."""

    @patch('urllib.request.urlopen')
    def test_returns_correct_runner_count(self, mock_urlopen):
        """Test returns correct number of runners."""
        runners = [{'id': 1, 'name': 'runner-1'}, {'id': 2, 'name': 'runner-2'}]
        mock_urlopen.return_value = _create_mock_json_response({'runners': runners})

        result = list_repo_runners('github-token', 'owner/repo')
        assert len(result) == 2

    @patch('urllib.request.urlopen')
    def test_returns_runner_data(self, mock_urlopen):
        """Test returns runner data correctly."""
        runners = [{'id': 1, 'name': 'runner-1'}, {'id': 2, 'name': 'runner-2'}]
        mock_urlopen.return_value = _create_mock_json_response({'runners': runners})

        result = list_repo_runners('github-token', 'owner/repo')
        assert result[0]['name'] == 'runner-1'

    @patch('urllib.request.urlopen')
    def test_returns_empty_list_on_error(self, mock_urlopen):
        """Test returns empty list on API error."""
        mock_urlopen.side_effect = urllib.error.URLError('API error')

        result = list_repo_runners('github-token', 'owner/repo')
        assert result == []

    @patch('urllib.request.urlopen')
    def test_paginates_for_large_results(self, mock_urlopen):
        """Test paginates when more than 100 runners."""
        page1_runners = [{'id': i, 'name': f'runner-{i}'} for i in range(100)]
        page2_runners = [{'id': 100, 'name': 'runner-100'}]

        mock_response1 = MagicMock()
        mock_response1.read.return_value = json.dumps({'runners': page1_runners}).encode()
        mock_response1.__enter__ = MagicMock(return_value=mock_response1)
        mock_response1.__exit__ = MagicMock(return_value=False)

        mock_response2 = MagicMock()
        mock_response2.read.return_value = json.dumps({'runners': page2_runners}).encode()
        mock_response2.__enter__ = MagicMock(return_value=mock_response2)
        mock_response2.__exit__ = MagicMock(return_value=False)

        mock_urlopen.side_effect = [mock_response1, mock_response2]

        result = list_repo_runners('github-token', 'owner/repo')
        assert len(result) == 101


class TestDeleteRunner:
    """Tests for delete_runner function."""

    @patch('urllib.request.urlopen')
    def test_returns_true_on_204_status(self, mock_urlopen):
        """Test returns True when API returns 204."""
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        result = delete_runner('github-token', 'owner/repo', 123)
        assert result is True

    @patch('urllib.request.urlopen')
    def test_returns_false_on_error(self, mock_urlopen):
        """Test returns False on API error."""
        mock_urlopen.side_effect = urllib.error.URLError('API error')

        result = delete_runner('github-token', 'owner/repo', 123)
        assert result is False

    @patch('urllib.request.urlopen')
    def test_uses_delete_method(self, mock_urlopen):
        """Test uses DELETE HTTP method."""
        mock_response = MagicMock()
        mock_response.status = 204
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_response

        delete_runner('github-token', 'owner/repo', 123)

        request = mock_urlopen.call_args[0][0]
        assert request.method == 'DELETE'


class TestCleanupOfflineRunners:
    """Tests for cleanup_offline_runners function."""

    @patch('github_runner_api.delete_runner')
    @patch('github_runner_api.list_repo_runners')
    def test_finds_offline_runner_with_run_id_label(self, mock_list, mock_delete):
        """Test finds offline runner matching run_id label."""
        mock_list.return_value = [{
            'id': 1,
            'name': 'runner-1',
            'status': 'offline',
            'labels': [{'name': 'runner-12345'}]
        }]
        mock_delete.return_value = True

        result = cleanup_offline_runners('token', 'owner/repo', 12345)

        assert result['found'] == 1

    @patch('github_runner_api.delete_runner')
    @patch('github_runner_api.list_repo_runners')
    def test_deletes_offline_runner_with_run_id_label(self, mock_list, mock_delete):
        """Test deletes offline runner matching run_id label."""
        mock_list.return_value = [{
            'id': 1,
            'name': 'runner-1',
            'status': 'offline',
            'labels': [{'name': 'runner-12345'}]
        }]
        mock_delete.return_value = True

        result = cleanup_offline_runners('token', 'owner/repo', 12345)

        assert result['deleted'] == 1

    @patch('github_runner_api.delete_runner')
    @patch('github_runner_api.list_repo_runners')
    def test_calls_delete_for_offline_runner(self, mock_list, mock_delete):
        """Test calls delete_runner for offline runner with matching label."""
        mock_list.return_value = [{
            'id': 1,
            'name': 'runner-1',
            'status': 'offline',
            'labels': [{'name': 'runner-12345'}]
        }]
        mock_delete.return_value = True

        cleanup_offline_runners('token', 'owner/repo', 12345)

        mock_delete.assert_called_once_with('token', 'owner/repo', 1)

    @patch('github_runner_api.delete_runner')
    @patch('github_runner_api.list_repo_runners')
    def test_skips_online_runners(self, mock_list, mock_delete):
        """Test skips runners with online status."""
        mock_list.return_value = [{
            'id': 1,
            'name': 'runner-1',
            'status': 'online',
            'labels': [{'name': 'runner-12345'}]
        }]

        result = cleanup_offline_runners('token', 'owner/repo', 12345)

        assert result['found'] == 0
        mock_delete.assert_not_called()

    @patch('github_runner_api.delete_runner')
    @patch('github_runner_api.list_repo_runners')
    def test_skips_runners_without_run_id_label(self, mock_list, mock_delete):
        """Test skips offline runners without matching run_id label."""
        mock_list.return_value = [{
            'id': 1,
            'name': 'runner-1',
            'status': 'offline',
            'labels': [{'name': 'runner-99999'}]
        }]

        result = cleanup_offline_runners('token', 'owner/repo', 12345)

        assert result['found'] == 0
        mock_delete.assert_not_called()

    @patch('github_runner_api.delete_runner')
    @patch('github_runner_api.list_repo_runners')
    def test_counts_found_when_delete_fails(self, mock_list, mock_delete):
        """Test counts found runners when delete fails."""
        mock_list.return_value = [{
            'id': 1,
            'name': 'runner-1',
            'status': 'offline',
            'labels': [{'name': 'runner-12345'}]
        }]
        mock_delete.return_value = False

        result = cleanup_offline_runners('token', 'owner/repo', 12345)

        assert result['found'] == 1

    @patch('github_runner_api.delete_runner')
    @patch('github_runner_api.list_repo_runners')
    def test_counts_zero_deleted_when_delete_fails(self, mock_list, mock_delete):
        """Test counts zero deleted when delete fails."""
        mock_list.return_value = [{
            'id': 1,
            'name': 'runner-1',
            'status': 'offline',
            'labels': [{'name': 'runner-12345'}]
        }]
        mock_delete.return_value = False

        result = cleanup_offline_runners('token', 'owner/repo', 12345)

        assert result['deleted'] == 0

    @patch('github_runner_api.delete_runner')
    @patch('github_runner_api.list_repo_runners')
    def test_counts_failed_deletes(self, mock_list, mock_delete):
        """Test counts failed delete attempts."""
        mock_list.return_value = [{
            'id': 1,
            'name': 'runner-1',
            'status': 'offline',
            'labels': [{'name': 'runner-12345'}]
        }]
        mock_delete.return_value = False

        result = cleanup_offline_runners('token', 'owner/repo', 12345)

        assert result['failed'] == 1


class TestGetExistingRunnerForWorkflow:
    """Tests for get_existing_runner_for_workflow function."""

    @patch('github_runner_api.list_repo_runners')
    def test_finds_matching_runner(self, mock_list):
        """Test finds runner matching run_id and labels."""
        runner = _create_runner_with_labels(
            1, 'runner-1', 'online', ['runner-12345', 'self-hosted', 'linux']
        )
        mock_list.return_value = [runner]

        result = get_existing_runner_for_workflow(
            'token', 'owner/repo', 12345, ['self-hosted', 'linux']
        )

        assert result is not None

    @patch('github_runner_api.list_repo_runners')
    def test_returns_correct_runner_id(self, mock_list):
        """Test returns runner with correct id."""
        runner = _create_runner_with_labels(
            1, 'runner-1', 'online', ['runner-12345', 'self-hosted', 'linux']
        )
        mock_list.return_value = [runner]

        result = get_existing_runner_for_workflow(
            'token', 'owner/repo', 12345, ['self-hosted', 'linux']
        )

        assert result['id'] == 1

    @patch('github_runner_api.list_repo_runners')
    def test_returns_none_without_run_id_label(self, mock_list):
        """Test returns None if runner lacks run_id label."""
        mock_list.return_value = [{
            'id': 1,
            'name': 'runner-1',
            'status': 'online',
            'labels': [{'name': 'self-hosted'}, {'name': 'linux'}]
        }]

        result = get_existing_runner_for_workflow(
            'token', 'owner/repo', 12345, ['self-hosted', 'linux']
        )

        assert result is None

    @patch('github_runner_api.list_repo_runners')
    def test_returns_none_for_offline_runner(self, mock_list):
        """Test returns None if runner is offline."""
        mock_list.return_value = [{
            'id': 1,
            'name': 'runner-1',
            'status': 'offline',
            'labels': [{'name': 'runner-12345'}, {'name': 'self-hosted'}]
        }]

        result = get_existing_runner_for_workflow(
            'token', 'owner/repo', 12345, ['self-hosted']
        )

        assert result is None

    @patch('github_runner_api.list_repo_runners')
    def test_returns_none_without_required_labels(self, mock_list):
        """Test returns None if runner lacks required labels."""
        mock_list.return_value = [{
            'id': 1,
            'name': 'runner-1',
            'status': 'online',
            'labels': [{'name': 'runner-12345'}, {'name': 'self-hosted'}]
        }]

        result = get_existing_runner_for_workflow(
            'token', 'owner/repo', 12345, ['self-hosted', 'custom-label']
        )

        assert result is None


class TestBuildRunnerLabels:
    """Tests for build_runner_labels function."""

    def test_includes_self_hosted_label(self):
        """Test includes self-hosted base label."""
        result = build_runner_labels([], None)
        assert 'self-hosted' in result

    def test_includes_linux_label(self):
        """Test includes linux base label."""
        result = build_runner_labels([], None)
        assert 'linux' in result

    def test_includes_x64_label(self):
        """Test includes x64 base label."""
        result = build_runner_labels([], None)
        assert 'x64' in result

    def test_includes_job_labels(self):
        """Test includes job labels."""
        result = build_runner_labels(['custom-label'], None)
        assert 'custom-label' in result

    def test_includes_run_id_label(self):
        """Test includes runner-{run_id} label when run_id provided."""
        result = build_runner_labels([], 12345)
        assert 'runner-12345' in result

    def test_excludes_run_id_label_when_none(self):
        """Test excludes run_id label when run_id is None."""
        result = build_runner_labels([], None)
        assert not any(label.startswith('runner-') for label in result)

    def test_deduplicates_self_hosted_label(self):
        """Test does not duplicate self-hosted label."""
        result = build_runner_labels(['self-hosted', 'linux'], None)
        assert result.count('self-hosted') == 1

    def test_deduplicates_linux_label(self):
        """Test does not duplicate linux label."""
        result = build_runner_labels(['self-hosted', 'linux'], None)
        assert result.count('linux') == 1
