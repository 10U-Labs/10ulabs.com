"""Unit tests for launch_packer_builder functionality."""
from unittest.mock import patch
import pytest


@pytest.mark.usefixtures("mock_env_vars")
class TestLaunchPackerBuilder:
    """Tests for launch_packer_builder when triggering GitHub workflows."""

    def test_successful_workflow_trigger(self, handler_module):
        """Test that successful workflow trigger returns success."""
        with patch.object(
            handler_module, 'trigger_github_workflow', return_value={'success': True}
        ):
            result = handler_module.launch_packer_builder({})

            assert result['success'] is True

    def test_calls_trigger_github_workflow_once(self, handler_module):
        """Test that trigger_github_workflow is called exactly once."""
        with patch.object(
            handler_module, 'trigger_github_workflow', return_value={'success': True}
        ) as mock_trigger:
            handler_module.launch_packer_builder({})

            mock_trigger.assert_called_once()

    def test_calls_with_correct_workflow_file(self, handler_module):
        """Test that workflow is triggered with correct workflow file name."""
        with patch.object(
            handler_module, 'trigger_github_workflow', return_value={'success': True}
        ) as mock_trigger:
            handler_module.launch_packer_builder({})

            assert mock_trigger.call_args[0][0] == 'image_for_ec2_runners_post.yml'

    def test_error_handling(self, handler_module):
        """Test that errors from workflow trigger are properly handled."""
        with patch.object(
            handler_module,
            'trigger_github_workflow',
            return_value={'success': False, 'error': 'failed'}
        ):
            result = handler_module.launch_packer_builder({})

            assert result['success'] is False
