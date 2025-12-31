"""Tests for test configuration fixtures."""


def test_config_has_aws_account_id(config):
    """Verify that config fixture provides AWS account ID."""
    assert "aws_account_id" in config


def test_config_has_aws_region(config):
    """Verify that config fixture provides AWS region."""
    assert "aws_region" in config
