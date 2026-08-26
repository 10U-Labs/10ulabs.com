def test_outputs_file_exists(src_dir):
    assert (src_dir / "outputs.tf").exists()


def test_output_bucket_name_defined(src_dir):
    content = (src_dir / "outputs.tf").read_text()
    assert 'output "bucket_name"' in content


def test_output_bucket_name_value(src_dir):
    content = (src_dir / "outputs.tf").read_text()
    assert "value = module.website_bucket.bucket_id" in content


def test_output_cloudfront_distribution_id_defined(src_dir):
    content = (src_dir / "outputs.tf").read_text()
    assert 'output "cloudfront_distribution_id"' in content


def test_output_cloudfront_distribution_id_value(src_dir):
    content = (src_dir / "outputs.tf").read_text()
    assert "value = aws_cloudfront_distribution.website.id" in content


def test_output_cloudfront_domain_name_defined(src_dir):
    content = (src_dir / "outputs.tf").read_text()
    assert 'output "cloudfront_domain_name"' in content


def test_output_cloudfront_domain_name_value(src_dir):
    content = (src_dir / "outputs.tf").read_text()
    assert "value = aws_cloudfront_distribution.website.domain_name" in content


def test_output_website_domain_name_defined(src_dir):
    content = (src_dir / "outputs.tf").read_text()
    assert 'output "website_domain_name"' in content


def test_output_website_domain_name_value(src_dir):
    content = (src_dir / "outputs.tf").read_text()
    assert "value = local.www_fqdn" in content


def test_output_website_url_defined(src_dir):
    content = (src_dir / "outputs.tf").read_text()
    assert 'output "website_url"' in content


def test_output_website_url_uses_https(src_dir):
    content = (src_dir / "outputs.tf").read_text()
    assert 'value = "https://${local.www_fqdn}"' in content
