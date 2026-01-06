"""Unit tests for www/common outputs.tf configuration."""


def test_outputs_file_exists(src_dir):
    """Verify outputs.tf file exists."""
    assert (src_dir / "outputs.tf").exists()


def test_output_bucket_name_defined(src_dir):
    """Verify bucket_name output is defined."""
    content = (src_dir / "outputs.tf").read_text()
    assert 'output "bucket_name"' in content


def test_output_bucket_name_value(src_dir):
    """Verify bucket_name output uses module.website_bucket.bucket_id."""
    content = (src_dir / "outputs.tf").read_text()
    assert "value = module.website_bucket.bucket_id" in content


def test_output_cloudfront_distribution_id_defined(src_dir):
    """Verify cloudfront_distribution_id output is defined."""
    content = (src_dir / "outputs.tf").read_text()
    assert 'output "cloudfront_distribution_id"' in content


def test_output_cloudfront_distribution_id_value(src_dir):
    """Verify cloudfront_distribution_id output value."""
    content = (src_dir / "outputs.tf").read_text()
    assert "value = aws_cloudfront_distribution.website.id" in content


def test_output_cloudfront_domain_name_defined(src_dir):
    """Verify cloudfront_domain_name output is defined."""
    content = (src_dir / "outputs.tf").read_text()
    assert 'output "cloudfront_domain_name"' in content


def test_output_cloudfront_domain_name_value(src_dir):
    """Verify cloudfront_domain_name output value."""
    content = (src_dir / "outputs.tf").read_text()
    assert "value = aws_cloudfront_distribution.website.domain_name" in content


def test_output_website_domain_name_defined(src_dir):
    """Verify website_domain_name output is defined."""
    content = (src_dir / "outputs.tf").read_text()
    assert 'output "website_domain_name"' in content


def test_output_website_domain_name_value(src_dir):
    """Verify website_domain_name output uses local.www_fqdn."""
    content = (src_dir / "outputs.tf").read_text()
    assert "value = local.www_fqdn" in content


def test_output_website_url_defined(src_dir):
    """Verify website_url output is defined."""
    content = (src_dir / "outputs.tf").read_text()
    assert 'output "website_url"' in content


def test_output_website_url_uses_https(src_dir):
    """Verify website_url output uses https."""
    content = (src_dir / "outputs.tf").read_text()
    assert 'value = "https://${local.www_fqdn}"' in content
