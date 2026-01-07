"""Comprehensive tests for runner_labels module."""
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import os

from runner_labels import (
    ParsedLabels,
    LabelParseError,
    LabelValidationError,
    parse_labels,
    validate_labels,
    get_instance_type,
    get_ecs_config,
    get_task_architecture,
    is_spot,
    get_runner_id_number,
    get_runner_type_from_labels,
    _find_config_file_from_paths,
    PLATFORMS,
    PRICING_MODELS,
    ECS_COMPUTE,
    ECS_ARCHITECTURES,
    EC2_COMPUTE,
    EC2_ARCHITECTURES,
    EC2_COMPUTE_REQUIRES_ARCH,
    EC2_COMPUTE_FORBIDS_ARCH,
    COMPUTE_TYPES,
    ALL_ARCHITECTURES,
    INSTANCE_TYPE_MAP,
    ECS_TASK_ARCHITECTURE_MAP,
    ECS_FARGATE_CONFIG,
    RUNNER_ID_PATTERN,
    DEFAULT_ECS_ARCH,
    DEFAULT_EC2_ARCH,
    DEFAULT_ECS_COMPUTE,
    DEFAULT_EC2_COMPUTE,
    DEFAULT_PRICING,
    DEFAULT_RUNNER_ID,
)


# === Exception Classes ===


class TestLabelParseError:
    """Tests for LabelParseError exception class."""

    def test_is_exception(self):
        """LabelParseError should be a subclass of Exception."""
        assert issubclass(LabelParseError, Exception)

    def test_can_be_raised(self):
        """LabelParseError can be raised with a message."""
        with pytest.raises(LabelParseError, match="parse error"):
            raise LabelParseError("parse error")


class TestLabelValidationError:
    """Tests for LabelValidationError exception class."""

    def test_is_exception(self):
        """LabelValidationError should be a subclass of Exception."""
        assert issubclass(LabelValidationError, Exception)

    def test_can_be_raised(self):
        """LabelValidationError can be raised with a message."""
        with pytest.raises(LabelValidationError, match="validation error"):
            raise LabelValidationError("validation error")


# === ParsedLabels Dataclass ===


class TestParsedLabels:
    """Tests for ParsedLabels dataclass."""

    def test_required_fields_platform(self):
        """ParsedLabels stores platform correctly."""
        labels = ParsedLabels(
            platform="ecs",
            compute="fargate",
            pricing="spot",
            runner_id="runner-12345",
        )
        assert labels.platform == "ecs"

    def test_required_fields_compute(self):
        """ParsedLabels stores compute correctly."""
        labels = ParsedLabels(
            platform="ecs",
            compute="fargate",
            pricing="spot",
            runner_id="runner-12345",
        )
        assert labels.compute == "fargate"

    def test_required_fields_pricing(self):
        """ParsedLabels stores pricing correctly."""
        labels = ParsedLabels(
            platform="ecs",
            compute="fargate",
            pricing="spot",
            runner_id="runner-12345",
        )
        assert labels.pricing == "spot"

    def test_required_fields_runner_id(self):
        """ParsedLabels stores runner_id correctly."""
        labels = ParsedLabels(
            platform="ecs",
            compute="fargate",
            pricing="spot",
            runner_id="runner-12345",
        )
        assert labels.runner_id == "runner-12345"

    def test_architecture_defaults_to_none(self):
        """ParsedLabels has architecture default to None."""
        labels = ParsedLabels(
            platform="ecs",
            compute="fargate",
            pricing="spot",
            runner_id="runner-12345",
        )
        assert labels.architecture is None

    def test_optional_architecture(self):
        """ParsedLabels can include optional architecture."""
        labels = ParsedLabels(
            platform="ecs",
            compute="fargate",
            pricing="spot",
            runner_id="runner-12345",
            architecture="x86",
        )
        assert labels.architecture == "x86"


# === Configuration Constants ===


