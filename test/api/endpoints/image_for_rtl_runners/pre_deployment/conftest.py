"""Test fixtures for RTL runner image configuration tests."""

import pytest
from pathlib import Path

import yaml


@pytest.fixture
def config_dir() -> Path:
    """Return the path to the RTL runner config directory."""
    return Path(__file__).parent.parent.parent.parent.parent.parent / \
        "src/api/endpoints/image_for_rtl_runners/config"


@pytest.fixture
def dockerfile_dir() -> Path:
    """Return the path to the RTL runner dockerfile directory."""
    return Path(__file__).parent.parent.parent.parent.parent.parent / \
        "src/api/endpoints/image_for_rtl_runners/dockerfiles"


@pytest.fixture
def rtl_sim_config(config_dir: Path) -> dict:
    """Load the RTL simulation runner config."""
    config_path = config_dir / "rtl-sim.yml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def rtl_synth_config(config_dir: Path) -> dict:
    """Load the RTL synthesis runner config."""
    config_path = config_dir / "rtl-synth.yml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture
def rtl_gpu_config(config_dir: Path) -> dict:
    """Load the RTL GPU runner config."""
    config_path = config_dir / "rtl-gpu.yml"
    with open(config_path, encoding="utf-8") as f:
        return yaml.safe_load(f)
