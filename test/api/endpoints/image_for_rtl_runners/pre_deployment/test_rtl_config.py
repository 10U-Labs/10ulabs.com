"""Unit tests for RTL runner image configuration parsing."""

import pytest
from pathlib import Path


class TestRtlSimConfig:
    """Tests for RTL simulation runner configuration."""

    def test_config_file_exists(self, config_dir: Path) -> None:
        """Test that rtl-sim.yml config file exists."""
        config_path = config_dir / "rtl-sim.yml"
        assert config_path.exists(), f"Config file not found: {config_path}"

    def test_runner_section_exists(self, rtl_sim_config: dict) -> None:
        """Test that runner section exists in config."""
        assert "runner" in rtl_sim_config

    def test_runner_user_is_github_runner(self, rtl_sim_config: dict) -> None:
        """Test that runner user is github-runner."""
        assert rtl_sim_config["runner"]["user"] == "github-runner"

    def test_runner_version_is_valid(self, rtl_sim_config: dict) -> None:
        """Test that runner version is a valid semver string."""
        version = rtl_sim_config["runner"]["version"]
        parts = version.split(".")
        assert len(parts) == 3, f"Invalid version format: {version}"
        assert all(part.isdigit() for part in parts)

    def test_instance_type_is_c8i(self, rtl_sim_config: dict) -> None:
        """Test that instance type is c8i.4xlarge for simulation."""
        assert rtl_sim_config["instance"]["type"] == "c8i.4xlarge"

    def test_disk_size_is_at_least_100gb(self, rtl_sim_config: dict) -> None:
        """Test that disk size is at least 100GB for Chipyard."""
        assert rtl_sim_config["instance"]["disk_size_gb"] >= 100

    def test_tools_section_exists(self, rtl_sim_config: dict) -> None:
        """Test that tools section exists."""
        assert "tools" in rtl_sim_config

    def test_chipyard_version_specified(self, rtl_sim_config: dict) -> None:
        """Test that Chipyard version is specified."""
        assert "chipyard" in rtl_sim_config["tools"]
        assert "version" in rtl_sim_config["tools"]["chipyard"]

    def test_verilator_version_specified(self, rtl_sim_config: dict) -> None:
        """Test that Verilator version is specified."""
        assert "verilator" in rtl_sim_config["tools"]
        assert "version" in rtl_sim_config["tools"]["verilator"]

    def test_packages_is_non_empty_list(self, rtl_sim_config: dict) -> None:
        """Test that packages is a non-empty list."""
        assert "packages" in rtl_sim_config
        assert isinstance(rtl_sim_config["packages"], list)
        assert len(rtl_sim_config["packages"]) > 0

    def test_environment_has_riscv_path(self, rtl_sim_config: dict) -> None:
        """Test that RISCV environment variable is set."""
        assert "environment" in rtl_sim_config
        assert "RISCV" in rtl_sim_config["environment"]


class TestRtlSynthConfig:
    """Tests for RTL synthesis runner configuration."""

    def test_config_file_exists(self, config_dir: Path) -> None:
        """Test that rtl-synth.yml config file exists."""
        config_path = config_dir / "rtl-synth.yml"
        assert config_path.exists(), f"Config file not found: {config_path}"

    def test_instance_type_is_r8i(self, rtl_synth_config: dict) -> None:
        """Test that instance type is r8i.4xlarge for synthesis."""
        assert rtl_synth_config["instance"]["type"] == "r8i.4xlarge"

    def test_disk_size_is_at_least_200gb(self, rtl_synth_config: dict) -> None:
        """Test that disk size is at least 200GB for PDK."""
        assert rtl_synth_config["instance"]["disk_size_gb"] >= 200

    def test_openlane_version_specified(self, rtl_synth_config: dict) -> None:
        """Test that OpenLane version is specified."""
        assert "openlane" in rtl_synth_config["tools"]
        assert "version" in rtl_synth_config["tools"]["openlane"]

    def test_sky130_pdk_version_specified(self, rtl_synth_config: dict) -> None:
        """Test that SKY130 PDK version is specified."""
        assert "sky130_pdk" in rtl_synth_config["tools"]
        assert "version" in rtl_synth_config["tools"]["sky130_pdk"]

    def test_environment_has_pdk_root(self, rtl_synth_config: dict) -> None:
        """Test that PDK_ROOT environment variable is set."""
        assert "environment" in rtl_synth_config
        assert "PDK_ROOT" in rtl_synth_config["environment"]

    def test_environment_has_pdk_variable(self, rtl_synth_config: dict) -> None:
        """Test that PDK environment variable is set to sky130A."""
        assert rtl_synth_config["environment"]["PDK"] == "sky130A"


