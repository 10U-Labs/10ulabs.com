import re

from repo_utils import REPO_ROOT


SRC_DIR = REPO_ROOT / "src" / "www" / "common"


def _read_file(filename: str) -> str:
    with open(SRC_DIR / filename, encoding="utf-8") as f:
        return f.read()


def _extract_local_references(content: str) -> set:
    return set(re.findall(r'local\.(\w+)', content))


def _extract_local_definitions(content: str) -> set:
    definitions = set()
    for match in re.finditer(r'^\s*(\w+)\s*=', content, re.MULTILINE):
        name = match.group(1)
        if name != 'locals':
            definitions.add(name)
    return definitions


def test_cloudfront_s3_local_references_exist_in_locals() -> None:
    cloudfront_content = _read_file("cloudfront_s3.tf")
    locals_content = _read_file("locals.tf")

    references = _extract_local_references(cloudfront_content)
    definitions = _extract_local_definitions(locals_content)

    missing = references - definitions
    assert not missing, (
        f"cloudfront_s3.tf references undefined locals: {missing}. "
        f"Defined locals: {definitions}"
    )


def test_certificate_dns_local_references_exist_in_locals() -> None:
    cert_content = _read_file("certificate_dns.tf")
    locals_content = _read_file("locals.tf")

    references = _extract_local_references(cert_content)
    definitions = _extract_local_definitions(locals_content)

    missing = references - definitions
    assert not missing, (
        f"certificate_dns.tf references undefined locals: {missing}. "
        f"Defined locals: {definitions}"
    )


def test_providers_local_references_exist_in_locals() -> None:
    providers_content = _read_file("providers.tf")
    locals_content = _read_file("locals.tf")

    references = _extract_local_references(providers_content)
    definitions = _extract_local_definitions(locals_content)

    missing = references - definitions
    assert not missing, (
        f"providers.tf references undefined locals: {missing}. "
        f"Defined locals: {definitions}"
    )


def test_lambda_edge_local_references_exist_in_locals() -> None:
    lambda_content = _read_file("lambda_edge.tf")
    locals_content = _read_file("locals.tf")

    references = _extract_local_references(lambda_content)
    definitions = _extract_local_definitions(locals_content)

    missing = references - definitions
    assert not missing, (
        f"lambda_edge.tf references undefined locals: {missing}. "
        f"Defined locals: {definitions}"
    )


def test_shared_module_source_declaration_exists() -> None:
    shared_content = _read_file("shared.tf")
    match = re.search(r'source\s*=\s*"([^"]+)"', shared_content)
    assert match, "shared.tf missing module source declaration"


def test_shared_module_source_path_exists() -> None:
    shared_content = _read_file("shared.tf")
    match = re.search(r'source\s*=\s*"([^"]+)"', shared_content)
    source_path = match.group(1) if match else "(no module source declared)"
    resolved_path = SRC_DIR / source_path
    assert resolved_path.exists(), (
        f"Module source path does not exist: {resolved_path}"
    )


def test_s3_bucket_module_source_declaration_exists() -> None:
    cloudfront_content = _read_file("cloudfront_s3.tf")
    match = re.search(
        r'module\s+"website_bucket"\s*\{[^}]*source\s*=\s*"([^"]+)"',
        cloudfront_content,
        re.DOTALL
    )
    assert match, "cloudfront_s3.tf missing website_bucket module source"


def test_s3_bucket_module_source_path_exists() -> None:
    cloudfront_content = _read_file("cloudfront_s3.tf")
    match = re.search(
        r'module\s+"website_bucket"\s*\{[^}]*source\s*=\s*"([^"]+)"',
        cloudfront_content,
        re.DOTALL
    )
    source_path = match.group(1) if match else "(no module source declared)"
    resolved_path = SRC_DIR / source_path
    assert resolved_path.exists(), (
        f"S3 bucket module source path does not exist: {resolved_path}"
    )


def test_lambda_handler_file_exists() -> None:
    handler_path = SRC_DIR / "lambda" / "handler.py"
    assert handler_path.exists(), f"Lambda handler not found: {handler_path}"


def test_lambda_handler_has_handler_function() -> None:
    handler_content = (SRC_DIR / "lambda" / "handler.py").read_text()
    assert "def lambda_handler(" in handler_content, (
        "Lambda handler file missing 'def lambda_handler(' function"
    )


def test_lambda_edge_references_handler_file() -> None:
    lambda_content = _read_file("lambda_edge.tf")
    assert "lambda/handler.py" in lambda_content, (
        "lambda_edge.tf does not reference lambda/handler.py"
    )


def test_lambda_edge_has_handler_config() -> None:
    lambda_content = _read_file("lambda_edge.tf")
    match = re.search(r'handler\s*=\s*"([^"]+)"', lambda_content)
    assert match, "lambda_edge.tf missing handler configuration"


def test_lambda_edge_handler_matches_module() -> None:
    lambda_content = _read_file("lambda_edge.tf")
    match = re.search(r'handler\s*=\s*"([^"]+)"', lambda_content)
    handler_config = match.group(1) if match else ""
    assert handler_config == "handler.lambda_handler", (
        f"Expected handler 'handler.lambda_handler', got '{handler_config}'"
    )
