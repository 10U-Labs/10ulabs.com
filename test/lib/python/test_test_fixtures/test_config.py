"""Unit tests for test_fixtures.config module."""
import tempfile
from pathlib import Path
from typing import Callable, Dict

import pytest

from test_fixtures.config import (
    parse_tfvars_file,
    parse_locals_file,
    create_simple_config,
    create_website_config,
)


@pytest.fixture
def tfvars_file() -> Callable[[str], Path]:
    """Create a temporary tfvars file with given content."""
    def _create(content: str) -> Path:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.tfvars', delete=False
        ) as f:
            f.write(content)
            f.flush()
            return Path(f.name)
    return _create


@pytest.fixture
def tf_file() -> Callable[[str], Path]:
    """Create a temporary .tf file with given content."""
    def _create(content: str) -> Path:
        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.tf', delete=False
        ) as f:
            f.write(content)
            f.flush()
            return Path(f.name)
    return _create


@pytest.fixture
def base_shared_config() -> Dict[str, str]:
    """Provide base shared config for tests."""
    return {'aws_region': 'us-east-1', 'domain_name': 'example.com'}


class TestParseTfvarsFile:
    """Tests for parse_tfvars_file function."""

    def test_parses_unquoted_value(self, tfvars_file):
        """Test that unquoted values are parsed correctly."""
        result = parse_tfvars_file(tfvars_file('key = value\n'))
        assert result['key'] == 'value'

    def test_parses_quoted_value(self, tfvars_file):
        """Test that quoted values are parsed correctly."""
        result = parse_tfvars_file(tfvars_file('key = "quoted value"\n'))
        assert result['key'] == 'quoted value'

    def test_ignores_comment_lines(self, tfvars_file):
        """Test that comment lines are ignored."""
        result = parse_tfvars_file(tfvars_file('# this is a comment\nkey = value\n'))
        assert len(result) == 1

    def test_ignores_empty_lines(self, tfvars_file):
        """Test that empty lines are ignored."""
        result = parse_tfvars_file(tfvars_file('\n\nkey = value\n\n'))
        assert result['key'] == 'value'

    def test_returns_empty_dict_for_empty_file(self, tfvars_file):
        """Test that empty file returns empty dict."""
        result = parse_tfvars_file(tfvars_file(''))
        assert result == {}

    def test_parses_multiple_key_value_pairs(self, tfvars_file):
        """Test that multiple key-value pairs are parsed."""
        result = parse_tfvars_file(tfvars_file('key1 = "value1"\nkey2 = "value2"\n'))
        assert len(result) == 2

    def test_handles_equals_sign_spacing(self, tfvars_file):
        """Test that various spacing around equals sign works."""
        result = parse_tfvars_file(tfvars_file('key="value"\n'))
        assert result['key'] == 'value'

    def test_ignores_malformed_lines(self, tfvars_file):
        """Test that lines without valid key=value format are ignored."""
        result = parse_tfvars_file(tfvars_file('this line has no equals sign\nkey = "value"\n'))
        assert len(result) == 1


class TestParseLocalsFile:
    """Tests for parse_locals_file function."""

    def test_parses_quoted_string_value(self, tf_file):
        """Test that quoted string values are parsed."""
        result = parse_locals_file(tf_file('  resource_prefix = "my-prefix"\n'))
        assert result['resource_prefix'] == 'my-prefix'

    def test_ignores_locals_block_declaration(self, tf_file):
        """Test that 'locals {' line is ignored."""
        result = parse_locals_file(tf_file('locals {\n  key = "value"\n}\n'))
        assert 'locals' not in result

    def test_ignores_comment_lines(self, tf_file):
        """Test that comment lines are ignored."""
        result = parse_locals_file(tf_file('# comment\n  key = "value"\n'))
        assert len(result) == 1

    def test_resolves_module_shared_reference(self, tf_file):
        """Test that module.shared.* references are resolved."""
        shared_config = {'aws_region': 'us-east-2'}
        result = parse_locals_file(
            tf_file('  region = module.shared.aws_region\n'),
            shared_config
        )
        assert result['region'] == 'us-east-2'

    def test_returns_empty_for_unresolved_reference(self, tf_file):
        """Test that unresolved module.shared.* returns empty string."""
        shared_config = {'other_key': 'value'}
        result = parse_locals_file(
            tf_file('  region = module.shared.missing_key\n'),
            shared_config
        )
        assert result['region'] == ''

    def test_ignores_module_reference_without_shared_config(self, tf_file):
        """Test that module.shared.* is ignored when shared_config is None."""
        result = parse_locals_file(tf_file('  region = module.shared.aws_region\n'), None)
        assert 'region' not in result

    def test_returns_empty_dict_for_empty_file(self, tf_file):
        """Test that empty file returns empty dict."""
        result = parse_locals_file(tf_file(''))
        assert result == {}

    def test_ignores_malformed_lines_with_equals(self, tf_file):
        """Test that lines with equals but no valid pattern are ignored."""
        result = parse_locals_file(tf_file('  } = {\n  key = "value"\n'))
        assert len(result) == 1


