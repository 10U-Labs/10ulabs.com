"""
Runner label parsing and validation module.

This module provides functions to parse, validate, and interpret the composable
runner label system. Labels combine to select the appropriate runner:

    Platform:     ecs | ec2
    Compute:      fargate (ECS) | general-purpose | memory-optimized | gpu | fpga (EC2)
    Architecture: x86 | arm (ECS) | intel | amd | arm (EC2, required for some compute)
    Pricing:      spot | on-demand
    Workflow ID:  runner-{github.run_id}

Example label combinations:
    ["ecs", "fargate", "x86", "spot", "runner-12345"] -> ECS Fargate X86_64 Spot
    ["ecs", "fargate", "arm", "spot", "runner-12345"] -> ECS Fargate ARM64 Spot
    ["ec2", "general-purpose", "intel", "spot", "runner-12345"] -> EC2 m8i.4xlarge Spot
    ["ec2", "memory-optimized", "arm", "on-demand", "runner-12345"] -> EC2 r8g.4xlarge On-Demand
    ["ec2", "gpu", "spot", "runner-12345"] -> EC2 g6e.2xlarge Spot (no arch)
    ["ec2", "fpga", "on-demand", "runner-12345"] -> EC2 f2.12xlarge On-Demand (no arch)
"""

import re
from dataclasses import dataclass
from typing import Dict, List, Optional


# Valid label values
PLATFORMS = frozenset({"ecs", "ec2"})
PRICING_MODELS = frozenset({"spot", "on-demand"})

# ECS compute types
ECS_COMPUTE = frozenset({"fargate"})

# EC2 compute types
EC2_COMPUTE = frozenset({"general-purpose", "memory-optimized", "gpu", "fpga"})

# EC2 compute types that REQUIRE architecture label
EC2_COMPUTE_REQUIRES_ARCH = frozenset({"general-purpose", "memory-optimized"})

# EC2 compute types that FORBID architecture label
EC2_COMPUTE_FORBIDS_ARCH = frozenset({"gpu", "fpga"})

# All compute types (derived)
COMPUTE_TYPES = ECS_COMPUTE | EC2_COMPUTE

# Architecture labels for ECS (maps to task CPU architecture)
ECS_ARCHITECTURES = frozenset({"x86", "arm"})

# Architecture labels for EC2 (maps to instance type suffix)
EC2_ARCHITECTURES = frozenset({"intel", "amd", "arm"})

# All architecture labels
ALL_ARCHITECTURES = ECS_ARCHITECTURES | EC2_ARCHITECTURES

# Instance type mapping: (compute, architecture) -> instance type
# For gpu/fpga, architecture is None
INSTANCE_TYPE_MAP: Dict[tuple, str] = {
    ("general-purpose", "intel"): "m8i.4xlarge",
    ("general-purpose", "amd"): "m8a.4xlarge",
    ("general-purpose", "arm"): "m8g.4xlarge",
    ("memory-optimized", "intel"): "r8i.4xlarge",
    ("memory-optimized", "amd"): "r8a.4xlarge",
    ("memory-optimized", "arm"): "r8g.4xlarge",
    ("gpu", None): "g6e.2xlarge",
    ("fpga", None): "f2.12xlarge",
}

# ECS task architecture mapping
ECS_TASK_ARCHITECTURE_MAP = {
    "x86": "X86_64",
    "arm": "ARM64",
}

# ECS Fargate configuration
ECS_FARGATE_CONFIG = {
    "cpu": "4096",
    "memory": "16384",
}

# Runner ID pattern
RUNNER_ID_PATTERN = re.compile(r"^runner-(\d+)$")


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
    compute = compute_labels.pop()

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
        compute=compute,
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
