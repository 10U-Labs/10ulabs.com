"""Test fixtures for workflowctl tests.

This module provides shared graph constants for workflowctl unit tests.
"""
from typing import Any, Dict


# Extended dependency graph with deep linear chain for comprehensive testing.
# Use this for testing deep ancestor/descendant traversal algorithms.
EXTENDED_LINEAR_GRAPH: Dict[str, Dict[str, Any]] = {
    "bootstrap": {
        "name": "Bootstrap",
        "depends_on": [],
        "paths": [".github/workflows/bootstrap.yml", "src/bootstrap/**"],
    },
    "www_shared": {
        "name": "WWW Shared",
        "depends_on": ["bootstrap"],
        "paths": [".github/workflows/www_shared.yml", "src/www/shared/**"],
    },
    "api": {
        "name": "API",
        "depends_on": ["www_shared"],
        "paths": [".github/workflows/api_shared_routing.yml", "src/api/shared/routing/**"],
    },
    "health": {
        "name": "Health",
        "depends_on": ["api"],
        "paths": [
            ".github/workflows/api_operational_health.yml",
            "src/api/operational/health/**",
        ],
    },
    "ecr": {
        "name": "ECR",
        "depends_on": ["health"],
        "paths": [".github/workflows/api_shared_ecr.yml", "src/api/shared/ecr/**"],
    },
    "ecs_images": {
        "name": "Image for ECS Runners",
        "depends_on": ["ecr"],
        "paths": [
            ".github/workflows/api_endpoint_v1_runners_ecs_images.yml",
            "src/api/endpoints/runners/ecs/images/**",
        ],
    },
    "ecs_runner": {
        "name": "ECS Runner",
        "depends_on": ["ecs_images"],
        "paths": [
            ".github/workflows/api_endpoint_v1_runners_ecs.yml",
            "src/api/endpoints/runners/ecs/**",
        ],
    },
    "contact": {
        "name": "Contact",
        "depends_on": ["ecs_runner"],
        "paths": [
            ".github/workflows/api_endpoint_v1_contact.yml",
            "src/api/endpoints/contact/**",
        ],
    },
}

# Diamond-shaped dependency graph for testing multi-parent scenarios.
# www_app depends on both www_shared and api_shared (diamond pattern).
DIAMOND_GRAPH: Dict[str, Dict[str, Any]] = {
    "bootstrap": {"name": "Bootstrap", "depends_on": []},
    "www_shared": {"name": "WWW Shared", "depends_on": ["bootstrap"]},
    "api_shared": {"name": "API Shared", "depends_on": ["bootstrap"]},
    "www_app": {"name": "WWW App", "depends_on": ["www_shared", "api_shared"]},
}

# Minimal dependency graph for basic utility testing.
# Use this for simple tests that don't need complex graph structures.
MINIMAL_GRAPH: Dict[str, Dict[str, Any]] = {
    "bootstrap": {
        "name": "Ensuring bootstrap infrastructure exists and is properly configured",
        "depends_on": [],
        "paths": ["src/bootstrap/**"],
    },
    "www_shared": {
        "name": "WWW Shared",
        "depends_on": ["bootstrap"],
        "paths": ["src/www/shared/**"],
    },
    "api_shared_routing": {
        "name": "Ensuring API backend exists and is properly configured",
        "depends_on": ["www_shared"],
        "paths": ["src/api/backend/**"],
    },
}
