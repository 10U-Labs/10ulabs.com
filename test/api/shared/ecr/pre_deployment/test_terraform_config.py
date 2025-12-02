import os
import re


def test_backend_tf_exists(ecr_dir):
    path = os.path.join(ecr_dir, 'backend.tf')
    assert os.path.exists(path)


def test_main_tf_exists(ecr_dir):
    path = os.path.join(ecr_dir, 'main.tf')
    assert os.path.exists(path)


def test_outputs_tf_exists(ecr_dir):
    path = os.path.join(ecr_dir, 'outputs.tf')
    assert os.path.exists(path)


def test_providers_tf_exists(ecr_dir):
    path = os.path.join(ecr_dir, 'providers.tf')
    assert os.path.exists(path)


def test_locals_tf_exists(ecr_dir):
    path = os.path.join(ecr_dir, 'locals.tf')
    assert os.path.exists(path)


def test_shared_tf_exists(ecr_dir):
    path = os.path.join(ecr_dir, 'shared.tf')
    assert os.path.exists(path)


def test_ecr_repository_name_defined(ecr_repository_name):
    assert ecr_repository_name is not None


def test_ecr_repository_name_not_empty(ecr_repository_name):
    assert len(ecr_repository_name) > 0


def test_backend_contains_s3_backend_block(backend_tf_content):
    pattern = r'backend\s+"s3"'
    assert re.search(pattern, backend_tf_content) is not None


def test_backend_bucket_is_correct(backend_tf_content):
    pattern = r'bucket\s*=\s*"10ulabs-terraform-state"'
    assert re.search(pattern, backend_tf_content) is not None


def test_backend_key_is_correct(backend_tf_content):
    pattern = r'key\s*=\s*"ecr/terraform\.tfstate"'
    assert re.search(pattern, backend_tf_content) is not None


def test_backend_region_is_correct(backend_tf_content):
    pattern = r'region\s*=\s*"us-east-1"'
    assert re.search(pattern, backend_tf_content) is not None


def test_backend_encrypt_is_true(backend_tf_content):
    pattern = r'encrypt\s*=\s*true'
    assert re.search(pattern, backend_tf_content) is not None


def test_backend_use_lockfile_is_true(backend_tf_content):
    pattern = r'use_lockfile\s*=\s*true'
    assert re.search(pattern, backend_tf_content) is not None


def test_required_terraform_version(backend_tf_content):
    pattern = r'required_version\s*=\s*">= 1\.14"'
    assert re.search(pattern, backend_tf_content) is not None


def test_required_aws_provider_version(backend_tf_content):
    pattern = r'version\s*=\s*"~> 5\.0"'
    assert re.search(pattern, backend_tf_content) is not None


def test_main_contains_ecr_repository_resource(main_tf_content):
    pattern = r'resource\s+"aws_ecr_repository"'
    assert re.search(pattern, main_tf_content) is not None


def test_main_contains_ecr_lifecycle_policy_resource(main_tf_content):
    pattern = r'resource\s+"aws_ecr_lifecycle_policy"'
    assert re.search(pattern, main_tf_content) is not None


def test_outputs_contains_repository_arn(outputs_tf_content):
    pattern = r'output\s+"repository_arn"'
    assert re.search(pattern, outputs_tf_content) is not None


def test_outputs_contains_repository_name(outputs_tf_content):
    pattern = r'output\s+"repository_name"'
    assert re.search(pattern, outputs_tf_content) is not None


def test_outputs_contains_repository_url(outputs_tf_content):
    pattern = r'output\s+"repository_url"'
    assert re.search(pattern, outputs_tf_content) is not None