class TestConfigurationConstants:
    """Tests for configuration constants loaded from JSON."""

    def test_platforms_contains_ecs(self):
        """PLATFORMS should contain ecs."""
        assert "ecs" in PLATFORMS

    def test_platforms_contains_ec2(self):
        """PLATFORMS should contain ec2."""
        assert "ec2" in PLATFORMS

    def test_pricing_models_contains_spot(self):
        """PRICING_MODELS should contain spot."""
        assert "spot" in PRICING_MODELS

    def test_pricing_models_contains_on_demand(self):
        """PRICING_MODELS should contain on-demand."""
        assert "on-demand" in PRICING_MODELS

    def test_ecs_compute_contains_fargate(self):
        """ECS_COMPUTE should contain fargate."""
        assert "fargate" in ECS_COMPUTE

    def test_ecs_architectures_contains_x86(self):
        """ECS_ARCHITECTURES should contain x86."""
        assert "x86" in ECS_ARCHITECTURES

    def test_ecs_architectures_contains_arm(self):
        """ECS_ARCHITECTURES should contain arm."""
        assert "arm" in ECS_ARCHITECTURES

    def test_ec2_compute_not_empty(self):
        """EC2_COMPUTE should not be empty."""
        assert len(EC2_COMPUTE) > 0

    def test_compute_types_union(self):
        """COMPUTE_TYPES should be union of ECS and EC2 compute."""
        assert COMPUTE_TYPES == ECS_COMPUTE | EC2_COMPUTE

    def test_all_architectures_union(self):
        """ALL_ARCHITECTURES should be union of ECS and EC2 architectures."""
        assert ALL_ARCHITECTURES == ECS_ARCHITECTURES | EC2_ARCHITECTURES

    def test_ecs_fargate_config_has_cpu(self):
        """ECS_FARGATE_CONFIG should have cpu."""
        assert "cpu" in ECS_FARGATE_CONFIG

    def test_ecs_fargate_config_has_memory(self):
        """ECS_FARGATE_CONFIG should have memory."""
        assert "memory" in ECS_FARGATE_CONFIG

    def test_runner_id_pattern_matches_valid_format(self):
        """RUNNER_ID_PATTERN should match valid runner ID format."""
        match = RUNNER_ID_PATTERN.match("runner-12345")
        assert match is not None

    def test_runner_id_pattern_captures_number(self):
        """RUNNER_ID_PATTERN should capture the numeric portion."""
        match = RUNNER_ID_PATTERN.match("runner-12345")
        assert match.group(1) == "12345"

    def test_runner_id_pattern_rejects_invalid_prefix(self):
        """RUNNER_ID_PATTERN should not match invalid prefix."""
        assert RUNNER_ID_PATTERN.match("invalid-12345") is None

    def test_runner_id_pattern_rejects_non_numeric_suffix(self):
        """RUNNER_ID_PATTERN should not match non-numeric suffix."""
        assert RUNNER_ID_PATTERN.match("runner-abc") is None


# === parse_labels Function ===


