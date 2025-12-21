"""
Runner label parsing and validation module.

This module provides functions to parse, validate, and interpret the composable
runner label system. Labels combine to select the appropriate runner:

    Platform:     ecs | ec2
    Compute:      fargate (ECS) | general-purpose | memory-optimized | gpu | fpga (EC2)
    Architecture: x86 | arm (ECS) | intel | amd | arm (EC2, required for some compute)
    Pricing:      spot | on-demand
    Workflow ID:  runner-{github.run_id}

Configuration is loaded from etc/runners.json (single source of truth).

Example label combinations:
    ["ecs", "fargate", "x86", "spot", "runner-12345"] -> ECS Fargate X86_64 Spot
    ["ecs", "fargate", "arm", "spot", "runner-12345"] -> ECS Fargate ARM64 Spot
    ["ec2", "general-purpose", "intel", "spot", "runner-12345"] -> EC2 m8i.4xlarge Spot
    ["ec2", "memory-optimized", "arm", "on-demand", "runner-12345"] -> EC2 r8g.4xlarge On-Demand
    ["ec2", "gpu", "spot", "runner-12345"] -> EC2 g6e.2xlarge Spot (no arch)
    ["ec2", "fpga", "on-demand", "runner-12345"] -> EC2 f2.12xlarge On-Demand (no arch)
"""

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import json


def _find_config_file() -> Path:
    """Find the runners.json config file."""
    # Try relative to this file (lib/python/runner_labels/__init__.py)
    module_dir = Path(__file__).parent
    config_path = module_dir.parent.parent.parent / "etc" / "runners.json"
    if config_path.exists():
        return config_path

    # Try from ETC_PATH environment variable (for Lambda deployment)
    etc_path = os.environ.get("ETC_PATH")
    if etc_path:
        config_path = Path(etc_path) / "runners.json"
        if config_path.exists():
            return config_path

    # Try current working directory
    config_path = Path.cwd() / "etc" / "runners.json"
    if config_path.exists():
        return config_path

    raise FileNotFoundError(
        "Could not find etc/runners.json. "
        "Set ETC_PATH environment variable or run from repo root."
    )


def _load_config() -> Dict[str, Any]:
    """Load configuration from etc/runners.json."""
    config_path = _find_config_file()
    with open(config_path, "r", encoding="utf-8") as f:
        return json.load(f)


# Load configuration from JSON (single source of truth)
_config = _load_config()
_labels = _config.get("labels", {})

# Valid label values from JSON
PLATFORMS = frozenset(_labels.get("platforms", ["ecs", "ec2"]))
PRICING_MODELS = frozenset(_labels.get("pricing_models", ["spot", "on-demand"]))

# ECS labels from JSON
_ecs_config = _labels.get("ecs", {})
ECS_COMPUTE = frozenset(_ecs_config.get("compute_types", ["fargate"]))
ECS_ARCHITECTURES = frozenset(_ecs_config.get("architectures", ["x86", "arm"]))

# EC2 labels from JSON
_ec2_config = _labels.get("ec2", {})
EC2_COMPUTE = frozenset(_ec2_config.get("compute_types", []))
EC2_ARCHITECTURES = frozenset(_ec2_config.get("architectures", []))
EC2_COMPUTE_REQUIRES_ARCH = frozenset(_ec2_config.get("compute_requires_arch", []))
EC2_COMPUTE_FORBIDS_ARCH = frozenset(_ec2_config.get("compute_forbids_arch", []))

# All compute types (derived)
COMPUTE_TYPES = ECS_COMPUTE | EC2_COMPUTE

# All architecture labels
ALL_ARCHITECTURES = ECS_ARCHITECTURES | EC2_ARCHITECTURES

# Instance type mapping from JSON
_instance_map = _labels.get("instance_type_map", {})
INSTANCE_TYPE_MAP: Dict[tuple, str] = {}
for compute, arch_map in _instance_map.items():
    if isinstance(arch_map, dict):
        for arch, instance_type in arch_map.items():
            INSTANCE_TYPE_MAP[(compute, arch)] = instance_type
    else:
        # No architecture (gpu, fpga)
        INSTANCE_TYPE_MAP[(compute, None)] = arch_map

