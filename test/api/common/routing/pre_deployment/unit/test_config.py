def test_config_has_aws_account_id(config):
    assert "aws_account_id" in config


def test_config_has_aws_region(config):
    assert "aws_region" in config