class TestParseLabels:
    """Tests for parse_labels function."""

    def test_parse_ecs_fargate_labels_platform(self):
        """parse_labels parses ECS Fargate platform correctly."""
        labels = ["ecs", "fargate", "x86", "spot", "runner-12345"]
        result = parse_labels(labels)
        assert result.platform == "ecs"

    def test_parse_ecs_fargate_labels_compute(self):
        """parse_labels parses ECS Fargate compute correctly."""
        labels = ["ecs", "fargate", "x86", "spot", "runner-12345"]
        result = parse_labels(labels)
        assert result.compute == "fargate"

    def test_parse_ecs_fargate_labels_architecture(self):
        """parse_labels parses ECS Fargate architecture correctly."""
        labels = ["ecs", "fargate", "x86", "spot", "runner-12345"]
        result = parse_labels(labels)
        assert result.architecture == "x86"

    def test_parse_ecs_fargate_labels_pricing(self):
        """parse_labels parses ECS Fargate pricing correctly."""
        labels = ["ecs", "fargate", "x86", "spot", "runner-12345"]
        result = parse_labels(labels)
        assert result.pricing == "spot"

    def test_parse_ecs_fargate_labels_runner_id(self):
        """parse_labels parses ECS Fargate runner ID correctly."""
        labels = ["ecs", "fargate", "x86", "spot", "runner-12345"]
        result = parse_labels(labels)
        assert result.runner_id == "runner-12345"

    def test_parse_ec2_labels_platform(self):
        """parse_labels parses EC2 platform correctly."""
        labels = ["ec2", "general-purpose", "intel", "on-demand", "runner-99999"]
        result = parse_labels(labels)
        assert result.platform == "ec2"

    def test_parse_ec2_labels_compute(self):
        """parse_labels parses EC2 compute correctly."""
        labels = ["ec2", "general-purpose", "intel", "on-demand", "runner-99999"]
        result = parse_labels(labels)
        assert result.compute == "general-purpose"

    def test_parse_ec2_labels_architecture(self):
        """parse_labels parses EC2 architecture correctly."""
        labels = ["ec2", "general-purpose", "intel", "on-demand", "runner-99999"]
        result = parse_labels(labels)
        assert result.architecture == "intel"

    def test_parse_ec2_labels_pricing(self):
        """parse_labels parses EC2 pricing correctly."""
        labels = ["ec2", "general-purpose", "intel", "on-demand", "runner-99999"]
        result = parse_labels(labels)
        assert result.pricing == "on-demand"

    def test_parse_ec2_labels_runner_id(self):
        """parse_labels parses EC2 runner ID correctly."""
        labels = ["ec2", "general-purpose", "intel", "on-demand", "runner-99999"]
        result = parse_labels(labels)
        assert result.runner_id == "runner-99999"

    def test_parse_ec2_gpu_labels_platform(self):
        """parse_labels parses EC2 GPU platform correctly."""
        labels = ["ec2", "gpu", "spot", "runner-12345"]
        result = parse_labels(labels)
        assert result.platform == "ec2"

    def test_parse_ec2_gpu_labels_compute(self):
        """parse_labels parses EC2 GPU compute correctly."""
        labels = ["ec2", "gpu", "spot", "runner-12345"]
        result = parse_labels(labels)
        assert result.compute == "gpu"

    def test_parse_ec2_gpu_labels_architecture_is_none(self):
        """parse_labels parses EC2 GPU without architecture."""
        labels = ["ec2", "gpu", "spot", "runner-12345"]
        result = parse_labels(labels)
        assert result.architecture is None

    def test_empty_labels_raises(self):
        """parse_labels raises LabelParseError for empty list."""
        with pytest.raises(LabelParseError, match="cannot be empty"):
            parse_labels([])

    def test_missing_platform_raises(self):
        """parse_labels raises LabelParseError for missing platform."""
        with pytest.raises(LabelParseError, match="Missing platform"):
            parse_labels(["fargate", "x86", "spot", "runner-12345"])

    def test_multiple_platforms_raises(self):
        """parse_labels raises LabelParseError for multiple platforms."""
        with pytest.raises(LabelParseError, match="Multiple platform"):
            parse_labels(["ecs", "ec2", "fargate", "x86", "spot", "runner-12345"])

    def test_missing_compute_raises(self):
        """parse_labels raises LabelParseError for missing compute."""
        with pytest.raises(LabelParseError, match="Missing compute"):
            parse_labels(["ecs", "x86", "spot", "runner-12345"])

    def test_multiple_compute_raises(self):
        """parse_labels raises LabelParseError for multiple compute types."""
        with pytest.raises(LabelParseError, match="Multiple compute"):
            parse_labels(["ecs", "fargate", "gpu", "x86", "spot", "runner-12345"])

    def test_multiple_architectures_raises(self):
        """parse_labels raises LabelParseError for multiple architectures."""
        with pytest.raises(LabelParseError, match="Multiple architecture"):
            parse_labels(["ecs", "fargate", "x86", "arm", "spot", "runner-12345"])

    def test_missing_pricing_raises(self):
        """parse_labels raises LabelParseError for missing pricing."""
        with pytest.raises(LabelParseError, match="Missing pricing"):
            parse_labels(["ecs", "fargate", "x86", "runner-12345"])

    def test_multiple_pricing_raises(self):
        """parse_labels raises LabelParseError for multiple pricing models."""
        with pytest.raises(LabelParseError, match="Multiple pricing"):
            parse_labels(["ecs", "fargate", "x86", "spot", "on-demand", "runner-12345"])

    def test_missing_runner_id_raises(self):
        """parse_labels raises LabelParseError for missing runner ID."""
        with pytest.raises(LabelParseError, match="Missing runner ID"):
            parse_labels(["ecs", "fargate", "x86", "spot"])

    def test_extra_labels_ignored(self):
        """parse_labels ignores extra unrecognized labels."""
        labels = ["ecs", "fargate", "x86", "spot", "runner-12345", "extra", "labels"]
        result = parse_labels(labels)
        assert result.platform == "ecs"


