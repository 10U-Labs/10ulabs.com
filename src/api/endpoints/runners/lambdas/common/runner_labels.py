"""Runner label parsing and validation."""

import json
import os
import re
from pathlib import Path
from typing import Any


class LabelParseError(Exception):
    """Error parsing runner labels."""


class LabelValidationError(Exception):
    """Error validating runner labels."""


def _find_config_file() -> Path:
    """Find the runners.json configuration file."""
    # Try ETC_PATH environment variable
    etc_path = os.environ.get("ETC_PATH")
    if etc_path:
        config_path = Path(etc_path) / "runners.json"
        if config_path.exists():
            return config_path

    # Try relative to this file (Lambda deployment: bundled in common/etc/)
    layer_path = Path(__file__).parent / "etc" / "runners.json"
    if layer_path.exists():
        return layer_path

    # Try repo root structure (local development)
    repo_path = Path(__file__).parent.parent.parent.parent.parent.parent.parent
    repo_config = repo_path / "etc" / "runners.json"
    if repo_config.exists():
        return repo_config

    # Try current working directory
    cwd_path = Path.cwd() / "etc" / "runners.json"
    if cwd_path.exists():
        return cwd_path

    raise FileNotFoundError(
        "Could not find etc/runners.json. "
        "Set ETC_PATH environment variable or run from repo root."
    )


def _load_config() -> dict[str, Any]:
    """Load configuration from JSON file."""
    config_path = _find_config_file()
    with open(config_path, encoding="utf-8") as f:
        return json.load(f)


# Load configuration from JSON (single source of truth)
_config = _load_config()
_labels = _config.get("labels", {})

# Valid label values from JSON
PLATFORMS: set[str] = set(_labels.get("platforms", ["ecs", "ec2"]))
PRICING_MODELS: set[str] = set(_labels.get("pricing_models", ["spot", "on-demand"]))

# ECS labels from JSON
_ecs_config = _labels.get("ecs", {})
ECS_COMPUTE: set[str] = set(_ecs_config.get("compute_types", ["fargate"]))
ECS_ARCHITECTURES: set[str] = set(_ecs_config.get("architectures", ["x86", "arm"]))

# EC2 labels from JSON
_ec2_config = _labels.get("ec2", {})
EC2_COMPUTE: set[str] = set(_ec2_config.get("compute_types", []))
EC2_ARCHITECTURES: set[str] = set(_ec2_config.get("architectures", []))
_EC2_COMPUTE_REQUIRES_ARCH: set[str] = set(
    _ec2_config.get("compute_requires_arch", [])
)
_EC2_COMPUTE_FORBIDS_ARCH: set[str] = set(_ec2_config.get("compute_forbids_arch", []))

# All compute types (derived)
COMPUTE_TYPES: set[str] = ECS_COMPUTE | EC2_COMPUTE

# All architecture labels
ALL_ARCHITECTURES: set[str] = ECS_ARCHITECTURES | EC2_ARCHITECTURES

# Instance type mapping from JSON
_instance_map = _labels.get("instance_type_map", {})
_INSTANCE_TYPE_MAP: dict[str, str] = {}
for _compute, _arch_map in _instance_map.items():
    if isinstance(_arch_map, dict):
        for _arch, _instance_type in _arch_map.items():
            _INSTANCE_TYPE_MAP[f"{_compute}:{_arch}"] = _instance_type
    else:
        # No architecture (gpu, fpga)
        _INSTANCE_TYPE_MAP[f"{_compute}:None"] = _arch_map

# ECS task architecture mapping from JSON
_ECS_TASK_ARCHITECTURE_MAP: dict[str, str] = _labels.get(
    "ecs_task_architecture_map", {}
)

# ECS Fargate configuration from JSON
_fargate_config = _config.get("fargate", {})
_ECS_FARGATE_CONFIG = {
    "cpu": _fargate_config.get("cpu", "4096"),
    "memory": _fargate_config.get("memory", "16384"),
}

# Runner ID pattern
_RUNNER_ID_PATTERN = re.compile(r"^runner-(\d+)$")


def parse_labels(label_list: list[str]) -> dict[str, Any]:
    """Parse job labels to extract platform, compute, architecture, pricing, runner ID.

    Args:
        label_list: List of labels from the workflow job

    Returns:
        Dictionary with platform, compute, pricing, runnerId, architecture

    Raises:
        LabelParseError: If required labels are missing or duplicated
    """
    if not label_list:
        raise LabelParseError("Label list cannot be empty")

    label_set = set(label_list)

    # Extract platform
    platform_labels = [label for label in label_set if label in PLATFORMS]
    if not platform_labels:
        raise LabelParseError(
            f"Missing platform label. Must be one of: {', '.join(sorted(PLATFORMS))}"
        )
    if len(platform_labels) > 1:
        raise LabelParseError(
            f"Multiple platform labels found: {', '.join(sorted(platform_labels))}"
        )
    platform = platform_labels[0]

    # Extract compute type
    compute_labels = [label for label in label_set if label in COMPUTE_TYPES]
    if not compute_labels:
        raise LabelParseError(
            f"Missing compute label. Must be one of: "
            f"{', '.join(sorted(COMPUTE_TYPES))}"
        )
    if len(compute_labels) > 1:
        raise LabelParseError(
            f"Multiple compute labels found: {', '.join(sorted(compute_labels))}"
        )
    compute = compute_labels[0]

    # Extract architecture (may be None for gpu/fpga)
    arch_labels = [label for label in label_set if label in ALL_ARCHITECTURES]
    if len(arch_labels) > 1:
        raise LabelParseError(
            f"Multiple architecture labels found: {', '.join(sorted(arch_labels))}"
        )
    architecture = arch_labels[0] if arch_labels else None

    # Extract pricing model
    pricing_labels = [label for label in label_set if label in PRICING_MODELS]
    if not pricing_labels:
        raise LabelParseError(
            f"Missing pricing label. Must be one of: "
            f"{', '.join(sorted(PRICING_MODELS))}"
        )
    if len(pricing_labels) > 1:
        raise LabelParseError(
            f"Multiple pricing labels found: {', '.join(sorted(pricing_labels))}"
        )
    pricing = pricing_labels[0]

    # Extract runner ID
    runner_id = None
    for label in label_list:
        if _RUNNER_ID_PATTERN.match(label):
            runner_id = label
            break

    if not runner_id:
        raise LabelParseError(
            "Missing runner ID label. Must match pattern: runner-{number}"
        )

    return {
        "platform": platform,
        "compute": compute,
        "pricing": pricing,
        "runnerId": runner_id,
        "architecture": architecture,
    }


