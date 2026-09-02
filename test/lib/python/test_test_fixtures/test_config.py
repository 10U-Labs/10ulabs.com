import tempfile
from functools import partial
from pathlib import Path
from typing import Callable, Dict

import pytest

from test_fixtures.config import (
    parse_tfvars_file,
    parse_locals_file,
    create_simple_config,
    create_website_config,
    add_derived_config,
)


def write_temporary_file(content: str, suffix: str) -> Path:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False
    ) as handle:
        handle.write(content)
        handle.flush()
        return Path(handle.name)


@pytest.fixture(name="tfvars_file")
def fixture_tfvars_file() -> Callable[[str], Path]:
    return partial(write_temporary_file, suffix=".tfvars")


@pytest.fixture(name="tf_file")
def fixture_tf_file() -> Callable[[str], Path]:
    return partial(write_temporary_file, suffix=".tf")


@pytest.fixture(name="base_shared_config")
def fixture_base_shared_config() -> Dict[str, str]:
    return {'aws_region': 'us-east-1', 'domain_name': 'example.com'}


class TestParseTfvarsFile:
    def test_parses_unquoted_value(self, tfvars_file: Callable[[str], Path]) -> None:
        result = parse_tfvars_file(tfvars_file('key = value\n'))
        assert result['key'] == 'value'

    def test_parses_quoted_value(self, tfvars_file: Callable[[str], Path]) -> None:
        result = parse_tfvars_file(tfvars_file('key = "quoted value"\n'))
        assert result['key'] == 'quoted value'

    def test_ignores_comment_lines(self, tfvars_file: Callable[[str], Path]) -> None:
        result = parse_tfvars_file(tfvars_file('# this is a comment\nkey = value\n'))
        assert len(result) == 1

    def test_ignores_empty_lines(self, tfvars_file: Callable[[str], Path]) -> None:
        result = parse_tfvars_file(tfvars_file('\n\nkey = value\n\n'))
        assert result['key'] == 'value'

    def test_returns_empty_dict_for_empty_file(self, tfvars_file: Callable[[str], Path]) -> None:
        result = parse_tfvars_file(tfvars_file(''))
        assert not result

    def test_parses_multiple_key_value_pairs(self, tfvars_file: Callable[[str], Path]) -> None:
        result = parse_tfvars_file(tfvars_file('key1 = "value1"\nkey2 = "value2"\n'))
        assert len(result) == 2

    def test_handles_equals_sign_spacing(self, tfvars_file: Callable[[str], Path]) -> None:
        result = parse_tfvars_file(tfvars_file('key="value"\n'))
        assert result['key'] == 'value'

    def test_ignores_malformed_lines(self, tfvars_file: Callable[[str], Path]) -> None:
        result = parse_tfvars_file(tfvars_file('this line has no equals sign\nkey = "value"\n'))
        assert len(result) == 1


class TestParseLocalsFile:
    def test_parses_quoted_string_value(self, tf_file: Callable[[str], Path]) -> None:
        result = parse_locals_file(tf_file('  resource_prefix = "my-prefix"\n'))
        assert result['resource_prefix'] == 'my-prefix'

    def test_ignores_locals_block_declaration(self, tf_file: Callable[[str], Path]) -> None:
        result = parse_locals_file(tf_file('locals {\n  key = "value"\n}\n'))
        assert 'locals' not in result

    def test_ignores_comment_lines(self, tf_file: Callable[[str], Path]) -> None:
        result = parse_locals_file(tf_file('# comment\n  key = "value"\n'))
        assert len(result) == 1

    def test_resolves_module_shared_reference(self, tf_file: Callable[[str], Path]) -> None:
        shared_config = {'aws_region': 'us-east-2'}
        result = parse_locals_file(
            tf_file('  region = module.common.aws_region\n'),
            shared_config
        )
        assert result['region'] == 'us-east-2'

    def test_returns_empty_for_unresolved_reference(self, tf_file: Callable[[str], Path]) -> None:
        shared_config = {'other_key': 'value'}
        result = parse_locals_file(
            tf_file('  region = module.common.missing_key\n'),
            shared_config
        )
        assert result['region'] == ''

    def test_ignores_module_reference_without_shared_config(
        self,
        tf_file: Callable[[str], Path]
    ) -> None:
        result = parse_locals_file(tf_file('  region = module.common.aws_region\n'), None)
        assert 'region' not in result

    def test_returns_empty_dict_for_empty_file(self, tf_file: Callable[[str], Path]) -> None:
        result = parse_locals_file(tf_file(''))
        assert not result

    def test_ignores_malformed_lines_with_equals(self, tf_file: Callable[[str], Path]) -> None:
        result = parse_locals_file(tf_file('  } = {\n  key = "value"\n'))
        assert len(result) == 1