# ECS task architecture mapping from JSON
ECS_TASK_ARCHITECTURE_MAP = _labels.get("ecs_task_architecture_map", {})

# ECS Fargate configuration from JSON
_fargate_config = _config.get("fargate", {})
ECS_FARGATE_CONFIG = {
    "cpu": _fargate_config.get("cpu", "4096"),
    "memory": _fargate_config.get("memory", "16384"),
}

# Runner ID pattern
RUNNER_ID_PATTERN = re.compile(r"^runner-(\d+)$")

# Default/canonical values for testing (from JSON - single source of truth)
_ecs_defaults = _ecs_config.get("defaults", {})
_ec2_defaults = _ec2_config.get("defaults", {})
_global_defaults = _labels.get("defaults", {})

DEFAULT_ECS_ARCH = _ecs_defaults.get("architecture", "x86")
DEFAULT_EC2_ARCH = _ec2_defaults.get("architecture", "intel")
DEFAULT_ECS_COMPUTE = _ecs_defaults.get("compute", "fargate")
DEFAULT_EC2_COMPUTE = _ec2_defaults.get("compute", "memory-optimized")
DEFAULT_PRICING = _global_defaults.get("pricing", "spot")
DEFAULT_RUNNER_ID = _global_defaults.get("runner_id", "runner-12345")


@dataclass
class ParsedLabels:
    """Parsed runner labels."""

    platform: str
    compute: str
    pricing: str
    runner_id: str
    architecture: Optional[str] = None


class LabelParseError(Exception):
    """Raised when label parsing fails."""


class LabelValidationError(Exception):
    """Raised when label validation fails."""


def parse_labels(label_list: List[str]) -> ParsedLabels:
    """
    Parse a list of runner labels into structured components.

    Args:
        label_list: List of label strings.

    Returns:
        ParsedLabels with platform, compute, pricing, runner_id, and architecture.

    Raises:
        LabelParseError: If required labels are missing or invalid.
    """
    if not label_list:
        raise LabelParseError("Label list cannot be empty")

    labels = set(label_list)

    # Extract platform
    platform_labels = labels & PLATFORMS
    if not platform_labels:
        raise LabelParseError(
            f"Missing platform label. Must be one of: {sorted(PLATFORMS)}"
        )
    if len(platform_labels) > 1:
        raise LabelParseError(
            f"Multiple platform labels found: {sorted(platform_labels)}"
        )
    platform = platform_labels.pop()

    # Extract compute type
    compute_labels = labels & COMPUTE_TYPES
    if not compute_labels:
        raise LabelParseError(
            f"Missing compute label. Must be one of: {sorted(COMPUTE_TYPES)}"
        )
    if len(compute_labels) > 1:
        raise LabelParseError(
            f"Multiple compute labels found: {sorted(compute_labels)}"
        )
    compute_type = compute_labels.pop()

    # Extract architecture (may be None for gpu/fpga)
    arch_labels = labels & ALL_ARCHITECTURES
    architecture = None
    if len(arch_labels) > 1:
        raise LabelParseError(
            f"Multiple architecture labels found: {sorted(arch_labels)}"
        )
    if arch_labels:
        architecture = arch_labels.pop()

    # Extract pricing model
    pricing_labels = labels & PRICING_MODELS
    if not pricing_labels:
        raise LabelParseError(
            f"Missing pricing label. Must be one of: {sorted(PRICING_MODELS)}"
        )
    if len(pricing_labels) > 1:
        raise LabelParseError(
            f"Multiple pricing labels found: {sorted(pricing_labels)}"
        )
    pricing = pricing_labels.pop()

    # Extract runner ID
    runner_id = None
    for label in label_list:
        match = RUNNER_ID_PATTERN.match(label)
        if match:
            runner_id = label
            break

    if runner_id is None:
        raise LabelParseError(
            "Missing runner ID label. Must match pattern: runner-{number}"
        )

    return ParsedLabels(
        platform=platform,
        compute=compute_type,
        pricing=pricing,
        runner_id=runner_id,
        architecture=architecture,
    )