def validate_labels(parsed: dict[str, Any]) -> None:
    """Validate parsed labels for platform-specific requirements.

    Args:
        parsed: Parsed labels from parse_labels()

    Raises:
        LabelValidationError: If labels are invalid for the platform
    """
    platform = parsed["platform"]
    compute = parsed["compute"]
    architecture = parsed["architecture"]

    # ECS validation
    if platform == "ecs":
        if compute not in ECS_COMPUTE:
            raise LabelValidationError(
                f"ECS platform only supports compute types: "
                f"{', '.join(sorted(ECS_COMPUTE))}. Got: {compute}"
            )
        # ECS requires architecture
        if architecture is None:
            raise LabelValidationError(
                f"ECS platform requires architecture label. "
                f"Must be one of: {', '.join(sorted(ECS_ARCHITECTURES))}"
            )
        # ECS architecture must be valid
        if architecture not in ECS_ARCHITECTURES:
            raise LabelValidationError(
                f"ECS platform only supports architectures: "
                f"{', '.join(sorted(ECS_ARCHITECTURES))}. Got: {architecture}"
            )

    # EC2 validation
    if platform == "ec2":
        if compute not in EC2_COMPUTE:
            raise LabelValidationError(
                f"EC2 platform only supports compute types: "
                f"{', '.join(sorted(EC2_COMPUTE))}. Got: {compute}"
            )

        # Check architecture requirements based on compute type
        if compute in _EC2_COMPUTE_REQUIRES_ARCH:
            if architecture is None:
                raise LabelValidationError(
                    f"EC2 compute type '{compute}' requires architecture label. "
                    f"Must be one of: {', '.join(sorted(EC2_ARCHITECTURES))}"
                )
            if architecture not in EC2_ARCHITECTURES:
                raise LabelValidationError(
                    f"EC2 platform only supports architectures: "
                    f"{', '.join(sorted(EC2_ARCHITECTURES))}. Got: {architecture}"
                )

        if compute in _EC2_COMPUTE_FORBIDS_ARCH:
            if architecture is not None:
                raise LabelValidationError(
                    f"EC2 compute type '{compute}' does not support "
                    f"architecture label. Got: {architecture}"
                )


def get_instance_type(parsed: dict[str, Any]) -> str | None:
    """Get EC2 instance type for the parsed labels.

    Args:
        parsed: Parsed labels from parse_labels()

    Returns:
        Instance type string or None for ECS
    """
    if parsed["platform"] == "ecs":
        return None
    key = f"{parsed['compute']}:{parsed['architecture']}"
    return _INSTANCE_TYPE_MAP.get(key)


def get_ecs_config(parsed: dict[str, Any]) -> dict[str, str] | None:
    """Get ECS Fargate configuration for the parsed labels.

    Args:
        parsed: Parsed labels from parse_labels()

    Returns:
        Dictionary with cpu and memory, or None for non-ECS/non-Fargate
    """
    if parsed["platform"] != "ecs":
        return None
    if parsed["compute"] == "fargate":
        return dict(_ECS_FARGATE_CONFIG)
    return None


def get_task_architecture(parsed: dict[str, Any]) -> str | None:
    """Get ECS task architecture for the parsed labels.

    Args:
        parsed: Parsed labels from parse_labels()

    Returns:
        ECS task architecture (X86_64 or ARM64) or None
    """
    if parsed["platform"] != "ecs":
        return None
    if parsed["architecture"] is None:
        return None
    return _ECS_TASK_ARCHITECTURE_MAP.get(parsed["architecture"])


def is_spot(parsed: dict[str, Any]) -> bool:
    """Check if the parsed labels indicate spot pricing.

    Args:
        parsed: Parsed labels from parse_labels()

    Returns:
        True if spot pricing, False otherwise
    """
    return parsed["pricing"] == "spot"


def get_runner_id_number(parsed: dict[str, Any]) -> int:
    """Extract the numeric part of the runner ID.

    Args:
        parsed: Parsed labels from parse_labels()

    Returns:
        Runner ID number

    Raises:
        LabelParseError: If runner ID format is invalid
    """
    match = _RUNNER_ID_PATTERN.match(parsed["runnerId"])
    if match:
        return int(match.group(1))
    raise LabelParseError(f"Invalid runner ID format: {parsed['runnerId']}")