# === validate_labels Function ===


class TestValidateLabels:
    """Tests for validate_labels function."""

    def test_valid_ecs_fargate_x86(self):
        """validate_labels accepts valid ECS Fargate x86."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture="x86",
            pricing="spot",
            runner_id="runner-12345",
        )
        validate_labels(parsed)  # Should not raise
        assert True  # Explicit pass

    def test_valid_ecs_fargate_arm(self):
        """validate_labels accepts valid ECS Fargate ARM."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture="arm",
            pricing="spot",
            runner_id="runner-12345",
        )
        validate_labels(parsed)  # Should not raise
        assert True  # Explicit pass

    def test_ecs_invalid_compute_raises(self):
        """validate_labels raises for invalid ECS compute type."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="gpu",  # GPU is EC2 only
            architecture="x86",
            pricing="spot",
            runner_id="runner-12345",
        )
        with pytest.raises(LabelValidationError, match="ECS platform only supports"):
            validate_labels(parsed)

    def test_ecs_missing_architecture_raises(self):
        """validate_labels raises for ECS without architecture."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture=None,
            pricing="spot",
            runner_id="runner-12345",
        )
        with pytest.raises(LabelValidationError, match="requires architecture"):
            validate_labels(parsed)

    def test_ecs_invalid_architecture_raises(self):
        """validate_labels raises for ECS with EC2 architecture."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture="intel",  # Intel is EC2 only
            pricing="spot",
            runner_id="runner-12345",
        )
        with pytest.raises(LabelValidationError, match="ECS platform only supports"):
            validate_labels(parsed)

    def test_valid_ec2_with_arch(self):
        """validate_labels accepts valid EC2 with architecture."""
        parsed = ParsedLabels(
            platform="ec2",
            compute="general-purpose",
            architecture="intel",
            pricing="spot",
            runner_id="runner-12345",
        )
        validate_labels(parsed)  # Should not raise
        assert True  # Explicit pass

    def test_valid_ec2_gpu_no_arch(self):
        """validate_labels accepts valid EC2 GPU without architecture."""
        parsed = ParsedLabels(
            platform="ec2",
            compute="gpu",
            architecture=None,
            pricing="spot",
            runner_id="runner-12345",
        )
        validate_labels(parsed)  # Should not raise
        assert True  # Explicit pass

    def test_ec2_invalid_compute_raises(self):
        """validate_labels raises for invalid EC2 compute type."""
        parsed = ParsedLabels(
            platform="ec2",
            compute="fargate",  # Fargate is ECS only
            architecture="intel",
            pricing="spot",
            runner_id="runner-12345",
        )
        with pytest.raises(LabelValidationError, match="EC2 platform only supports"):
            validate_labels(parsed)

    def test_ec2_requires_arch_missing_raises(self):
        """validate_labels raises for EC2 compute requiring arch but missing."""
        if not EC2_COMPUTE_REQUIRES_ARCH:
            pytest.skip("No EC2 compute types require architecture")
        compute = list(EC2_COMPUTE_REQUIRES_ARCH)[0]
        parsed = ParsedLabels(
            platform="ec2",
            compute=compute,
            architecture=None,
            pricing="spot",
            runner_id="runner-12345",
        )
        with pytest.raises(LabelValidationError, match="requires architecture"):
            validate_labels(parsed)

    def test_ec2_forbids_arch_with_arch_raises(self):
        """validate_labels raises for EC2 compute forbidding arch with arch."""
        if not EC2_COMPUTE_FORBIDS_ARCH:
            pytest.skip("No EC2 compute types forbid architecture")
        compute = list(EC2_COMPUTE_FORBIDS_ARCH)[0]
        parsed = ParsedLabels(
            platform="ec2",
            compute=compute,
            architecture="intel",
            pricing="spot",
            runner_id="runner-12345",
        )
        with pytest.raises(LabelValidationError, match="does not support"):
            validate_labels(parsed)

    def test_ec2_invalid_architecture_raises(self):
        """validate_labels raises for EC2 with ECS architecture."""
        if not EC2_COMPUTE_REQUIRES_ARCH:
            pytest.skip("No EC2 compute types require architecture")
        compute = list(EC2_COMPUTE_REQUIRES_ARCH)[0]
        parsed = ParsedLabels(
            platform="ec2",
            compute=compute,
            architecture="x86",  # x86 is ECS-only (EC2 uses intel/amd)
            pricing="spot",
            runner_id="runner-12345",
        )
        # This only raises if x86 is not in EC2_ARCHITECTURES
        if "x86" not in EC2_ARCHITECTURES:
            with pytest.raises(LabelValidationError, match="EC2 platform only supports"):
                validate_labels(parsed)


# === get_instance_type Function ===


class TestGetInstanceType:
    """Tests for get_instance_type function."""

    def test_returns_none_for_ecs(self):
        """get_instance_type returns None for ECS platform."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture="x86",
            pricing="spot",
            runner_id="runner-12345",
        )
        assert get_instance_type(parsed) is None

    def test_returns_instance_type_for_ec2(self):
        """get_instance_type returns instance type for EC2."""
        parsed = ParsedLabels(
            platform="ec2",
            compute="general-purpose",
            architecture="intel",
            pricing="spot",
            runner_id="runner-12345",
        )
        result = get_instance_type(parsed)
        assert result is not None or ("general-purpose", "intel") not in INSTANCE_TYPE_MAP