def validate_labels(parsed: ParsedLabels) -> None:
    """
    Validate that parsed labels form a valid combination.

    Args:
        parsed: ParsedLabels to validate.

    Raises:
        LabelValidationError: If the label combination is invalid.
    """
    # ECS validation
    if parsed.platform == "ecs":
        if parsed.compute not in ECS_COMPUTE:
            raise LabelValidationError(
                f"ECS platform only supports compute types: {sorted(ECS_COMPUTE)}. "
                f"Got: {parsed.compute}"
            )
        # ECS requires architecture
        if parsed.architecture is None:
            raise LabelValidationError(
                f"ECS platform requires architecture label. "
                f"Must be one of: {sorted(ECS_ARCHITECTURES)}"
            )
        # ECS architecture must be valid
        if parsed.architecture not in ECS_ARCHITECTURES:
            raise LabelValidationError(
                f"ECS platform only supports architectures: {sorted(ECS_ARCHITECTURES)}. "
                f"Got: {parsed.architecture}"
            )

    # EC2 validation
    if parsed.platform == "ec2":
        if parsed.compute not in EC2_COMPUTE:
            raise LabelValidationError(
                f"EC2 platform only supports compute types: {sorted(EC2_COMPUTE)}. "
                f"Got: {parsed.compute}"
            )

        # Check architecture requirements based on compute type
        if parsed.compute in EC2_COMPUTE_REQUIRES_ARCH:
            if parsed.architecture is None:
                raise LabelValidationError(
                    f"EC2 compute type '{parsed.compute}' requires architecture label. "
                    f"Must be one of: {sorted(EC2_ARCHITECTURES)}"
                )
            if parsed.architecture not in EC2_ARCHITECTURES:
                raise LabelValidationError(
                    f"EC2 platform only supports architectures: "
                    f"{sorted(EC2_ARCHITECTURES)}. Got: {parsed.architecture}"
                )

        if parsed.compute in EC2_COMPUTE_FORBIDS_ARCH:
            if parsed.architecture is not None:
                raise LabelValidationError(
                    f"EC2 compute type '{parsed.compute}' does not support "
                    f"architecture label. Got: {parsed.architecture}"
                )


def get_instance_type(parsed: ParsedLabels) -> Optional[str]:
    """
    Get the EC2 instance type for a parsed label set.

    Args:
        parsed: ParsedLabels to get instance type for.

    Returns:
        Instance type string (e.g., "m8i.4xlarge") or None for ECS/Fargate.
    """
    if parsed.platform == "ecs":
        return None

    return INSTANCE_TYPE_MAP.get((parsed.compute, parsed.architecture))


def get_ecs_config(parsed: ParsedLabels) -> Optional[Dict[str, str]]:
    """
    Get the ECS task configuration for a parsed label set.

    Args:
        parsed: ParsedLabels to get ECS config for.

    Returns:
        Dict with cpu and memory keys, or None for EC2.
    """
    if parsed.platform != "ecs":
        return None

    if parsed.compute == "fargate":
        return ECS_FARGATE_CONFIG.copy()

    return None


def get_task_architecture(parsed: ParsedLabels) -> Optional[str]:
    """
    Get the ECS task CPU architecture for a parsed label set.

    Args:
        parsed: ParsedLabels to get task architecture for.

    Returns:
        Task architecture string (e.g., "X86_64", "ARM64") or None for EC2.
    """
    if parsed.platform != "ecs":
        return None

    if parsed.architecture is None:
        return None

    return ECS_TASK_ARCHITECTURE_MAP.get(parsed.architecture)


def is_spot(parsed: ParsedLabels) -> bool:
    """
    Check if the parsed labels indicate Spot pricing.

    Args:
        parsed: ParsedLabels to check.

    Returns:
        True if Spot pricing, False for On-Demand.
    """
    return parsed.pricing == "spot"


def get_runner_id_number(parsed: ParsedLabels) -> int:
    """
    Extract the numeric portion of the runner ID.

    Args:
        parsed: ParsedLabels with runner_id.

    Returns:
        The numeric ID portion.
    """
    match = RUNNER_ID_PATTERN.match(parsed.runner_id)
    if match:
        return int(match.group(1))
    raise LabelParseError(f"Invalid runner ID format: {parsed.runner_id}")
