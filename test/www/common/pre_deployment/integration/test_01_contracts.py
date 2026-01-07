"""Layer 1: Contract tests for www_common pre-deployment validation.

Verify local files that must work together are compatible. No AWS calls.
"""
import re

import pytest
from repo_utils import REPO_ROOT




SRC_DIR = REPO_ROOT / "src" / "www" / "common"


def _read_file(filename: str) -> str:
    """Read a file from the source directory."""
    with open(SRC_DIR / filename, encoding="utf-8") as f:
        return f.read()


def _extract_local_references(content: str) -> set:
    """Extract all local.* references from Terraform content."""
    return set(re.findall(r'local\.(\w+)', content))


def _extract_local_definitions(content: str) -> set:
    """Extract all local variable definitions from locals.tf content."""
    definitions = set()
    for match in re.finditer(r'^\s*(\w+)\s*=', content, re.MULTILINE):
        name = match.group(1)
        if name != 'locals':
            definitions.add(name)
    return definitions


def test_cloudfront_s3_local_references_exist_in_locals():
    """Verify all local.* references in cloudfront_s3.tf are defined in locals.tf."""
    cloudfront_content = _read_file("cloudfront_s3.tf")
    locals_content = _read_file("locals.tf")

    references = _extract_local_references(cloudfront_content)
    definitions = _extract_local_definitions(locals_content)

    missing = references - definitions
    assert not missing, (
        f"cloudfront_s3.tf references undefined locals: {missing}. "
        f"Defined locals: {definitions}"
    )


def test_certificate_dns_local_references_exist_in_locals():
    """Verify all local.* references in certificate_dns.tf are defined in locals.tf."""
    cert_content = _read_file("certificate_dns.tf")
    locals_content = _read_file("locals.tf")

    references = _extract_local_references(cert_content)
    definitions = _extract_local_definitions(locals_content)

    missing = references - definitions
    assert not missing, (
        f"certificate_dns.tf references undefined locals: {missing}. "
        f"Defined locals: {definitions}"
    )


def test_providers_local_references_exist_in_locals():
    """Verify all local.* references in providers.tf are defined in locals.tf."""
    providers_content = _read_file("providers.tf")
    locals_content = _read_file("locals.tf")

    references = _extract_local_references(providers_content)
    definitions = _extract_local_definitions(locals_content)

    missing = references - definitions
    assert not missing, (
        f"providers.tf references undefined locals: {missing}. "
        f"Defined locals: {definitions}"
    )


def test_lambda_edge_local_references_exist_in_locals():
    """Verify all local.* references in lambda_edge.tf are defined in locals.tf."""
    lambda_content = _read_file("lambda_edge.tf")
    locals_content = _read_file("locals.tf")

    references = _extract_local_references(lambda_content)
    definitions = _extract_local_definitions(locals_content)

    missing = references - definitions
    assert not missing, (
        f"lambda_edge.tf references undefined locals: {missing}. "
        f"Defined locals: {definitions}"
    )


def test_shared_module_source_declaration_exists():
    """Verify shared.tf has a module source declaration."""
    shared_content = _read_file("shared.tf")
    match = re.search(r'source\s*=\s*"([^"]+)"', shared_content)
    assert match, "shared.tf missing module source declaration"


def test_shared_module_source_path_exists():
    """Verify shared module source path exists on disk."""
    shared_content = _read_file("shared.tf")
    match = re.search(r'source\s*=\s*"([^"]+)"', shared_content)
    source_path = match.group(1)
    resolved_path = SRC_DIR / source_path
    assert resolved_path.exists(), (
        f"Module source path does not exist: {resolved_path}"
    )


def test_s3_bucket_module_source_declaration_exists():
    """Verify cloudfront_s3.tf has website_bucket module source declaration."""
    cloudfront_content = _read_file("cloudfront_s3.tf")
    match = re.search(
        r'module\s+"website_bucket"\s*\{[^}]*source\s*=\s*"([^"]+)"',
        cloudfront_content,
        re.DOTALL
    )
    assert match, "cloudfront_s3.tf missing website_bucket module source"


def test_s3_bucket_module_source_path_exists():
    """Verify S3 bucket module source path exists on disk."""
    cloudfront_content = _read_file("cloudfront_s3.tf")
    match = re.search(
        r'module\s+"website_bucket"\s*\{[^}]*source\s*=\s*"([^"]+)"',
        cloudfront_content,
        re.DOTALL
    )
    source_path = match.group(1)
    resolved_path = SRC_DIR / source_path
    assert resolved_path.exists(), (
        f"S3 bucket module source path does not exist: {resolved_path}"
    )


def test_waf_module_source_declaration_exists():
    """Verify cloudfront_s3.tf has website_waf module source declaration."""
    cloudfront_content = _read_file("cloudfront_s3.tf")
    match = re.search(
        r'module\s+"website_waf"\s*\{[^}]*source\s*=\s*"([^"]+)"',
        cloudfront_content,
        re.DOTALL
    )
    assert match, "cloudfront_s3.tf missing website_waf module source"


def test_waf_module_source_path_exists():
    """Verify WAF module source path exists on disk."""
    cloudfront_content = _read_file("cloudfront_s3.tf")
    match = re.search(
        r'module\s+"website_waf"\s*\{[^}]*source\s*=\s*"([^"]+)"',
        cloudfront_content,
        re.DOTALL
    )
    source_path = match.group(1)
    resolved_path = SRC_DIR / source_path
    assert resolved_path.exists(), (
        f"WAF module source path does not exist: {resolved_path}"
    )


def test_lambda_handler_file_exists():
    """Verify Lambda@Edge handler file exists."""
    handler_path = SRC_DIR / "lambda" / "spa_routing.py"
    assert handler_path.exists(), f"Lambda handler not found: {handler_path}"


def test_lambda_handler_has_handler_function():
    """Verify Lambda@Edge handler has the expected handler function."""
    handler_content = (SRC_DIR / "lambda" / "spa_routing.py").read_text()
    assert "def handler(" in handler_content, (
        "Lambda handler file missing 'def handler(' function"
    )


def test_lambda_edge_references_handler_file():
    """Verify lambda_edge.tf references the correct handler file."""
    lambda_content = _read_file("lambda_edge.tf")
    assert "spa_routing.py" in lambda_content, (
        "lambda_edge.tf does not reference spa_routing.py"
    )


def test_lambda_edge_has_handler_config():
    """Verify lambda_edge.tf has handler configuration."""
    lambda_content = _read_file("lambda_edge.tf")
    match = re.search(r'handler\s*=\s*"([^"]+)"', lambda_content)
    assert match, "lambda_edge.tf missing handler configuration"


def test_lambda_edge_handler_matches_module():
    """Verify lambda_edge.tf handler config matches Python module."""
    lambda_content = _read_file("lambda_edge.tf")
    match = re.search(r'handler\s*=\s*"([^"]+)"', lambda_content)
    handler_config = match.group(1) if match else ""
    assert handler_config == "spa_routing.handler", (
        f"Expected handler 'spa_routing.handler', got '{handler_config}'"
    )