# === get_ecs_config Function ===


class TestGetEcsConfig:
    """Tests for get_ecs_config function."""

    def test_returns_none_for_ec2(self):
        """get_ecs_config returns None for EC2 platform."""
        parsed = ParsedLabels(
            platform="ec2",
            compute="general-purpose",
            architecture="intel",
            pricing="spot",
            runner_id="runner-12345",
        )
        assert get_ecs_config(parsed) is None

    def test_returns_none_for_ecs_unknown_compute(self):
        """get_ecs_config returns None for ECS with unknown compute type."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="unknown-compute",
            architecture="x86",
            pricing="spot",
            runner_id="runner-12345",
        )
        assert get_ecs_config(parsed) is None

    def test_returns_config_for_fargate(self):
        """get_ecs_config returns config for Fargate."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture="x86",
            pricing="spot",
            runner_id="runner-12345",
        )
        result = get_ecs_config(parsed)
        assert result is not None

    def test_returns_config_with_cpu_key(self):
        """get_ecs_config returns config containing cpu key."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture="x86",
            pricing="spot",
            runner_id="runner-12345",
        )
        result = get_ecs_config(parsed)
        assert "cpu" in result

    def test_returns_config_with_memory_key(self):
        """get_ecs_config returns config containing memory key."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture="x86",
            pricing="spot",
            runner_id="runner-12345",
        )
        result = get_ecs_config(parsed)
        assert "memory" in result

    def test_returns_copy_not_reference(self):
        """get_ecs_config returns a copy, not the original."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture="x86",
            pricing="spot",
            runner_id="runner-12345",
        )
        result = get_ecs_config(parsed)
        result["cpu"] = "modified"
        assert ECS_FARGATE_CONFIG["cpu"] != "modified"


# === get_task_architecture Function ===


class TestGetTaskArchitecture:
    """Tests for get_task_architecture function."""

    def test_returns_none_for_ec2(self):
        """get_task_architecture returns None for EC2 platform."""
        parsed = ParsedLabels(
            platform="ec2",
            compute="general-purpose",
            architecture="intel",
            pricing="spot",
            runner_id="runner-12345",
        )
        assert get_task_architecture(parsed) is None

    def test_returns_none_for_no_architecture(self):
        """get_task_architecture returns None when architecture is None."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture=None,
            pricing="spot",
            runner_id="runner-12345",
        )
        assert get_task_architecture(parsed) is None

    def test_returns_x86_64_for_x86(self):
        """get_task_architecture returns X86_64 for x86 architecture."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture="x86",
            pricing="spot",
            runner_id="runner-12345",
        )
        result = get_task_architecture(parsed)
        assert result == ECS_TASK_ARCHITECTURE_MAP.get("x86")

    def test_returns_arm64_for_arm(self):
        """get_task_architecture returns ARM64 for arm architecture."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture="arm",
            pricing="spot",
            runner_id="runner-12345",
        )
        result = get_task_architecture(parsed)
        assert result == ECS_TASK_ARCHITECTURE_MAP.get("arm")


