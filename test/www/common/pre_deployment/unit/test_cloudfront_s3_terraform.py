from pathlib import Path
def test_cloudfront_s3_file_exists(src_dir: Path) -> None:
    assert (src_dir / "cloudfront_s3.tf").exists()


def test_website_bucket_module_defined(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'module "website_bucket"' in content


def test_website_bucket_module_source(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'source = "../../../lib/terraform/s3_bucket"' in content


def test_website_bucket_uses_local_bucket_name(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "bucket_name         = local.website_bucket_name" in content


def test_website_bucket_force_destroy_disabled(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "force_destroy       = false" in content


def test_website_bucket_does_not_configure_versioning(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "versioning" not in content


def test_cloudfront_origin_access_control_defined(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'resource "aws_cloudfront_origin_access_control" "website"' in content


def test_cloudfront_oac_s3_origin_type(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'origin_access_control_origin_type = "s3"' in content


def test_cloudfront_oac_signing_always(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'signing_behavior                  = "always"' in content


def test_cloudfront_oac_sigv4_protocol(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'signing_protocol                  = "sigv4"' in content


def test_bucket_policy_document_defined(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'data "aws_iam_policy_document" "website_bucket_policy"' in content


def test_bucket_policy_allows_cloudfront_principal(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'identifiers = ["cloudfront.amazonaws.com"]' in content


def test_bucket_policy_allows_get_object(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert '"s3:GetObject"' in content


def test_s3_bucket_policy_resource_defined(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'resource "aws_s3_bucket_policy" "website"' in content


def test_response_headers_policy_defined(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'resource "aws_cloudfront_response_headers_policy" "website"' in content


def test_hsts_max_age_configured(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "access_control_max_age_sec = 31536000" in content


def test_hsts_include_subdomains_enabled(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "include_subdomains         = true" in content


def test_hsts_preload_enabled(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "preload                    = true" in content


def test_cache_policy_defined(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'resource "aws_cloudfront_cache_policy" "website"' in content


def test_cache_policy_default_ttl(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "default_ttl = 86400" in content


def test_cache_policy_brotli_enabled(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "enable_accept_encoding_brotli = true" in content


def test_cache_policy_gzip_enabled(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "enable_accept_encoding_gzip   = true" in content


def test_cloudfront_distribution_defined(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'resource "aws_cloudfront_distribution" "website"' in content


def test_cloudfront_distribution_enabled(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "enabled         = true" in content


def test_cloudfront_ipv6_disabled(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "is_ipv6_enabled = false" in content


def test_cloudfront_viewer_protocol_redirect_https(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'viewer_protocol_policy = "redirect-to-https"' in content


def test_cloudfront_compress_enabled(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "compress               = true" in content


def test_cloudfront_lambda_function_association(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "lambda_function_association {" in content


def test_cloudfront_lambda_viewer_request(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'event_type   = "viewer-request"' in content


def test_cloudfront_custom_error_403(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "error_code         = 403" in content


def test_cloudfront_custom_error_404(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "error_code         = 404" in content


def test_cloudfront_ssl_sni_only(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'ssl_support_method       = "sni-only"' in content


def test_cloudfront_tls_minimum_version(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'minimum_protocol_version = "TLSv1.2_2021"' in content


def test_cloudfront_geo_restriction_none(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'restriction_type = "none"' in content


def test_cloudfront_depends_on_certificate_validation(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert "aws_acm_certificate_validation.website" in content


def test_cors_s3_origin_policy_data_source(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'data "aws_cloudfront_origin_request_policy" "cors_s3_origin"' in content


def test_cors_policy_name_managed(src_dir: Path) -> None:
    content = (src_dir / "cloudfront_s3.tf").read_text()
    assert 'name = "Managed-CORS-S3Origin"' in content
