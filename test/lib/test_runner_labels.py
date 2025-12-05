"""
Unit tests for lib/runner_labels.py.

Tests follow the testing pyramid principles from CLAUDE.md:
- Atomic tests: each test verifies one thing
- Single responsibility: one assertion per test
- Full coverage: every function, every branch
"""

import sys
from pathlib import Path

import pytest

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "lib"))

from runner_labels import (
    ECS_FARGATE_CONFIG,
    INSTANCE_TYPES,
    LabelParseError,
    LabelValidationError,
    ParsedLabels,
    get_ecs_config,
    get_instance_type,
    get_runner_id_number,
    is_spot,
    parse_labels,
    validate_labels,
)


class TestParseLabelsValidInput:
    """Tests for parse_labels with valid input."""

    def test_parses_valid_ecs_fargate_spot_labels(self) -> None:
        """parse_labels extracts correct values for ECS Fargate Spot."""
        result = parse_labels(["ecs", "fargate", "spot", "runner-12345"])
        assert result.platform == "ecs"

    def test_parses_valid_ecs_fargate_spot_compute(self) -> None:
        """parse_labels extracts correct compute for ECS Fargate Spot."""
        result = parse_labels(["ecs", "fargate", "spot", "runner-12345"])
        assert result.compute == "fargate"

    def test_parses_valid_ecs_fargate_spot_pricing(self) -> None:
        """parse_labels extracts correct pricing for ECS Fargate Spot."""
        result = parse_labels(["ecs", "fargate", "spot", "runner-12345"])
        assert result.pricing == "spot"

    def test_parses_valid_ecs_fargate_spot_runner_id(self) -> None:
        """parse_labels extracts correct runner_id for ECS Fargate Spot."""
        result = parse_labels(["ecs", "fargate", "spot", "runner-12345"])
        assert result.runner_id == "runner-12345"

    def test_parses_valid_ec2_c8i_on_demand_labels(self) -> None:
        """parse_labels extracts correct values for EC2 c8i On-Demand."""
        result = parse_labels(["ec2", "c8i", "on-demand", "runner-99999"])
        assert result.platform == "ec2"

    def test_parses_valid_ec2_c8i_on_demand_compute(self) -> None:
        """parse_labels extracts correct compute for EC2 c8i On-Demand."""
        result = parse_labels(["ec2", "c8i", "on-demand", "runner-99999"])
        assert result.compute == "c8i"

    def test_parses_valid_ec2_c8i_on_demand_pricing(self) -> None:
        """parse_labels extracts correct pricing for EC2 c8i On-Demand."""
        result = parse_labels(["ec2", "c8i", "on-demand", "runner-99999"])
        assert result.pricing == "on-demand"

    def test_parses_valid_ec2_r8i_labels(self) -> None:
        """parse_labels extracts correct compute for EC2 r8i."""
        result = parse_labels(["ec2", "r8i", "on-demand", "runner-1"])
        assert result.compute == "r8i"

    def test_parses_valid_ec2_g6e_labels(self) -> None:
        """parse_labels extracts correct compute for EC2 g6e."""
        result = parse_labels(["ec2", "g6e", "on-demand", "runner-1"])
        assert result.compute == "g6e"

    def test_parses_labels_in_any_order(self) -> None:
        """parse_labels handles labels in any order."""
        result = parse_labels(["runner-42", "spot", "fargate", "ecs"])
        assert result.platform == "ecs"
        assert result.compute == "fargate"
        assert result.pricing == "spot"
        assert result.runner_id == "runner-42"

    def test_parses_labels_with_extra_labels(self) -> None:
        """parse_labels ignores unrecognized labels."""
        result = parse_labels(
            ["ecs", "fargate", "spot", "runner-1", "extra-label", "another"]
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
            parse_labels(["fargate", "spot", "runner-1"])

    def test_raises_on_missing_compute(self) -> None:
        """parse_labels raises LabelParseError when compute is missing."""
        with pytest.raises(LabelParseError, match="Missing compute"):
            parse_labels(["ecs", "spot", "runner-1"])

    def test_raises_on_missing_pricing(self) -> None:
        """parse_labels raises LabelParseError when pricing is missing."""
        with pytest.raises(LabelParseError, match="Missing pricing"):
            parse_labels(["ecs", "fargate", "runner-1"])

    def test_raises_on_missing_runner_id(self) -> None:
        """parse_labels raises LabelParseError when runner_id is missing."""
        with pytest.raises(LabelParseError, match="Missing runner ID"):
            parse_labels(["ecs", "fargate", "spot"])

    def test_raises_on_invalid_runner_id_format(self) -> None:
        """parse_labels raises LabelParseError on invalid runner_id format."""
        with pytest.raises(LabelParseError, match="Missing runner ID"):
            parse_labels(["ecs", "fargate", "spot", "runner-abc"])

    def test_raises_on_multiple_platforms(self) -> None:
        """parse_labels raises LabelParseError with multiple platforms."""
        with pytest.raises(LabelParseError, match="Multiple platform"):
            parse_labels(["ecs", "ec2", "fargate", "spot", "runner-1"])

    def test_raises_on_multiple_compute_types(self) -> None:
        """parse_labels raises LabelParseError with multiple compute types."""
        with pytest.raises(LabelParseError, match="Multiple compute"):
            parse_labels(["ec2", "c8i", "r8i", "spot", "runner-1"])

    def test_raises_on_multiple_pricing_models(self) -> None:
        """parse_labels raises LabelParseError with multiple pricing models."""
        with pytest.raises(LabelParseError, match="Multiple pricing"):
            parse_labels(["ecs", "fargate", "spot", "on-demand", "runner-1"])


class TestValidateLabels:
    """Tests for validate_labels function."""

    def test_accepts_ecs_fargate_spot(self) -> None:
        """validate_labels accepts ecs + fargate + spot."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1")
        validate_labels(parsed)  # Should not raise

    def test_accepts_ecs_fargate_on_demand(self) -> None:
        """validate_labels accepts ecs + fargate + on-demand."""
        parsed = ParsedLabels("ecs", "fargate", "on-demand", "runner-1")
        validate_labels(parsed)  # Should not raise

    def test_accepts_ec2_c8i_on_demand(self) -> None:
        """validate_labels accepts ec2 + c8i + on-demand."""
        parsed = ParsedLabels("ec2", "c8i", "on-demand", "runner-1")
        validate_labels(parsed)  # Should not raise

    def test_accepts_ec2_c8i_spot(self) -> None:
        """validate_labels accepts ec2 + c8i + spot."""
        parsed = ParsedLabels("ec2", "c8i", "spot", "runner-1")
        validate_labels(parsed)  # Should not raise

    def test_accepts_ec2_r8i_on_demand(self) -> None:
        """validate_labels accepts ec2 + r8i + on-demand."""
        parsed = ParsedLabels("ec2", "r8i", "on-demand", "runner-1")
        validate_labels(parsed)  # Should not raise

    def test_accepts_ec2_g6e_on_demand(self) -> None:
        """validate_labels accepts ec2 + g6e + on-demand."""
        parsed = ParsedLabels("ec2", "g6e", "on-demand", "runner-1")
        validate_labels(parsed)  # Should not raise

    def test_rejects_ecs_with_c8i(self) -> None:
        """validate_labels rejects ecs + c8i (invalid combination)."""
        parsed = ParsedLabels("ecs", "c8i", "spot", "runner-1")
        with pytest.raises(LabelValidationError, match="ECS platform only"):
            validate_labels(parsed)

    def test_rejects_ecs_with_r8i(self) -> None:
        """validate_labels rejects ecs + r8i (invalid combination)."""
        parsed = ParsedLabels("ecs", "r8i", "spot", "runner-1")
        with pytest.raises(LabelValidationError, match="ECS platform only"):
            validate_labels(parsed)

    def test_rejects_ecs_with_g6e(self) -> None:
        """validate_labels rejects ecs + g6e (invalid combination)."""
        parsed = ParsedLabels("ecs", "g6e", "spot", "runner-1")
        with pytest.raises(LabelValidationError, match="ECS platform only"):
            validate_labels(parsed)

    def test_rejects_ec2_with_fargate(self) -> None:
        """validate_labels rejects ec2 + fargate (invalid combination)."""
        parsed = ParsedLabels("ec2", "fargate", "spot", "runner-1")
        with pytest.raises(LabelValidationError, match="EC2 platform only"):
            validate_labels(parsed)


class TestGetInstanceType:
    """Tests for get_instance_type function."""

    def test_returns_c8i_4xlarge_for_c8i(self) -> None:
        """get_instance_type returns c8i.4xlarge for c8i compute."""
        parsed = ParsedLabels("ec2", "c8i", "on-demand", "runner-1")
        assert get_instance_type(parsed) == "c8i.4xlarge"

    def test_returns_r8i_4xlarge_for_r8i(self) -> None:
        """get_instance_type returns r8i.4xlarge for r8i compute."""
        parsed = ParsedLabels("ec2", "r8i", "on-demand", "runner-1")
        assert get_instance_type(parsed) == "r8i.4xlarge"

    def test_returns_g6e_xlarge_for_g6e(self) -> None:
        """get_instance_type returns g6e.xlarge for g6e compute."""
        parsed = ParsedLabels("ec2", "g6e", "on-demand", "runner-1")
        assert get_instance_type(parsed) == "g6e.xlarge"

    def test_returns_none_for_ecs_fargate(self) -> None:
        """get_instance_type returns None for ECS Fargate."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1")
        assert get_instance_type(parsed) is None

    def test_instance_types_dict_has_all_ec2_compute(self) -> None:
        """INSTANCE_TYPES dict contains all EC2 compute types."""
        assert "c8i" in INSTANCE_TYPES
        assert "r8i" in INSTANCE_TYPES
        assert "g6e" in INSTANCE_TYPES


