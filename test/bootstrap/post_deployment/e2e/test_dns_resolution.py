import time
import dns.resolver
import pytest


def test_can_create_and_resolve_record_via_route53_nameserver(route53_client, hosted_zone, config):
    domain_name = config['domain_name']
    ns_response = route53_client.get_hosted_zone(Id=hosted_zone['Id'])
    name_servers = ns_response['DelegationSet']['NameServers']
    test_record_name = f"e2e-test.{domain_name}"
    test_value = "e2e-test-value-12345"
    try:
        change_response = route53_client.change_resource_record_sets(
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
        )
        change_id = change_response['ChangeInfo']['Id']
        max_attempts = 30
        attempt = 0
        while attempt < max_attempts:
            change_status = route53_client.get_change(Id=change_id)
            if change_status['ChangeInfo']['Status'] == 'INSYNC':
                break
            time.sleep(1)
            attempt = attempt + 1
        ns_ip = dns.resolver.resolve(name_servers[0], 'A')[0].to_text()
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [ns_ip]
        answers = resolver.resolve(test_record_name, 'TXT')
        resolved_value = str(answers[0]).strip('"')
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
        except:
            pass


def test_google_verification_record_resolves_via_public_dns(route53_client, config):
    domain_name = config['domain_name']
    google_verification = config['google_site_verification']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    zone_details = route53_client.get_hosted_zone(Id=zone['Id'])
    name_servers = zone_details['DelegationSet']['NameServers']

    ns_ip = dns.resolver.resolve(name_servers[0], 'A')[0].to_text()

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [ns_ip]

    try:
        answers = resolver.resolve(domain_name, 'TXT')
        txt_values = [str(rdata) for rdata in answers]

        expected_value = f'"google-site-verification={google_verification}"'
        assert any(expected_value in txt for txt in txt_values)
    except dns.resolver.NXDOMAIN:
        pytest.fail(f"Domain {domain_name} not found in DNS")
    except dns.resolver.NoAnswer:
        pytest.fail(f"No TXT records found for {domain_name}")


def test_google_verification_record_has_correct_content(route53_client, config):
    domain_name = config['domain_name']
    google_verification = config['google_site_verification']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    zone_details = route53_client.get_hosted_zone(Id=zone['Id'])
    name_servers = zone_details['DelegationSet']['NameServers']

    ns_ip = dns.resolver.resolve(name_servers[0], 'A')[0].to_text()

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [ns_ip]

    answers = resolver.resolve(domain_name, 'TXT')
    txt_values = [str(rdata).strip('"') for rdata in answers]

    expected_prefix = f"google-site-verification={google_verification}"
    assert any(expected_prefix in txt for txt in txt_values)


def test_mx_record_resolves_via_public_dns(route53_client, config):
    domain_name = config['domain_name']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    zone_details = route53_client.get_hosted_zone(Id=zone['Id'])
    name_servers = zone_details['DelegationSet']['NameServers']

    ns_ip = dns.resolver.resolve(name_servers[0], 'A')[0].to_text()

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [ns_ip]

    try:
        answers = resolver.resolve(domain_name, 'MX')
        assert len(answers) > 0
    except dns.resolver.NXDOMAIN:
        pytest.fail(f"Domain {domain_name} not found in DNS")
    except dns.resolver.NoAnswer:
        pytest.fail(f"No MX records found for {domain_name}")


def test_mx_record_returns_correct_priority_via_dns(route53_client, config):
    domain_name = config['domain_name']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    zone_details = route53_client.get_hosted_zone(Id=zone['Id'])
    name_servers = zone_details['DelegationSet']['NameServers']

    ns_ip = dns.resolver.resolve(name_servers[0], 'A')[0].to_text()

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [ns_ip]

    answers = resolver.resolve(domain_name, 'MX')
    priorities = [rdata.preference for rdata in answers]
    assert 1 in priorities


def test_mx_record_returns_smtp_hostname_via_dns(route53_client, config):
    domain_name = config['domain_name']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    zone_details = route53_client.get_hosted_zone(Id=zone['Id'])
    name_servers = zone_details['DelegationSet']['NameServers']

    ns_ip = dns.resolver.resolve(name_servers[0], 'A')[0].to_text()

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [ns_ip]

    answers = resolver.resolve(domain_name, 'MX')
    exchanges = [str(rdata.exchange) for rdata in answers]
    assert any('smtp.google.com' in exchange for exchange in exchanges)


def test_mx_record_has_correct_ttl_in_dns_response(route53_client, config):
    domain_name = config['domain_name']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    zone_details = route53_client.get_hosted_zone(Id=zone['Id'])
    name_servers = zone_details['DelegationSet']['NameServers']

    ns_ip = dns.resolver.resolve(name_servers[0], 'A')[0].to_text()

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [ns_ip]

    answers = resolver.resolve(domain_name, 'MX')
    assert answers.rrset.ttl == 300


def test_txt_record_has_correct_ttl_in_dns_response(route53_client, config):
    domain_name = config['domain_name']

    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = None
    for z in zones['HostedZones']:
        if z['Name'] == f"{domain_name}.":
            zone = z
            break

    zone_details = route53_client.get_hosted_zone(Id=zone['Id'])
    name_servers = zone_details['DelegationSet']['NameServers']

    ns_ip = dns.resolver.resolve(name_servers[0], 'A')[0].to_text()

    resolver = dns.resolver.Resolver()
    resolver.nameservers = [ns_ip]

    answers = resolver.resolve(domain_name, 'TXT')
    assert answers.rrset.ttl == 300
