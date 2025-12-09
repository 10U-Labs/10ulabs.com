"""
Runner label parsing and validation module.

This module provides functions to parse, validate, and interpret the composable
runner label system. Labels combine to select the appropriate runner:

    Platform:     ecs | ec2
    Compute:      fargate | r8i | g6e
    Pricing:      spot | on-demand
    Workflow ID:  runner-{github.run_id}

Example label combinations:
    ["ecs", "fargate", "spot", "runner-12345"] -> ECS Fargate Spot
    ["ec2", "r8i", "on-demand", "runner-12345"] -> EC2 r8i.4xlarge On-Demand
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
EC2_COMPUTE = frozenset({"r8i", "g6e"})

# All compute types (derived)
COMPUTE_TYPES = ECS_COMPUTE | EC2_COMPUTE

# Instance type mapping for EC2 compute labels
INSTANCE_TYPES = {
    "r8i": "r8i.4xlarge",
    "g6e": "g6e.2xlarge",
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
        ParsedLabels with platform, compute, pricing, and runner_id.

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
    )


def validate_labels(parsed: ParsedLabels) -> None:
    """
    Validate that parsed labels form a valid combination.

    Args:
        parsed: ParsedLabels to validate.

    Raises:
        LabelValidationError: If the label combination is invalid.
    """
    # ECS can only use Fargate
    if parsed.platform == "ecs" and parsed.compute not in ECS_COMPUTE:
        raise LabelValidationError(
            f"ECS platform only supports compute types: {sorted(ECS_COMPUTE)}. "
            f"Got: {parsed.compute}"
        )

    # EC2 cannot use Fargate
    if parsed.platform == "ec2" and parsed.compute not in EC2_COMPUTE:
        raise LabelValidationError(
            f"EC2 platform only supports compute types: {sorted(EC2_COMPUTE)}. "
            f"Got: {parsed.compute}"
        )


def get_instance_type(parsed: ParsedLabels) -> Optional[str]:
    """
    Get the EC2 instance type for a parsed label set.

    Args:
        parsed: ParsedLabels to get instance type for.

    Returns:
        Instance type string (e.g., "c8i.4xlarge") or None for ECS/Fargate.
    """
    if parsed.platform == "ecs":
        return None

    return INSTANCE_TYPES.get(parsed.compute)


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