class TestCreateSimpleConfig:
    """Tests for create_simple_config function."""

    def test_includes_aws_region_from_shared_config(self, tfvars_file):
        """Test that aws_region is included from shared_config."""
        shared_config = {'aws_region': 'us-west-2', 'domain_name': 'example.com'}
        result = create_simple_config(tfvars_file('endpoint_name = "test"\n'), shared_config)
        assert result['aws_region'] == 'us-west-2'

    def test_constructs_api_fqdn_from_domain_name(self, tfvars_file, base_shared_config):
        """Test that api_fqdn is constructed from domain_name."""
        result = create_simple_config(tfvars_file('endpoint_name = "test"\n'), base_shared_config)
        assert result['api_fqdn'] == 'api.example.com'

    def test_includes_tfvars_values(self, tfvars_file, base_shared_config):
        """Test that tfvars values are included in result."""
        result = create_simple_config(
            tfvars_file('endpoint_name = "my-endpoint"\n'),
            base_shared_config
        )
        assert result['endpoint_name'] == 'my-endpoint'

    def test_handles_missing_domain_name(self, tfvars_file):
        """Test that missing domain_name results in api. prefix only."""
        shared_config = {'aws_region': 'us-east-1'}
        result = create_simple_config(tfvars_file('key = "value"\n'), shared_config)
        assert result['api_fqdn'] == 'api.'


class TestCreateWebsiteConfig:
    """Tests for create_website_config function."""

    def test_includes_aws_region(self, tf_file):
        """Test that aws_region is included from shared_config."""
        shared_config = {'aws_region': 'us-east-2', 'domain_name': 'example.com'}
        result = create_website_config(tf_file('  resource_prefix = "test"\n'), shared_config)
        assert result['aws_region'] == 'us-east-2'

    def test_constructs_website_fqdn(self, tf_file, base_shared_config):
        """Test that website_fqdn is constructed with www prefix."""
        result = create_website_config(tf_file(''), base_shared_config)
        assert result['website_fqdn'] == 'www.example.com'

    def test_constructs_website_bucket_name(self, tf_file, base_shared_config):
        """Test that website_bucket_name replaces dots with hyphens."""
        result = create_website_config(tf_file(''), base_shared_config)
        assert result['website_bucket_name'] == 'www-example-com'

    def test_includes_apex_fqdn(self, tf_file, base_shared_config):
        """Test that apex_fqdn is the domain_name."""
        result = create_website_config(tf_file(''), base_shared_config)
        assert result['apex_fqdn'] == 'example.com'

    def test_includes_hosted_zone_id(self, tf_file, base_shared_config):
        """Test that hosted_zone_id is passed through."""
        result = create_website_config(tf_file(''), base_shared_config, 'Z12345')
        assert result['hosted_zone_id'] == 'Z12345'

    def test_constructs_github_repo(self, tf_file):
        """Test that github_repo is constructed from org and repo name."""
        shared_config = {
            'aws_region': 'us-east-1',
            'domain_name': 'example.com',
            'github_org': 'myorg',
            'name_for_github_repo': 'myrepo',
        }
        result = create_website_config(tf_file(''), shared_config)
        assert result['github_repo'] == 'myorg/myrepo'

    def test_includes_resource_prefix_from_locals(self, tf_file, base_shared_config):
        """Test that resource_prefix is extracted from locals file."""
        result = create_website_config(
            tf_file('  resource_prefix = "my-prefix"\n'),
            base_shared_config
        )
        assert result['resource_prefix'] == 'my-prefix'

    def test_includes_central_logs_bucket(self, tf_file):
        """Test that central_logs_bucket is included from shared_config."""
        shared_config = {
            'aws_region': 'us-east-1',
            'domain_name': 'example.com',
            'name_for_central_logs_bucket': 'my-logs-bucket',
        }
        result = create_website_config(tf_file(''), shared_config)
        assert result['central_logs_bucket'] == 'my-logs-bucket'
