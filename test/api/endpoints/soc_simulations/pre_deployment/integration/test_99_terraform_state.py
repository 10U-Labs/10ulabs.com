"""Tests to detect Terraform state drift for simulation_soc endpoint.

These tests verify that resources Terraform plans to create don't already
exist in AWS. If they do, it indicates the resource was created outside
of Terraform or the state was lost, and needs to be imported.
"""
from repo_utils import REPO_ROOT
from terraform_drift.test_helpers import create_orphaned_resource_tests

SIMULATION_SOC_SRC = REPO_ROOT / "src" / "api" / "endpoints" / "simulation_soc"

TestOrphanedResources = create_orphaned_resource_tests(
    terraform_dir=SIMULATION_SOC_SRC,
    region="us-east-2",
)
