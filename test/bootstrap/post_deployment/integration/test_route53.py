def test_hosted_zone_exists(route53_client, config):
    domain_name = config['domain_name']
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = zones['HostedZones'][0]
    assert zone['Name'] == f"{domain_name}."


def test_hosted_zone_is_public(route53_client, config):
    domain_name = config['domain_name']
    zones = route53_client.list_hosted_zones_by_name(DNSName=f"{domain_name}.")
    zone = zones['HostedZones'][0]
    assert zone['Config']['PrivateZone'] is False