class TestGetEcsConfig:
    """Tests for get_ecs_config function."""

    def test_returns_config_for_fargate(self) -> None:
        """get_ecs_config returns config dict for Fargate."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1")
        config = get_ecs_config(parsed)
        assert config is not None

    def test_returns_correct_cpu_for_fargate(self) -> None:
        """get_ecs_config returns correct CPU for Fargate."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1")
        config = get_ecs_config(parsed)
        assert config is not None
        assert config["cpu"] == "4096"

    def test_returns_correct_memory_for_fargate(self) -> None:
        """get_ecs_config returns correct memory for Fargate."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1")
        config = get_ecs_config(parsed)
        assert config is not None
        assert config["memory"] == "8192"

    def test_returns_none_for_ec2(self) -> None:
        """get_ecs_config returns None for EC2 platform."""
        parsed = ParsedLabels("ec2", "c8i", "on-demand", "runner-1")
        assert get_ecs_config(parsed) is None

    def test_returns_copy_not_reference(self) -> None:
        """get_ecs_config returns a copy, not the original dict."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1")
        config = get_ecs_config(parsed)
        assert config is not None
        config["cpu"] = "modified"
        assert ECS_FARGATE_CONFIG["cpu"] == "4096"


class TestIsSpot:
    """Tests for is_spot function."""

    def test_returns_true_for_spot_pricing(self) -> None:
        """is_spot returns True when pricing is spot."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1")
        assert is_spot(parsed) is True

    def test_returns_false_for_on_demand_pricing(self) -> None:
        """is_spot returns False when pricing is on-demand."""
        parsed = ParsedLabels("ecs", "fargate", "on-demand", "runner-1")
        assert is_spot(parsed) is False

    def test_returns_true_for_ec2_spot(self) -> None:
        """is_spot returns True for EC2 with spot pricing."""
        parsed = ParsedLabels("ec2", "c8i", "spot", "runner-1")
        assert is_spot(parsed) is True

    def test_returns_false_for_ec2_on_demand(self) -> None:
        """is_spot returns False for EC2 with on-demand pricing."""
        parsed = ParsedLabels("ec2", "c8i", "on-demand", "runner-1")
        assert is_spot(parsed) is False


class TestGetRunnerIdNumber:
    """Tests for get_runner_id_number function."""

    def test_extracts_number_from_runner_id(self) -> None:
        """get_runner_id_number extracts numeric ID."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-12345")
        assert get_runner_id_number(parsed) == 12345

    def test_extracts_single_digit_number(self) -> None:
        """get_runner_id_number extracts single digit ID."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1")
        assert get_runner_id_number(parsed) == 1

    def test_extracts_large_number(self) -> None:
        """get_runner_id_number extracts large ID."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-9999999999")
        assert get_runner_id_number(parsed) == 9999999999

    def test_raises_on_invalid_format(self) -> None:
        """get_runner_id_number raises on invalid runner_id format."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "invalid")
        with pytest.raises(LabelParseError, match="Invalid runner ID"):
            get_runner_id_number(parsed)


class TestParsedLabelsDataclass:
    """Tests for ParsedLabels dataclass."""

    def test_creates_instance_with_all_fields(self) -> None:
        """ParsedLabels creates instance with all fields."""
        parsed = ParsedLabels("ecs", "fargate", "spot", "runner-1")
        assert parsed.platform == "ecs"
        assert parsed.compute == "fargate"
        assert parsed.pricing == "spot"
        assert parsed.runner_id == "runner-1"

    def test_instances_are_equal_with_same_values(self) -> None:
        """ParsedLabels instances with same values are equal."""
        parsed1 = ParsedLabels("ecs", "fargate", "spot", "runner-1")
        parsed2 = ParsedLabels("ecs", "fargate", "spot", "runner-1")
        assert parsed1 == parsed2

    def test_instances_are_not_equal_with_different_values(self) -> None:
        """ParsedLabels instances with different values are not equal."""
        parsed1 = ParsedLabels("ecs", "fargate", "spot", "runner-1")
        parsed2 = ParsedLabels("ec2", "c8i", "on-demand", "runner-2")
        assert parsed1 != parsed2
