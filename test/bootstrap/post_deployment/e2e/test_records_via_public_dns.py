"""End-to-end tests for DNS records via public DNS queries."""
import time
from botocore.exceptions import ClientError
import dns.resolver
import pytest


def test_can_create_and_resolve_record(
    route53_client, hosted_zone, config, public_dns_resolver
):
    """Test creating and resolving DNS record."""
    domain_name = config['domain_name']
    test_record_name = f"e2e-test.{domain_name}"
    test_value = "e2e-test-value-12345"
    try:
        change_id = route53_client.change_resource_record_sets(
            HostedZoneId=hosted_zone['Id'],
            ChangeBatch={
                'Changes': [{
                    'Action': 'UPSERT',
                    'ResourceRecordSet': {
                        'Name': test_record_name,
                        'Type': 'TXT',
                        'TTL': 60,
                        'ResourceRecords': [{'Value': f'"{test_value}"'}]
                    }
                }]
            }
        )['ChangeInfo']['Id']
        attempt = 0
        while attempt < 30:
            if route53_client.get_change(Id=change_id)['ChangeInfo']['Status'] == 'INSYNC':
                break
            time.sleep(1)
            attempt = attempt + 1
        resolved_value = str(public_dns_resolver.resolve(test_record_name, 'TXT')[0]).strip('"')
        assert resolved_value == test_value
    finally:
        try:
            route53_client.change_resource_record_sets(
                HostedZoneId=hosted_zone['Id'],
                ChangeBatch={
                    'Changes': [{
                        'Action': 'DELETE',
                        'ResourceRecordSet': {
                            'Name': test_record_name,
                            'Type': 'TXT',
                            'TTL': 60,
                            'ResourceRecords': [{'Value': f'"{test_value}"'}]
                        }
                    }]
                }
            )
        except ClientError:
            pass


def test_google_verification_record_resolves(public_dns_resolver, config):
    """Test that Google verification record resolves."""
    domain_name = config['domain_name']
    google_verification = config['google_site_verification']

    try:
        answers = public_dns_resolver.resolve(domain_name, 'TXT')
        txt_values = [str(rdata) for rdata in answers]

        expected_value = f'"google-site-verification={google_verification}"'
        assert any(expected_value in txt for txt in txt_values)
    except dns.resolver.NXDOMAIN:
        pytest.fail(f"Domain {domain_name} not found in DNS")
    except dns.resolver.NoAnswer:
        pytest.fail(f"No TXT records found for {domain_name}")


def test_google_verification_record_has_correct_content(public_dns_resolver, config):
    """Test that Google verification record has correct content."""
    domain_name = config['domain_name']
    google_verification = config['google_site_verification']

    answers = public_dns_resolver.resolve(domain_name, 'TXT')
    txt_values = [str(rdata).strip('"') for rdata in answers]

    expected_prefix = f"google-site-verification={google_verification}"
    assert any(expected_prefix in txt for txt in txt_values)


def test_mx_record_resolves(public_dns_resolver, config):
    """Test that MX record resolves."""
    domain_name = config['domain_name']

    try:
        answers = public_dns_resolver.resolve(domain_name, 'MX')
        assert len(answers) > 0
    except dns.resolver.NXDOMAIN:
        pytest.fail(f"Domain {domain_name} not found in DNS")
    except dns.resolver.NoAnswer:
        pytest.fail(f"No MX records found for {domain_name}")


def test_mx_record_returns_correct_priority(public_dns_resolver, config):
    """Test that MX record returns correct priority."""
    domain_name = config['domain_name']

    answers = public_dns_resolver.resolve(domain_name, 'MX')
    priorities = [rdata.preference for rdata in answers]
    assert 1 in priorities


def test_mx_record_returns_smtp_hostname(public_dns_resolver, config):
    """Test that MX record returns SMTP hostname."""
    domain_name = config['domain_name']

    answers = public_dns_resolver.resolve(domain_name, 'MX')
    exchanges = [str(rdata.exchange) for rdata in answers]
    assert any('smtp.google.com' in exchange for exchange in exchanges)


def test_mx_record_has_correct_ttl(public_dns_resolver, config):
    """Test that MX record has correct TTL."""
    domain_name = config['domain_name']

    answers = public_dns_resolver.resolve(domain_name, 'MX')
    assert answers.rrset.ttl == 300


def test_txt_record_has_correct_ttl(public_dns_resolver, config):
    """Test that TXT record has correct TTL."""
    domain_name = config['domain_name']

    answers = public_dns_resolver.resolve(domain_name, 'TXT')
    assert answers.rrset.ttl == 300
