"""
Unit tests for lib/python/runner_labels.py.

Tests follow the testing pyramid principles from CLAUDE.md:
- Atomic tests: each test verifies one thing
- Single responsibility: one assertion per test
- Full coverage: every function, every branch
"""

import sys
from pathlib import Path

import pytest

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib" / "python"))

from runner_labels import (
    ECS_FARGATE_CONFIG,
    INSTANCE_TYPE_MAP,
    LabelParseError,
    LabelValidationError,
    ParsedLabels,
    get_ecs_config,
    get_instance_type,
    get_runner_id_number,
    get_task_architecture,
    is_spot,
    parse_labels,
    validate_labels,
)


class TestParseLabelsValidEcsInput:
    """Tests for parse_labels with valid ECS input."""

    def test_parses_ecs_fargate_x86_spot_platform(self) -> None:
        """parse_labels extracts correct platform for ECS."""
        result = parse_labels(["ecs", "fargate", "x86", "spot", "runner-12345"])
        assert result.platform == "ecs"

    def test_parses_ecs_fargate_x86_spot_compute(self) -> None:
        """parse_labels extracts correct compute for ECS."""
        result = parse_labels(["ecs", "fargate", "x86", "spot", "runner-12345"])
        assert result.compute == "fargate"

    def test_parses_ecs_fargate_x86_spot_architecture(self) -> None:
        """parse_labels extracts correct architecture for ECS."""
        result = parse_labels(["ecs", "fargate", "x86", "spot", "runner-12345"])
        assert result.architecture == "x86"

    def test_parses_ecs_fargate_arm_architecture(self) -> None:
        """parse_labels extracts arm architecture for ECS."""
        result = parse_labels(["ecs", "fargate", "arm", "spot", "runner-12345"])
        assert result.architecture == "arm"

    def test_parses_ecs_fargate_pricing(self) -> None:
        """parse_labels extracts correct pricing for ECS."""
        result = parse_labels(["ecs", "fargate", "x86", "spot", "runner-12345"])
        assert result.pricing == "spot"

    def test_parses_ecs_fargate_runner_id(self) -> None:
        """parse_labels extracts correct runner_id for ECS."""
        result = parse_labels(["ecs", "fargate", "x86", "spot", "runner-12345"])
        assert result.runner_id == "runner-12345"


class TestParseLabelsValidEc2WithArchInput:
    """Tests for parse_labels with valid EC2 input requiring architecture."""

    def test_parses_ec2_general_purpose_intel_platform(self) -> None:
        """parse_labels extracts correct platform for EC2 general-purpose."""
        result = parse_labels(
            ["ec2", "general-purpose", "intel", "spot", "runner-1"]
        )
        assert result.platform == "ec2"

    def test_parses_ec2_general_purpose_intel_compute(self) -> None:
        """parse_labels extracts correct compute for EC2 general-purpose."""
        result = parse_labels(
            ["ec2", "general-purpose", "intel", "spot", "runner-1"]
        )
        assert result.compute == "general-purpose"

    def test_parses_ec2_general_purpose_intel_architecture(self) -> None:
        """parse_labels extracts intel architecture for EC2."""
        result = parse_labels(
            ["ec2", "general-purpose", "intel", "spot", "runner-1"]
        )
        assert result.architecture == "intel"

    def test_parses_ec2_general_purpose_amd_architecture(self) -> None:
        """parse_labels extracts amd architecture for EC2."""
        result = parse_labels(
            ["ec2", "general-purpose", "amd", "spot", "runner-1"]
        )
        assert result.architecture == "amd"

    def test_parses_ec2_general_purpose_arm_architecture(self) -> None:
        """parse_labels extracts arm architecture for EC2."""
        result = parse_labels(
            ["ec2", "general-purpose", "arm", "spot", "runner-1"]
        )
        assert result.architecture == "arm"

    def test_parses_ec2_memory_optimized_intel_compute(self) -> None:
        """parse_labels extracts memory-optimized compute."""
        result = parse_labels(
            ["ec2", "memory-optimized", "intel", "on-demand", "runner-1"]
        )
        assert result.compute == "memory-optimized"