# === is_spot Function ===


class TestIsSpot:
    """Tests for is_spot function."""

    def test_returns_true_for_spot(self):
        """is_spot returns True for spot pricing."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture="x86",
            pricing="spot",
            runner_id="runner-12345",
        )
        assert is_spot(parsed) is True

    def test_returns_false_for_on_demand(self):
        """is_spot returns False for on-demand pricing."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture="x86",
            pricing="on-demand",
            runner_id="runner-12345",
        )
        assert is_spot(parsed) is False


# === get_runner_id_number Function ===


class TestGetRunnerIdNumber:
    """Tests for get_runner_id_number function."""

    def test_extracts_number(self):
        """get_runner_id_number extracts numeric portion."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture="x86",
            pricing="spot",
            runner_id="runner-12345",
        )
        assert get_runner_id_number(parsed) == 12345

    def test_extracts_large_number(self):
        """get_runner_id_number handles large numbers."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture="x86",
            pricing="spot",
            runner_id="runner-9876543210",
        )
        assert get_runner_id_number(parsed) == 9876543210

    def test_invalid_format_raises(self):
        """get_runner_id_number raises for invalid format."""
        parsed = ParsedLabels(
            platform="ecs",
            compute="fargate",
            architecture="x86",
            pricing="spot",
            runner_id="invalid-12345",
        )
        with pytest.raises(LabelParseError, match="Invalid runner ID"):
            get_runner_id_number(parsed)


# === get_runner_type_from_labels Function ===


