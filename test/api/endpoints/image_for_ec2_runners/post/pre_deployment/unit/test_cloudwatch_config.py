"""Tests for cloudwatch-agent-config.json file."""
import json
from pathlib import Path


REPO_ROOT = Path(__file__).parent.parent.parent.parent.parent.parent.parent.parent
CONFIG_PATH = (
    REPO_ROOT / "src" / "api" / "endpoints" / "image_for_ec2_runners"
    / "post" / "cloudwatch-agent-config.json"
)


def _read_config():
    """Read and parse the CloudWatch agent config file."""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_cloudwatch_config_file_exists():
    """Test that cloudwatch-agent-config.json file exists."""
    assert CONFIG_PATH.exists()


def test_config_has_metrics_section():
    """Test that config has metrics section."""
    config = _read_config()
    assert "metrics" in config


def test_config_metrics_has_namespace():
    """Test that metrics has GitHubRunner/EC2 namespace."""
    config = _read_config()
    assert config["metrics"]["namespace"] == "GitHubRunner/EC2"


def test_config_collects_memory_metrics():
    """Test that config collects memory metrics."""
    config = _read_config()
    assert "mem" in config["metrics"]["metrics_collected"]


def test_config_memory_has_mem_used_percent():
    """Test that memory config includes mem_used_percent."""
    config = _read_config()
    measurements = config["metrics"]["metrics_collected"]["mem"]["measurement"]
    assert "mem_used_percent" in measurements


def test_config_has_instance_dimensions():
    """Test that config appends InstanceId dimension."""
    config = _read_config()
    dimensions = config["metrics"]["append_dimensions"]
    assert "InstanceId" in dimensions


def test_config_has_instance_type_dimension():
    """Test that config appends InstanceType dimension."""
    config = _read_config()
    dimensions = config["metrics"]["append_dimensions"]
    assert "InstanceType" in dimensions