class TestParseLabelsValidEc2WithoutArchInput:
    """Tests for parse_labels with valid EC2 input forbidding architecture."""

    def test_parses_ec2_gpu_platform(self) -> None:
        """parse_labels extracts platform for EC2 GPU."""
        result = parse_labels(["ec2", "gpu", "spot", "runner-1"])
        assert result.platform == "ec2"

    def test_parses_ec2_gpu_compute(self) -> None:
        """parse_labels extracts compute for EC2 GPU."""
        result = parse_labels(["ec2", "gpu", "spot", "runner-1"])
        assert result.compute == "gpu"

    def test_parses_ec2_gpu_no_architecture(self) -> None:
        """parse_labels has None architecture for EC2 GPU."""
        result = parse_labels(["ec2", "gpu", "spot", "runner-1"])
        assert result.architecture is None

    def test_parses_ec2_fpga_compute(self) -> None:
        """parse_labels extracts compute for EC2 FPGA."""
        result = parse_labels(["ec2", "fpga", "on-demand", "runner-1"])
        assert result.compute == "fpga"

    def test_parses_ec2_fpga_no_architecture(self) -> None:
        """parse_labels has None architecture for EC2 FPGA."""
        result = parse_labels(["ec2", "fpga", "on-demand", "runner-1"])
        assert result.architecture is None


class TestParseLabelsLabelOrder:
    """Tests for parse_labels handling label order."""

    def test_parses_labels_in_any_order(self) -> None:
        """parse_labels handles labels in any order."""
        result = parse_labels(["runner-42", "spot", "x86", "fargate", "ecs"])
        assert result.platform == "ecs"

    def test_parses_labels_with_extra_labels(self) -> None:
        """parse_labels ignores unrecognized labels."""
        result = parse_labels(
            ["ecs", "fargate", "x86", "spot", "runner-1", "extra", "labels"]
        )
        assert result.platform == "ecs"


class TestParseLabelsInvalidInput:
    """Tests for parse_labels with invalid input."""

    def test_raises_on_empty_list(self) -> None:
        """parse_labels raises LabelParseError on empty list."""
        with pytest.raises(LabelParseError, match="cannot be empty"):
            parse_labels([])

    def test_raises_on_missing_platform(self) -> None:
        """parse_labels raises LabelParseError when platform is missing."""
        with pytest.raises(LabelParseError, match="Missing platform"):
            parse_labels(["fargate", "x86", "spot", "runner-1"])

    def test_raises_on_missing_compute(self) -> None:
        """parse_labels raises LabelParseError when compute is missing."""
        with pytest.raises(LabelParseError, match="Missing compute"):
            parse_labels(["ecs", "x86", "spot", "runner-1"])

    def test_raises_on_missing_pricing(self) -> None:
        """parse_labels raises LabelParseError when pricing is missing."""
        with pytest.raises(LabelParseError, match="Missing pricing"):
            parse_labels(["ecs", "fargate", "x86", "runner-1"])

    def test_raises_on_missing_runner_id(self) -> None:
        """parse_labels raises LabelParseError when runner_id is missing."""
        with pytest.raises(LabelParseError, match="Missing runner ID"):
            parse_labels(["ecs", "fargate", "x86", "spot"])

    def test_raises_on_invalid_runner_id_format(self) -> None:
        """parse_labels raises LabelParseError on invalid runner_id format."""
        with pytest.raises(LabelParseError, match="Missing runner ID"):
            parse_labels(["ecs", "fargate", "x86", "spot", "runner-abc"])

    def test_raises_on_multiple_platforms(self) -> None:
        """parse_labels raises LabelParseError with multiple platforms."""
        with pytest.raises(LabelParseError, match="Multiple platform"):
            parse_labels(["ecs", "ec2", "fargate", "x86", "spot", "runner-1"])

    def test_raises_on_multiple_compute_types(self) -> None:
        """parse_labels raises LabelParseError with multiple compute types."""
        with pytest.raises(LabelParseError, match="Multiple compute"):
            parse_labels(
                ["ec2", "general-purpose", "memory-optimized", "intel", "spot", "runner-1"]
            )

    def test_raises_on_multiple_pricing_models(self) -> None:
        """parse_labels raises LabelParseError with multiple pricing models."""
        with pytest.raises(LabelParseError, match="Multiple pricing"):
            parse_labels(["ecs", "fargate", "x86", "spot", "on-demand", "runner-1"])

    def test_raises_on_multiple_architectures(self) -> None:
        """parse_labels raises LabelParseError with multiple architectures."""
        with pytest.raises(LabelParseError, match="Multiple architecture"):
            parse_labels(["ecs", "fargate", "x86", "arm", "spot", "runner-1"])


