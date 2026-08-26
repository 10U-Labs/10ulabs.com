from typing import Dict

import pytest

from test_fixtures.integration import get_aws_account_id_via_cli


@pytest.fixture(scope="module")
def config(shared_config) -> Dict[str, str]:
    result = {
        'aws_region': shared_config['aws_region'],
        'aws_account_id': get_aws_account_id_via_cli(),
        'domain_name': shared_config['domain_name'],
        'api_fqdn': f"api.{shared_config['domain_name']}",
        'resource_prefix': shared_config['resource_prefix']
    }
    return result
