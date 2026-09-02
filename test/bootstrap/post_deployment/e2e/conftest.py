from typing import Any

import dns.resolver
import pytest


@pytest.fixture(scope="module")
def public_dns_resolver(zone_nameservers: Any) -> Any:
    ns_ip = dns.resolver.resolve(zone_nameservers[0], 'A')[0].to_text()
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [ns_ip]
    return resolver