class TestValidateLabelsEcs:
    """Tests for validate_labels with ECS labels."""

    def test_accepts_ecs_fargate_x86_spot(self) -> None:
        """validate_labels accepts ecs + fargate + x86 + spot."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "x86")
        validate_labels(parsed)
        assert True  # Explicit pass

    def test_accepts_ecs_fargate_arm_on_demand(self) -> None:
        """validate_labels accepts ecs + fargate + arm + on-demand."""
        parsed = ParsedLabels("ecs", "fargate", "on-demand", "runner-1", "arm")
        validate_labels(parsed)
        assert True  # Explicit pass

    def test_rejects_ecs_missing_architecture(self) -> None:
        """validate_labels rejects ecs without architecture."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", None)
        with pytest.raises(LabelValidationError, match="requires architecture"):
            validate_labels(parsed)

    def test_rejects_ecs_invalid_architecture(self) -> None:
        """validate_labels rejects ecs with invalid architecture."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "intel")
        with pytest.raises(LabelValidationError, match="only supports architectures"):
            validate_labels(parsed)

    def test_rejects_ecs_with_ec2_compute(self) -> None:
        """validate_labels rejects ecs + general-purpose."""
        parsed = ParsedLabels("ecs", "general-purpose", "spot", "runner-1", "x86")
        with pytest.raises(LabelValidationError, match="ECS platform only"):
            validate_labels(parsed)


class TestValidateLabelsEc2WithArch:
    """Tests for validate_labels with EC2 labels requiring architecture."""

    def test_accepts_ec2_general_purpose_intel(self) -> None:
        """validate_labels accepts ec2 + general-purpose + intel."""
        parsed = ParsedLabels("ec2", "general-purpose", "spot", "runner-1", "intel")
        validate_labels(parsed)
        assert True  # Explicit pass

    def test_accepts_ec2_general_purpose_amd(self) -> None:
        """validate_labels accepts ec2 + general-purpose + amd."""
        parsed = ParsedLabels("ec2", "general-purpose", "spot", "runner-1", "amd")
        validate_labels(parsed)
        assert True  # Explicit pass

    def test_accepts_ec2_general_purpose_arm(self) -> None:
        """validate_labels accepts ec2 + general-purpose + arm."""
        parsed = ParsedLabels("ec2", "general-purpose", "spot", "runner-1", "arm")
        validate_labels(parsed)
        assert True  # Explicit pass

    def test_accepts_ec2_memory_optimized_intel(self) -> None:
        """validate_labels accepts ec2 + memory-optimized + intel."""
        parsed = ParsedLabels("ec2", "memory-optimized", "on-demand", "runner-1", "intel")
        validate_labels(parsed)
        assert True  # Explicit pass

    def test_rejects_ec2_general_purpose_missing_arch(self) -> None:
        """validate_labels rejects ec2 + general-purpose without arch."""
        parsed = ParsedLabels("ec2", "general-purpose", "spot", "runner-1", None)
        with pytest.raises(LabelValidationError, match="requires architecture"):
            validate_labels(parsed)

    def test_rejects_ec2_general_purpose_invalid_arch(self) -> None:
        """validate_labels rejects ec2 + general-purpose + x86."""
        parsed = ParsedLabels("ec2", "general-purpose", "spot", "runner-1", "x86")
        with pytest.raises(LabelValidationError, match="only supports architectures"):
            validate_labels(parsed)


class TestValidateLabelsEc2WithoutArch:
    """Tests for validate_labels with EC2 labels forbidding architecture."""

    def test_accepts_ec2_gpu_no_arch(self) -> None:
        """validate_labels accepts ec2 + gpu without architecture."""
        parsed = ParsedLabels("ec2", "gpu", "spot", "runner-1", None)
        validate_labels(parsed)
        assert True  # Explicit pass

    def test_accepts_ec2_fpga_no_arch(self) -> None:
        """validate_labels accepts ec2 + fpga without architecture."""
        parsed = ParsedLabels("ec2", "fpga", "on-demand", "runner-1", None)
        validate_labels(parsed)
        assert True  # Explicit pass

    def test_rejects_ec2_gpu_with_arch(self) -> None:
        """validate_labels rejects ec2 + gpu with architecture."""
        parsed = ParsedLabels("ec2", "gpu", "spot", "runner-1", "intel")
        with pytest.raises(LabelValidationError, match="does not support"):
            validate_labels(parsed)

    def test_rejects_ec2_fpga_with_arch(self) -> None:
        """validate_labels rejects ec2 + fpga with architecture."""
        parsed = ParsedLabels("ec2", "fpga", "spot", "runner-1", "amd")
        with pytest.raises(LabelValidationError, match="does not support"):
            validate_labels(parsed)

    def test_rejects_ec2_with_fargate(self) -> None:
        """validate_labels rejects ec2 + fargate."""
        parsed = ParsedLabels("ec2", "fargate", "spot", "runner-1", "x86")
        with pytest.raises(LabelValidationError, match="EC2 platform only"):
            validate_labels(parsed)


class TestGetInstanceType:
    """Tests for get_instance_type function."""

    def test_returns_m8i_for_general_purpose_intel(self) -> None:
        """get_instance_type returns m8i.4xlarge for general-purpose + intel."""
        parsed = ParsedLabels("ec2", "general-purpose", "spot", "runner-1", "intel")
        assert get_instance_type(parsed) == "m8i.4xlarge"

    def test_returns_m8a_for_general_purpose_amd(self) -> None:
        """get_instance_type returns m8a.4xlarge for general-purpose + amd."""
        parsed = ParsedLabels("ec2", "general-purpose", "spot", "runner-1", "amd")
        assert get_instance_type(parsed) == "m8a.4xlarge"

    def test_returns_m8g_for_general_purpose_arm(self) -> None:
        """get_instance_type returns m8g.4xlarge for general-purpose + arm."""
        parsed = ParsedLabels("ec2", "general-purpose", "spot", "runner-1", "arm")
        assert get_instance_type(parsed) == "m8g.4xlarge"

    def test_returns_r8i_for_memory_optimized_intel(self) -> None:
        """get_instance_type returns r8i.4xlarge for memory-optimized + intel."""
        parsed = ParsedLabels("ec2", "memory-optimized", "on-demand", "runner-1", "intel")
        assert get_instance_type(parsed) == "r8i.4xlarge"

    def test_returns_r8a_for_memory_optimized_amd(self) -> None:
        """get_instance_type returns r8a.4xlarge for memory-optimized + amd."""
        parsed = ParsedLabels("ec2", "memory-optimized", "spot", "runner-1", "amd")
        assert get_instance_type(parsed) == "r8a.4xlarge"

    def test_returns_r8g_for_memory_optimized_arm(self) -> None:
        """get_instance_type returns r8g.4xlarge for memory-optimized + arm."""
        parsed = ParsedLabels("ec2", "memory-optimized", "spot", "runner-1", "arm")
        assert get_instance_type(parsed) == "r8g.4xlarge"

    def test_returns_g6e_for_gpu(self) -> None:
        """get_instance_type returns g6e.2xlarge for GPU."""
        parsed = ParsedLabels("ec2", "gpu", "spot", "runner-1", None)
        assert get_instance_type(parsed) == "g6e.2xlarge"

    def test_returns_f2_for_fpga(self) -> None:
        """get_instance_type returns f2.12xlarge for FPGA."""
        parsed = ParsedLabels("ec2", "fpga", "on-demand", "runner-1", None)
        assert get_instance_type(parsed) == "f2.12xlarge"

    def test_returns_none_for_ecs_fargate(self) -> None:
        """get_instance_type returns None for ECS Fargate."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "x86")
        assert get_instance_type(parsed) is None

    def test_instance_type_map_has_general_purpose_intel(self) -> None:
        """INSTANCE_TYPE_MAP contains general-purpose + intel."""
        assert ("general-purpose", "intel") in INSTANCE_TYPE_MAP

    def test_instance_type_map_has_general_purpose_amd(self) -> None:
        """INSTANCE_TYPE_MAP contains general-purpose + amd."""
        assert ("general-purpose", "amd") in INSTANCE_TYPE_MAP

    def test_instance_type_map_has_general_purpose_arm(self) -> None:
        """INSTANCE_TYPE_MAP contains general-purpose + arm."""
        assert ("general-purpose", "arm") in INSTANCE_TYPE_MAP

    def test_instance_type_map_has_memory_optimized_intel(self) -> None:
        """INSTANCE_TYPE_MAP contains memory-optimized + intel."""
        assert ("memory-optimized", "intel") in INSTANCE_TYPE_MAP

    def test_instance_type_map_has_memory_optimized_amd(self) -> None:
        """INSTANCE_TYPE_MAP contains memory-optimized + amd."""
        assert ("memory-optimized", "amd") in INSTANCE_TYPE_MAP

    def test_instance_type_map_has_memory_optimized_arm(self) -> None:
        """INSTANCE_TYPE_MAP contains memory-optimized + arm."""
        assert ("memory-optimized", "arm") in INSTANCE_TYPE_MAP

    def test_instance_type_map_has_gpu(self) -> None:
        """INSTANCE_TYPE_MAP contains gpu."""
        assert ("gpu", None) in INSTANCE_TYPE_MAP

    def test_instance_type_map_has_fpga(self) -> None:
        """INSTANCE_TYPE_MAP contains fpga."""
        assert ("fpga", None) in INSTANCE_TYPE_MAP


