"""Test fixtures for RTL runner AMI configuration tests."""

from pathlib import Path

import pytest
import yaml


def _get_config_dir() -> Path:
    """Return the path to the RTL runner config directory."""
    return Path(__file__).parent.parent.parent.parent.parent.parent / \
        "src/api/endpoints/ami_for_rtl_runners/config"


def _load_config(config_name: str) -> dict:
    """Load a configuration file by name."""
    config_path = _get_config_dir() / config_name
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def config_dir() -> Path:
    """Return the path to the RTL runner config directory."""
    return _get_config_dir()


@pytest.fixture
def rtl_sim_config() -> dict:
    """Load the RTL simulation runner config."""
    return _load_config("rtl-sim.yml")


@pytest.fixture
def rtl_synth_config() -> dict:
    """Load the RTL synthesis runner config."""
    return _load_config("rtl-synth.yml")


@pytest.fixture
def rtl_gpu_config() -> dict:
    """Load the RTL GPU runner config."""
    return _load_config("rtl-gpu.yml")
