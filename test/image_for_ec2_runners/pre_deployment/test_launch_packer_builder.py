from unittest.mock import patch
import pytest


@pytest.mark.usefixtures("mock_env_vars")
class TestLaunchPackerBuilder:

    def test_successful_workflow_trigger(self, v1_handler):
        with patch.object(v1_handler, 'trigger_github_workflow', return_value={'success': True}):
            result = v1_handler.launch_packer_builder({})

            assert result['success'] is True

    def test_calls_trigger_github_workflow_once(self, v1_handler):
        with patch.object(v1_handler, 'trigger_github_workflow', return_value={'success': True}) as mock_trigger:
            v1_handler.launch_packer_builder({})

            mock_trigger.assert_called_once()

    def test_calls_with_correct_workflow_file(self, v1_handler):
        with patch.object(v1_handler, 'trigger_github_workflow', return_value={'success': True}) as mock_trigger:
            v1_handler.launch_packer_builder({})

            assert mock_trigger.call_args[0][0] == 'image_for_ec2_runners_post.yml'

    def test_error_handling(self, v1_handler):
        with patch.object(v1_handler, 'trigger_github_workflow', return_value={'success': False, 'error': 'failed'}):
            result = v1_handler.launch_packer_builder({})

            assert result['success'] is False