class TestGetTaskArchitecture:
    """Tests for get_task_architecture function."""

    def test_returns_x86_64_for_x86(self) -> None:
        """get_task_architecture returns X86_64 for x86."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "x86")
        assert get_task_architecture(parsed) == "X86_64"

    def test_returns_arm64_for_arm(self) -> None:
        """get_task_architecture returns ARM64 for arm."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "arm")
        assert get_task_architecture(parsed) == "ARM64"

    def test_returns_none_for_ec2(self) -> None:
        """get_task_architecture returns None for EC2."""
        parsed = ParsedLabels("ec2", "general-purpose", "spot", "runner-1", "intel")
        assert get_task_architecture(parsed) is None

    def test_returns_none_for_no_architecture(self) -> None:
        """get_task_architecture returns None when architecture is None."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", None)
        assert get_task_architecture(parsed) is None


class TestGetEcsConfig:
    """Tests for get_ecs_config function."""

    def test_returns_config_for_fargate(self) -> None:
        """get_ecs_config returns config dict for Fargate."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "x86")
        config = get_ecs_config(parsed)
        assert config is not None

    def test_returns_correct_cpu_for_fargate(self) -> None:
        """get_ecs_config returns correct CPU for Fargate."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "arm")
        config = get_ecs_config(parsed)
        if config is None:
            pytest.fail("Expected config to be returned for ECS Fargate")
        assert config["cpu"] == "4096"

    def test_returns_correct_memory_for_fargate(self) -> None:
        """get_ecs_config returns correct memory for Fargate."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "x86")
        config = get_ecs_config(parsed)
        if config is None:
            pytest.fail("Expected config to be returned for ECS Fargate")
        assert config["memory"] == "16384"

    def test_returns_none_for_ec2(self) -> None:
        """get_ecs_config returns None for EC2 platform."""
        parsed = ParsedLabels("ec2", "general-purpose", "on-demand", "runner-1", "intel")
        assert get_ecs_config(parsed) is None

    def test_returns_copy_not_reference(self) -> None:
        """get_ecs_config returns a copy, not the original dict."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "x86")
        config = get_ecs_config(parsed)
        if config is None:
            pytest.fail("Expected config to be returned for ECS Fargate")
        config["cpu"] = "modified"
        assert ECS_FARGATE_CONFIG["cpu"] == "4096"


class TestIsSpot:
    """Tests for is_spot function."""

    def test_returns_true_for_ecs_spot(self) -> None:
        """is_spot returns True for ECS with spot pricing."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "x86")
        assert is_spot(parsed) is True

    def test_returns_false_for_ecs_on_demand(self) -> None:
        """is_spot returns False for ECS with on-demand pricing."""
        parsed = ParsedLabels("ecs", "fargate", "on-demand", "runner-1", "arm")
        assert is_spot(parsed) is False

    def test_returns_true_for_ec2_spot(self) -> None:
        """is_spot returns True for EC2 with spot pricing."""
        parsed = ParsedLabels("ec2", "general-purpose", "spot", "runner-1", "intel")
        assert is_spot(parsed) is True

    def test_returns_false_for_ec2_on_demand(self) -> None:
        """is_spot returns False for EC2 with on-demand pricing."""
        parsed = ParsedLabels("ec2", "memory-optimized", "on-demand", "runner-1", "arm")
        assert is_spot(parsed) is False


