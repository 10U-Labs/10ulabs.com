from typing import Any, Dict
def test_config_has_aws_account_id(config: Dict[str, Any]) -> None:
    assert "aws_account_id" in config


def test_config_has_aws_region(config: Dict[str, Any]) -> None:
    assert "aws_region" in config