class TestRtlGpuConfig:
    """Tests for RTL GPU acceleration runner configuration."""

    def test_config_file_exists(self, config_dir: Path) -> None:
        """Test that rtl-gpu.yml config file exists."""
        config_path = config_dir / "rtl-gpu.yml"
        assert config_path.exists(), f"Config file not found: {config_path}"

    def test_instance_type_is_g6e(self, rtl_gpu_config: dict) -> None:
        """Test that instance type is g6e.xlarge for GPU."""
        assert rtl_gpu_config["instance"]["type"] == "g6e.xlarge"

    def test_nvidia_section_exists(self, rtl_gpu_config: dict) -> None:
        """Test that nvidia section exists for GPU config."""
        assert "nvidia" in rtl_gpu_config

    def test_cuda_version_specified(self, rtl_gpu_config: dict) -> None:
        """Test that CUDA version is specified."""
        assert "cuda_version" in rtl_gpu_config["nvidia"]

    def test_rtlflow_tool_specified(self, rtl_gpu_config: dict) -> None:
        """Test that RTLflow is specified in tools."""
        assert "rtlflow" in rtl_gpu_config["tools"]
        assert "repository" in rtl_gpu_config["tools"]["rtlflow"]

    def test_environment_has_cuda_home(self, rtl_gpu_config: dict) -> None:
        """Test that CUDA_HOME environment variable is set."""
        assert "environment" in rtl_gpu_config
        assert "CUDA_HOME" in rtl_gpu_config["environment"]


class TestDockerfileExists:
    """Tests for Dockerfile existence."""

    def test_dockerfile_sim_exists(self, dockerfile_dir: Path) -> None:
        """Test that Dockerfile.sim exists."""
        dockerfile = dockerfile_dir / "Dockerfile.sim"
        assert dockerfile.exists(), f"Dockerfile not found: {dockerfile}"

    def test_dockerfile_synth_exists(self, dockerfile_dir: Path) -> None:
        """Test that Dockerfile.synth exists."""
        dockerfile = dockerfile_dir / "Dockerfile.synth"
        assert dockerfile.exists(), f"Dockerfile not found: {dockerfile}"

    def test_dockerfile_gpu_exists(self, dockerfile_dir: Path) -> None:
        """Test that Dockerfile.gpu exists."""
        dockerfile = dockerfile_dir / "Dockerfile.gpu"
        assert dockerfile.exists(), f"Dockerfile not found: {dockerfile}"


class TestDockerfileSyntax:
    """Tests for Dockerfile syntax validation."""

    def test_dockerfile_sim_has_from(self, dockerfile_dir: Path) -> None:
        """Test that Dockerfile.sim has FROM instruction."""
        dockerfile = dockerfile_dir / "Dockerfile.sim"
        content = dockerfile.read_text()
        assert "FROM " in content

    def test_dockerfile_sim_has_runner_user(self, dockerfile_dir: Path) -> None:
        """Test that Dockerfile.sim creates github-runner user."""
        dockerfile = dockerfile_dir / "Dockerfile.sim"
        content = dockerfile.read_text()
        assert "github-runner" in content

    def test_dockerfile_synth_has_openlane(self, dockerfile_dir: Path) -> None:
        """Test that Dockerfile.synth installs OpenLane."""
        dockerfile = dockerfile_dir / "Dockerfile.synth"
        content = dockerfile.read_text()
        assert "openlane" in content.lower()

    def test_dockerfile_gpu_has_cuda_base(self, dockerfile_dir: Path) -> None:
        """Test that Dockerfile.gpu uses CUDA base image."""
        dockerfile = dockerfile_dir / "Dockerfile.gpu"
        content = dockerfile.read_text()
        assert "nvidia/cuda" in content or "cuda" in content.lower()

    def test_dockerfile_sim_has_verilator(self, dockerfile_dir: Path) -> None:
        """Test that Dockerfile.sim installs Verilator."""
        dockerfile = dockerfile_dir / "Dockerfile.sim"
        content = dockerfile.read_text()
        assert "verilator" in content.lower()


class TestVersionExtraction:
    """Tests for version extraction from configs."""

    def test_extract_chipyard_version(self, rtl_sim_config: dict) -> None:
        """Test extracting Chipyard version."""
        version = rtl_sim_config["tools"]["chipyard"]["version"]
        # Version should be a valid semver or tag
        assert version is not None
        assert len(version) > 0

    def test_extract_openlane_version(self, rtl_synth_config: dict) -> None:
        """Test extracting OpenLane version."""
        version = rtl_synth_config["tools"]["openlane"]["version"]
        assert version is not None
        assert len(version) > 0

    def test_extract_cuda_version(self, rtl_gpu_config: dict) -> None:
        """Test extracting CUDA version."""
        version = rtl_gpu_config["nvidia"]["cuda_version"]
        assert version is not None
        # CUDA version should be like "12.4"
        parts = version.split(".")
        assert len(parts) >= 1