class TestGetRunnerIdNumber:
    """Tests for get_runner_id_number function."""

    def test_extracts_number_from_runner_id(self) -> None:
        """get_runner_id_number extracts numeric ID."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-12345", "x86")
        assert get_runner_id_number(parsed) == 12345

    def test_extracts_single_digit_number(self) -> None:
        """get_runner_id_number extracts single digit ID."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "arm")
        assert get_runner_id_number(parsed) == 1

    def test_extracts_large_number(self) -> None:
        """get_runner_id_number extracts large ID."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-9999999999", "x86")
        assert get_runner_id_number(parsed) == 9999999999

    def test_raises_on_invalid_format(self) -> None:
        """get_runner_id_number raises on invalid runner_id format."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "invalid", "x86")
        with pytest.raises(LabelParseError, match="Invalid runner ID"):
            get_runner_id_number(parsed)


class TestParsedLabelsDataclass:
    """Tests for ParsedLabels dataclass."""

    def test_creates_instance_with_platform(self) -> None:
        """ParsedLabels creates instance with correct platform."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "x86")
        assert parsed.platform == "ecs"

    def test_creates_instance_with_compute(self) -> None:
        """ParsedLabels creates instance with correct compute."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "x86")
        assert parsed.compute == "fargate"

    def test_creates_instance_with_pricing(self) -> None:
        """ParsedLabels creates instance with correct pricing."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "x86")
        assert parsed.pricing == "spot"

    def test_creates_instance_with_runner_id(self) -> None:
        """ParsedLabels creates instance with correct runner_id."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "x86")
        assert parsed.runner_id == "runner-1"

    def test_creates_instance_with_architecture(self) -> None:
        """ParsedLabels creates instance with correct architecture."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1", "x86")
        assert parsed.architecture == "x86"

    def test_creates_instance_with_default_architecture(self) -> None:
        """ParsedLabels creates instance with default None architecture."""
        parsed = ParsedLabels("ec2", "gpu", "spot", "runner-1")
        assert parsed.architecture is None

    def test_instances_are_equal_with_same_values(self) -> None:
        """ParsedLabels instances with same values are equal."""
        parsed1 = ParsedLabels("ecs", "fargate", "spot", "runner-1", "x86")
        parsed2 = ParsedLabels("ecs", "fargate", "spot", "runner-1", "x86")
        assert parsed1 == parsed2

    def test_instances_are_not_equal_with_different_arch(self) -> None:
        """ParsedLabels instances with different architecture are not equal."""
        parsed1 = ParsedLabels("ecs", "fargate", "spot", "runner-1", "x86")
        parsed2 = ParsedLabels("ecs", "fargate", "spot", "runner-1", "arm")
        assert parsed1 != parsed2