class TestGetRunnerTypeFromLabels:
    """Tests for get_runner_type_from_labels function."""

    def test_ec2_returns_ec2_runner_type(self):
        """get_runner_type_from_labels returns ec2 runner type for EC2 labels."""
        labels = ["ec2", "general-purpose", "intel", "spot", "runner-12345"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert runner_type == "ec2"

    def test_ec2_returns_ec2_endpoint_suffix(self):
        """get_runner_type_from_labels returns ec2 endpoint suffix for EC2 labels."""
        labels = ["ec2", "general-purpose", "intel", "spot", "runner-12345"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert endpoint_suffix == "ec2"

    def test_ec2_e2e_returns_ec2_e2e_runner_type(self):
        """get_runner_type_from_labels returns ec2-e2e runner type for EC2 with e2e."""
        labels = ["ec2", "general-purpose", "intel", "spot", "runner-12345", "e2e"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert runner_type == "ec2-e2e"

    def test_ec2_e2e_returns_ec2_endpoint_suffix(self):
        """get_runner_type_from_labels returns ec2 endpoint suffix for EC2 e2e."""
        labels = ["ec2", "general-purpose", "intel", "spot", "runner-12345", "e2e"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert endpoint_suffix == "ec2"

    def test_ecs_returns_fargate_runner_type(self):
        """get_runner_type_from_labels returns fargate runner type for ECS labels."""
        labels = ["ecs", "fargate", "x86", "spot", "runner-12345"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert runner_type == "fargate"

    def test_ecs_returns_ecs_endpoint_suffix(self):
        """get_runner_type_from_labels returns ecs endpoint suffix for ECS labels."""
        labels = ["ecs", "fargate", "x86", "spot", "runner-12345"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert endpoint_suffix == "ecs"

    def test_ecs_e2e_returns_fargate_e2e_runner_type(self):
        """get_runner_type_from_labels returns fargate-e2e runner type for ECS e2e."""
        labels = ["ecs", "fargate", "x86", "spot", "runner-12345", "e2e"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert runner_type == "fargate-e2e"

    def test_ecs_e2e_returns_ecs_endpoint_suffix(self):
        """get_runner_type_from_labels returns ecs endpoint suffix for ECS e2e."""
        labels = ["ecs", "fargate", "x86", "spot", "runner-12345", "e2e"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert endpoint_suffix == "ecs"

    def test_invalid_labels_returns_none_runner_type(self):
        """get_runner_type_from_labels returns None runner type for invalid labels."""
        labels = ["invalid", "labels"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert runner_type is None

    def test_invalid_labels_returns_none_endpoint_suffix(self):
        """get_runner_type_from_labels returns None endpoint suffix for invalid labels."""
        labels = ["invalid", "labels"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert endpoint_suffix is None

    def test_empty_labels_returns_none_runner_type(self):
        """get_runner_type_from_labels returns None runner type for empty labels."""
        runner_type, endpoint_suffix = get_runner_type_from_labels([])
        assert runner_type is None

    def test_empty_labels_returns_none_endpoint_suffix(self):
        """get_runner_type_from_labels returns None endpoint suffix for empty labels."""
        runner_type, endpoint_suffix = get_runner_type_from_labels([])
        assert endpoint_suffix is None


# === Default Values ===


class TestDefaultValues:
    """Tests for default configuration values."""

    def test_default_ecs_arch_is_valid(self):
        """DEFAULT_ECS_ARCH is a valid ECS architecture."""
        assert DEFAULT_ECS_ARCH in ECS_ARCHITECTURES

    def test_default_ec2_arch_is_valid(self):
        """DEFAULT_EC2_ARCH is a valid EC2 architecture."""
        assert DEFAULT_EC2_ARCH in EC2_ARCHITECTURES

    def test_default_ecs_compute_is_valid(self):
        """DEFAULT_ECS_COMPUTE is a valid ECS compute type."""
        assert DEFAULT_ECS_COMPUTE in ECS_COMPUTE

    def test_default_ec2_compute_is_valid(self):
        """DEFAULT_EC2_COMPUTE is a valid EC2 compute type."""
        assert DEFAULT_EC2_COMPUTE in EC2_COMPUTE

    def test_default_pricing_is_valid(self):
        """DEFAULT_PRICING is a valid pricing model."""
        assert DEFAULT_PRICING in PRICING_MODELS

    def test_default_runner_id_matches_pattern(self):
        """DEFAULT_RUNNER_ID matches the runner ID pattern."""
        assert RUNNER_ID_PATTERN.match(DEFAULT_RUNNER_ID) is not None


# === _find_config_file Fallback Paths ===


class TestFindConfigFileFallbacks:
    """Tests for _find_config_file_from_paths fallback paths."""

    def test_lib_config_used_when_exists(self, tmp_path):
        """_find_config_file_from_paths returns lib config when it exists."""
        config_file = tmp_path / "runners.json"
        config_file.write_text('{"platforms": ["ecs"]}')

        result = _find_config_file_from_paths(lib_config=config_file)
        assert result == config_file

    def test_env_path_fallback_used_when_lib_path_not_found(self, tmp_path):
        """_find_config_file_from_paths uses env path when lib path doesn't exist."""
        config_file = tmp_path / "runners.json"
        config_file.write_text('{"platforms": ["ecs"]}')

        # Pass non-existent lib config, but valid env path
        nonexistent_lib = tmp_path / "nonexistent" / "runners.json"
        result = _find_config_file_from_paths(
            lib_config=nonexistent_lib,
            env_path=str(tmp_path),
        )
        assert result == config_file

    def test_env_path_fallback_when_lib_config_is_none(self, tmp_path):
        """_find_config_file_from_paths uses env path when lib config is None."""
        config_file = tmp_path / "runners.json"
        config_file.write_text('{"platforms": ["ecs"]}')

        result = _find_config_file_from_paths(
            lib_config=None,
            env_path=str(tmp_path),
        )
        assert result == config_file

    def test_cwd_fallback_used_when_lib_and_env_not_found(self, tmp_path):
        """_find_config_file_from_paths uses cwd fallback when lib and env don't exist."""
        # Create config in cwd/etc
        etc_dir = tmp_path / "etc"
        etc_dir.mkdir()
        config_file = etc_dir / "runners.json"
        config_file.write_text('{"platforms": ["ecs"]}')

        result = _find_config_file_from_paths(
            lib_config=None,
            env_path=None,
            cwd=tmp_path,
        )
        assert result == config_file

    def test_cwd_fallback_when_env_path_has_no_config(self, tmp_path):
        """_find_config_file_from_paths uses cwd when env path exists but has no config."""
        # Create config in cwd/etc only
        etc_dir = tmp_path / "etc"
        etc_dir.mkdir()
        config_file = etc_dir / "runners.json"
        config_file.write_text('{"platforms": ["ecs"]}')

        # env_path directory exists but doesn't have runners.json
        env_dir = tmp_path / "env_dir"
        env_dir.mkdir()

        result = _find_config_file_from_paths(
            lib_config=None,
            env_path=str(env_dir),
            cwd=tmp_path,
        )
        assert result == config_file

    def test_file_not_found_when_no_config_exists(self, tmp_path):
        """_find_config_file_from_paths raises FileNotFoundError when no config found."""
        with pytest.raises(FileNotFoundError, match="Cannot locate"):
            _find_config_file_from_paths(
                lib_config=None,
                env_path=None,
                cwd=None,
            )

    def test_file_not_found_when_all_paths_invalid(self, tmp_path):
        """_find_config_file_from_paths raises when all paths exist but have no config."""
        nonexistent = tmp_path / "nonexistent" / "runners.json"
        empty_env = tmp_path / "empty_env"
        empty_env.mkdir()
        empty_cwd = tmp_path / "empty_cwd"
        empty_cwd.mkdir()

        with pytest.raises(FileNotFoundError, match="Cannot locate"):
            _find_config_file_from_paths(
                lib_config=nonexistent,
                env_path=str(empty_env),
                cwd=empty_cwd,
            )


# === get_runner_type_from_labels Function (Additional Tests) ===


class TestGetRunnerTypeFromLabelsExtended:
    """Additional tests for get_runner_type_from_labels function."""

    def test_returns_tuple(self):
        """get_runner_type_from_labels returns a tuple."""
        labels = ["ecs", "fargate", "x86", "spot", "runner-12345"]
        result = get_runner_type_from_labels(labels)
        assert isinstance(result, tuple)

    def test_returns_two_elements(self):
        """get_runner_type_from_labels returns tuple with two elements."""
        labels = ["ecs", "fargate", "x86", "spot", "runner-12345"]
        result = get_runner_type_from_labels(labels)
        assert len(result) == 2

    def test_ecs_non_e2e_returns_fargate(self):
        """get_runner_type_from_labels returns fargate for ECS non-e2e."""
        labels = ["ecs", "fargate", "x86", "spot", "runner-12345"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert runner_type == "fargate"
        assert endpoint_suffix == "ecs"

    def test_ecs_e2e_returns_fargate_e2e(self):
        """get_runner_type_from_labels returns fargate-e2e for ECS e2e."""
        labels = ["ecs", "fargate", "x86", "spot", "runner-12345", "e2e"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert runner_type == "fargate-e2e"
        assert endpoint_suffix == "ecs"

    def test_ec2_non_e2e_returns_ec2(self):
        """get_runner_type_from_labels returns ec2 for EC2 non-e2e."""
        labels = ["ec2", "general-purpose", "intel", "spot", "runner-12345"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert runner_type == "ec2"
        assert endpoint_suffix == "ec2"

    def test_ec2_e2e_returns_ec2_e2e(self):
        """get_runner_type_from_labels returns ec2-e2e for EC2 e2e."""
        labels = ["ec2", "general-purpose", "intel", "spot", "runner-12345", "e2e"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert runner_type == "ec2-e2e"
        assert endpoint_suffix == "ec2"

    def test_invalid_labels_returns_none(self):
        """get_runner_type_from_labels returns None values for invalid labels."""
        labels = ["invalid", "labels", "only"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert runner_type is None
        assert endpoint_suffix is None

    def test_empty_labels_returns_none(self):
        """get_runner_type_from_labels returns None values for empty labels."""
        labels = []
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert runner_type is None
        assert endpoint_suffix is None

    def test_missing_required_labels_returns_none(self):
        """get_runner_type_from_labels returns None when labels incomplete."""
        # Missing runner ID
        labels = ["ecs", "fargate", "x86", "spot"]
        runner_type, endpoint_suffix = get_runner_type_from_labels(labels)
        assert runner_type is None
        assert endpoint_suffix is None
