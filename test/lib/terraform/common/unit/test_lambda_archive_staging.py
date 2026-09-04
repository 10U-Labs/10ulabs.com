from pathlib import Path

import pytest

from repo_utils import REPO_ROOT
from terraform_config import packaged_lambda_archives

SCRATCH_DIRECTORY_NAME = ".terraform"


STAGED_ARCHIVES = [
    ("src/api/common/routing/lambda.tf",
     ".terraform/lambda_packages/catchall_handler.zip"),
    ("src/api/endpoints/contact_submissions/lambda.tf",
     ".terraform/lambda_packages/contact_handler.zip"),
    ("src/api/endpoints/rack_configurations/lambda.tf",
     ".terraform/lambda_packages/handler.zip"),
    ("src/api/endpoints/sessions/analytics.tf",
     ".terraform/lambda_packages/export_lambda.zip"),
    ("src/api/endpoints/sessions/lambda.tf",
     ".terraform/lambda_packages/handler.zip"),
    ("src/api/operational/diagnostics/lambda.tf",
     ".terraform/lambda_packages/diagnostics_handler.zip"),
    ("src/api/operational/health/lambda.tf",
     ".terraform/lambda_packages/health_handler.zip"),
    ("src/www/common/lambda_edge.tf",
     ".terraform/lambda_packages/spa_routing.zip"),
]

FILES_DECLARING_A_PACKAGE = [
    ("src/api/common/routing/lambda.tf", 1),
    ("src/api/endpoints/contact_submissions/lambda.tf", 1),
    ("src/api/endpoints/rack_configurations/lambda.tf", 1),
    ("src/api/endpoints/sessions/analytics.tf", 1),
    ("src/api/endpoints/sessions/lambda.tf", 1),
    ("src/api/operational/diagnostics/lambda.tf", 1),
    ("src/api/operational/health/lambda.tf", 1),
    ("src/www/common/lambda_edge.tf", 1),
]


@pytest.mark.parametrize("tf_file, archive", STAGED_ARCHIVES)
def test_packaged_function_is_staged_in_the_deployment_scratch_directory(
    tf_file: str, archive: str
) -> None:
    assert Path(archive).parts[:1] == (SCRATCH_DIRECTORY_NAME,), (
        f"{tf_file} writes its archive to {archive}, so a build output lands in a "
        f"directory holding source; every other deployed function is staged beneath "
        f"{SCRATCH_DIRECTORY_NAME}, which is where the deployment tool already keeps "
        f"its own working files"
    )


@pytest.mark.parametrize("tf_file, declared", FILES_DECLARING_A_PACKAGE)
def test_every_packaging_configuration_names_the_archive_it_writes(
    tf_file: str, declared: int
) -> None:
    read = len(packaged_lambda_archives(REPO_ROOT / tf_file))
    assert read == declared, (
        f"{tf_file} declares {declared} packages and {read} archive paths were read "
        f"from it, so a package is staged somewhere nothing checks; the check above "
        f"reads the paths it finds and cannot report on one it never saw"
    )
