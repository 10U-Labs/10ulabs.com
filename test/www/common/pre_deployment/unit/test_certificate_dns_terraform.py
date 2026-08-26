def test_certificate_dns_file_exists(src_dir):
    assert (src_dir / "certificate_dns.tf").exists()


def test_route53_zone_data_source_defined(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'data "aws_route53_zone" "parent"' in content


def test_route53_zone_uses_local_domain_name(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "name = local.domain_name" in content


def test_acm_certificate_defined(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'resource "aws_acm_certificate" "website"' in content


def test_acm_certificate_uses_us_east_1_provider(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "provider = aws.us-east-1" in content


def test_acm_certificate_domain_name(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "domain_name               = local.www_fqdn" in content


def test_acm_certificate_san_apex(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "subject_alternative_names = [local.apex_fqdn]" in content


def test_acm_certificate_dns_validation(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'validation_method         = "DNS"' in content


def test_acm_certificate_create_before_destroy(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "create_before_destroy = true" in content


def test_cert_validation_record_defined(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'resource "aws_route53_record" "cert_validation"' in content


def test_cert_validation_record_for_each(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "domain_validation_options" in content


def test_cert_validation_allow_overwrite(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "allow_overwrite = true" in content


def test_acm_certificate_validation_defined(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'resource "aws_acm_certificate_validation" "website"' in content


def test_www_dns_record_defined(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'resource "aws_route53_record" "www"' in content


def test_www_dns_record_name(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "name    = local.www_fqdn" in content


def test_www_dns_record_type_a(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'type    = "A"' in content


def test_www_dns_record_alias_cloudfront(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "aws_cloudfront_distribution.website.domain_name" in content


def test_apex_dns_record_defined(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert 'resource "aws_route53_record" "apex"' in content


def test_apex_dns_record_name(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "name    = local.apex_fqdn" in content


def test_dns_records_use_hosted_zone(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "data.aws_route53_zone.parent.zone_id" in content


def test_alias_evaluate_target_health_false(src_dir):
    content = (src_dir / "certificate_dns.tf").read_text()
    assert "evaluate_target_health = false" in content
