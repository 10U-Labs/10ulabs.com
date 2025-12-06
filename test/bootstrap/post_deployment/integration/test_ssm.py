"""Integration tests for SSM parameter configuration."""


def test_github_pat_parameter_exists(ssm_client, config):
    """Test that GitHub PAT parameter exists in SSM."""
    response = ssm_client.describe_parameters(
        Filters=[{'Key': 'Name', 'Values': [config['ssm_parameter_name_for_github_pat']]}]
    )
    assert len(response['Parameters']) == 1


def test_github_pat_parameter_type_is_secure_string(ssm_client, config):
    """Test that GitHub PAT parameter is SecureString type."""
    response = ssm_client.describe_parameters(
        Filters=[{'Key': 'Name', 'Values': [config['ssm_parameter_name_for_github_pat']]}]
    )
    parameter = response['Parameters'][0]
    assert parameter['Type'] == 'SecureString'


def test_github_pat_parameter_has_value(ssm_client, config):
    """Test that GitHub PAT parameter has a value."""
    param_name = config['ssm_parameter_name_for_github_pat']
    response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
    parameter_value = response['Parameter']['Value']
    assert parameter_value != ''


def test_github_pat_parameter_value_is_not_placeholder(ssm_client, config):
    """Test that GitHub PAT parameter value is not a placeholder."""
    param_name = config['ssm_parameter_name_for_github_pat']
    response = ssm_client.get_parameter(Name=param_name, WithDecryption=True)
    parameter_value = response['Parameter']['Value']
    assert not parameter_value.startswith('PLACEHOLDER')