class TestCreateSimpleConfig:
    def test_includes_aws_region_from_shared_config(
        self,
        tfvars_file: Callable[[str], Path]
    ) -> None:
        shared_config = {'aws_region': 'us-west-2', 'domain_name': 'example.com'}
        result = create_simple_config(tfvars_file('endpoint_name = "test"\n'), shared_config)
        assert result['aws_region'] == 'us-west-2'

    def test_constructs_api_fqdn_from_domain_name(
        self,
        tfvars_file: Callable[[str], Path],
        base_shared_config: Dict[str, str]
    ) -> None:
        result = create_simple_config(tfvars_file('endpoint_name = "test"\n'), base_shared_config)
        assert result['api_fqdn'] == 'api.example.com'

    def test_includes_tfvars_values(
        self,
        tfvars_file: Callable[[str], Path],
        base_shared_config: Dict[str, str]
    ) -> None:
        result = create_simple_config(
            tfvars_file('endpoint_name = "my-endpoint"\n'),
            base_shared_config
        )
        assert result['endpoint_name'] == 'my-endpoint'

    def test_handles_missing_domain_name(self, tfvars_file: Callable[[str], Path]) -> None:
        shared_config = {'aws_region': 'us-east-1'}
        result = create_simple_config(tfvars_file('key = "value"\n'), shared_config)
        assert result['api_fqdn'] == 'api.'


class TestCreateWebsiteConfig:
    def test_includes_aws_region(self, tf_file: Callable[[str], Path]) -> None:
        shared_config = {'aws_region': 'us-east-2', 'domain_name': 'example.com'}
        result = create_website_config(tf_file('  resource_prefix = "test"\n'), shared_config)
        assert result['aws_region'] == 'us-east-2'

    def test_constructs_website_fqdn(
        self,
        tf_file: Callable[[str], Path],
        base_shared_config: Dict[str, str]
    ) -> None:
        result = create_website_config(tf_file(''), base_shared_config)
        assert result['website_fqdn'] == 'www.example.com'

    def test_constructs_website_bucket_name(
        self,
        tf_file: Callable[[str], Path],
        base_shared_config: Dict[str, str]
    ) -> None:
        result = create_website_config(tf_file(''), base_shared_config)
        assert result['website_bucket_name'] == 'www-example-com'

    def test_includes_apex_fqdn(
        self,
        tf_file: Callable[[str], Path],
        base_shared_config: Dict[str, str]
    ) -> None:
        result = create_website_config(tf_file(''), base_shared_config)
        assert result['apex_fqdn'] == 'example.com'

    def test_includes_hosted_zone_id(
        self,
        tf_file: Callable[[str], Path],
        base_shared_config: Dict[str, str]
    ) -> None:
        result = create_website_config(tf_file(''), base_shared_config, 'Z12345')
        assert result['hosted_zone_id'] == 'Z12345'

    def test_constructs_github_repo(self, tf_file: Callable[[str], Path]) -> None:
        shared_config = {
            'aws_region': 'us-east-1',
            'domain_name': 'example.com',
            'github_org': 'myorg',
            'name_for_github_repo': 'myrepo',
        }
        result = create_website_config(tf_file(''), shared_config)
        assert result['github_repo'] == 'myorg/myrepo'

    def test_includes_resource_prefix_from_shared_config(
        self,
        tf_file: Callable[[str], Path]
    ) -> None:
        shared_config = {
            'aws_region': 'us-east-1',
            'domain_name': 'example.com',
            'resource_prefix': 'MyPrefix',
        }
        result = create_website_config(tf_file(''), shared_config)
        assert result['resource_prefix'] == 'MyPrefixWebsite'

    def test_includes_central_logs_bucket(self, tf_file: Callable[[str], Path]) -> None:
        shared_config = {
            'aws_region': 'us-east-1',
            'domain_name': 'example.com',
            'name_for_central_logs_bucket': 'my-logs-bucket',
        }
        result = create_website_config(tf_file(''), shared_config)
        assert result['central_logs_bucket'] == 'my-logs-bucket'


class TestAddDerivedConfig:
    def test_builds_firehose_delivery_stream_name(self) -> None:
        result = {'resource_prefix': 'MyPrefix'}
        add_derived_config(result)
        assert result['firehose_delivery_stream_name'] == 'MyPrefix-CloudWatchLogs'

    def test_builds_firehose_role_name(self) -> None:
        result = {'resource_prefix': 'MyPrefix'}
        add_derived_config(result)
        assert result['firehose_role_name'] == 'MyPrefixFirehoseCloudWatchLogs'

    def test_builds_cloudwatch_logs_firehose_role_name(self) -> None:
        result = {'resource_prefix': 'MyPrefix'}
        add_derived_config(result)
        assert result['cloudwatch_logs_firehose_role_name'] == 'MyPrefixCloudWatchLogsFirehose'

    def test_builds_api_gateway_cloudwatch_role_name(self) -> None:
        result = {'resource_prefix': 'MyPrefix'}
        add_derived_config(result)
        assert result['api_gateway_cloudwatch_role_name'] == 'MyPrefixApiGatewayCloudwatch'

    def test_leaves_resource_prefix_unchanged(self) -> None:
        result = {'resource_prefix': 'MyPrefix'}
        add_derived_config(result)
        assert result['resource_prefix'] == 'MyPrefix'
