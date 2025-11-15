import dns.resolver


def test_each_nameserver_resolves_soa(route53_client, hosted_zone, config):
    domain_name = config['domain_name']
    ns_response = route53_client.get_hosted_zone(Id=hosted_zone['Id'])
    name_servers = ns_response['DelegationSet']['NameServers']

    for ns in name_servers:
        ns_ip = dns.resolver.resolve(ns, 'A')[0].to_text()
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [ns_ip]
        answers = resolver.resolve(domain_name, 'SOA')
        if len(answers) == 0:
            pytest.fail(f"Name server {ns} did not respond with SOA record")


def test_can_create_and_resolve_record_via_route53_nameserver(route53_client, hosted_zone, config):
    import time
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
        for _ in range(30):
            change_status = route53_client.get_change(Id=change_id)
            if change_status['ChangeInfo']['Status'] == 'INSYNC':
                break
            time.sleep(1)

        ns_ip = dns.resolver.resolve(name_servers[0], 'A')[0].to_text()
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [ns_ip]

        answers = resolver.resolve(test_record_name, 'TXT')
        resolved_value = str(answers[0]).strip('"')

        assert resolved_value == test_value, f"Expected {test_value}, got {resolved_value}"

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
