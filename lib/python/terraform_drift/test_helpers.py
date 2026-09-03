import subprocess
from pathlib import Path

import pytest

from terraform_drift import (
    check_resource_exists,
    get_planned_creates,
)


def _has_existing_state(terraform_dir: Path) -> bool:
    result = subprocess.run(
        ["terraform", "state", "list"],
        cwd=terraform_dir,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    return result.returncode == 0 and len(result.stdout.strip()) > 0


def create_orphaned_resource_tests(
    terraform_dir: Path,
    region: str = "us-east-2",
    require_existing_state: bool = False,
) -> type:
    class TestOrphanedResources:
        def test_terraform_initialized(self) -> None:
            terraform_lock = terraform_dir / ".terraform.lock.hcl"
            print(f"\nChecking terraform initialization: {terraform_dir}")
            assert terraform_lock.exists(), (
                f"Terraform not initialized in {terraform_dir}. "
                f"Run 'terraform init' first."
            )
            print("  Terraform is initialized")

        def test_no_orphaned_resources(self) -> None:
            if require_existing_state and not _has_existing_state(terraform_dir):
                pytest.skip("Cold state - no prior Terraform state to validate against")

            print("\n" + "=" * 60)
            print("Running terraform plan to detect resources to create...")
            print(f"  Directory: {terraform_dir}")
            print(f"  Region: {region}")

            creates = get_planned_creates(terraform_dir)

            print(f"\nFound {len(creates)} resources to create:")
            for resource in creates:
                print(f"  - {resource['type']}: {resource['name']} ({resource['address']})")

            if not creates:
                print("\nNo resources to create - nothing to check for orphans")
                print("=" * 60)
                return

            orphaned = []
            for resource in creates:
                resource_type = resource["type"]
                name = resource["name"]
                tf_address = resource["address"]
                print(f"\nChecking {resource_type}: {name}")
                exists = check_resource_exists(resource_type, name, region)
                print(f"  Exists in AWS: {exists}")
                if exists:
                    orphaned.append((resource_type, name, tf_address))

            print("=" * 60)

            if orphaned:
                msg = f"\n\n{'!'*60}\n"
                msg += f"ORPHANED RESOURCES DETECTED ({len(orphaned)})\n"
                msg += f"{'!'*60}\n\n"
                msg += "The following resources exist in AWS but NOT in Terraform state.\n"
                msg += "This will cause 'terraform apply' to fail or hang.\n\n"
                msg += "FIX: Run these commands before applying:\n\n"
                for resource_type, name, tf_address in orphaned:
                    msg += f"    terraform import {tf_address} {name}\n"
                msg += f"\n{'!'*60}"
                pytest.fail(msg)

    return TestOrphanedResources
