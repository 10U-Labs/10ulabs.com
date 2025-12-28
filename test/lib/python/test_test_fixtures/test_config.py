"""Unit tests for test_fixtures.config module."""
import tempfile
from pathlib import Path

from test_fixtures.config import (
    parse_tfvars_file,
    parse_locals_file,
    create_simple_config,
    create_website_config,
)


class TestParseTfvarsFile:
    """Tests for parse_tfvars_file function."""

    def test_parses_unquoted_value(self):
        """Test that unquoted values are parsed correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False) as f:
            f.write('key = value\n')
            f.flush()
            result = parse_tfvars_file(Path(f.name))
        assert result['key'] == 'value'

    def test_parses_quoted_value(self):
        """Test that quoted values are parsed correctly."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False) as f:
            f.write('key = "quoted value"\n')
            f.flush()
            result = parse_tfvars_file(Path(f.name))
        assert result['key'] == 'quoted value'

    def test_ignores_comment_lines(self):
        """Test that comment lines are ignored."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False) as f:
            f.write('# this is a comment\nkey = value\n')
            f.flush()
            result = parse_tfvars_file(Path(f.name))
        assert len(result) == 1

    def test_ignores_empty_lines(self):
        """Test that empty lines are ignored."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False) as f:
            f.write('\n\nkey = value\n\n')
            f.flush()
            result = parse_tfvars_file(Path(f.name))
        assert result['key'] == 'value'

    def test_returns_empty_dict_for_empty_file(self):
        """Test that empty file returns empty dict."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False) as f:
            f.write('')
            f.flush()
            result = parse_tfvars_file(Path(f.name))
        assert result == {}

    def test_parses_multiple_key_value_pairs(self):
        """Test that multiple key-value pairs are parsed."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False) as f:
            f.write('key1 = "value1"\nkey2 = "value2"\n')
            f.flush()
            result = parse_tfvars_file(Path(f.name))
        assert len(result) == 2

    def test_handles_equals_sign_spacing(self):
        """Test that various spacing around equals sign works."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False) as f:
            f.write('key="value"\n')
            f.flush()
            result = parse_tfvars_file(Path(f.name))
        assert result['key'] == 'value'

    def test_ignores_malformed_lines(self):
        """Test that lines without valid key=value format are ignored."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False) as f:
            f.write('this line has no equals sign\nkey = "value"\n')
            f.flush()
            result = parse_tfvars_file(Path(f.name))
        assert len(result) == 1


class TestParseLocalsFile:
    """Tests for parse_locals_file function."""

    def test_parses_quoted_string_value(self):
        """Test that quoted string values are parsed."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('  resource_prefix = "my-prefix"\n')
            f.flush()
            result = parse_locals_file(Path(f.name))
        assert result['resource_prefix'] == 'my-prefix'

    def test_ignores_locals_block_declaration(self):
        """Test that 'locals {' line is ignored."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('locals {\n  key = "value"\n}\n')
            f.flush()
            result = parse_locals_file(Path(f.name))
        assert 'locals' not in result

    def test_ignores_comment_lines(self):
        """Test that comment lines are ignored."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('# comment\n  key = "value"\n')
            f.flush()
            result = parse_locals_file(Path(f.name))
        assert len(result) == 1

    def test_resolves_module_shared_reference(self):
        """Test that module.shared.* references are resolved."""
        shared_config = {'aws_region': 'us-east-2'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('  region = module.shared.aws_region\n')
            f.flush()
            result = parse_locals_file(Path(f.name), shared_config)
        assert result['region'] == 'us-east-2'

    def test_returns_empty_for_unresolved_reference(self):
        """Test that unresolved module.shared.* returns empty string."""
        shared_config = {'other_key': 'value'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('  region = module.shared.missing_key\n')
            f.flush()
            result = parse_locals_file(Path(f.name), shared_config)
        assert result['region'] == ''

    def test_ignores_module_reference_without_shared_config(self):
        """Test that module.shared.* is ignored when shared_config is None."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('  region = module.shared.aws_region\n')
            f.flush()
            result = parse_locals_file(Path(f.name), None)
        assert 'region' not in result

    def test_returns_empty_dict_for_empty_file(self):
        """Test that empty file returns empty dict."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('')
            f.flush()
            result = parse_locals_file(Path(f.name))
        assert result == {}

    def test_ignores_malformed_lines_with_equals(self):
        """Test that lines with equals but no valid pattern are ignored."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('  } = {\n  key = "value"\n')
            f.flush()
            result = parse_locals_file(Path(f.name))
        assert len(result) == 1


class TestCreateSimpleConfig:
    """Tests for create_simple_config function."""

    def test_includes_aws_region_from_shared_config(self):
        """Test that aws_region is included from shared_config."""
        shared_config = {'aws_region': 'us-west-2', 'domain_name': 'example.com'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False) as f:
            f.write('endpoint_name = "test"\n')
            f.flush()
            result = create_simple_config(Path(f.name), shared_config)
        assert result['aws_region'] == 'us-west-2'

    def test_constructs_api_fqdn_from_domain_name(self):
        """Test that api_fqdn is constructed from domain_name."""
        shared_config = {'aws_region': 'us-east-1', 'domain_name': 'example.com'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False) as f:
            f.write('endpoint_name = "test"\n')
            f.flush()
            result = create_simple_config(Path(f.name), shared_config)
        assert result['api_fqdn'] == 'api.example.com'

    def test_includes_tfvars_values(self):
        """Test that tfvars values are included in result."""
        shared_config = {'aws_region': 'us-east-1', 'domain_name': 'example.com'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False) as f:
            f.write('endpoint_name = "my-endpoint"\n')
            f.flush()
            result = create_simple_config(Path(f.name), shared_config)
        assert result['endpoint_name'] == 'my-endpoint'

    def test_handles_missing_domain_name(self):
        """Test that missing domain_name results in api. prefix only."""
        shared_config = {'aws_region': 'us-east-1'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tfvars', delete=False) as f:
            f.write('key = "value"\n')
            f.flush()
            result = create_simple_config(Path(f.name), shared_config)
        assert result['api_fqdn'] == 'api.'


class TestCreateWebsiteConfig:
    """Tests for create_website_config function."""

    def test_includes_aws_region(self):
        """Test that aws_region is included from shared_config."""
        shared_config = {'aws_region': 'us-east-2', 'domain_name': 'example.com'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('  resource_prefix = "test"\n')
            f.flush()
            result = create_website_config(Path(f.name), shared_config)
        assert result['aws_region'] == 'us-east-2'

    def test_constructs_website_fqdn(self):
        """Test that website_fqdn is constructed with www prefix."""
        shared_config = {'aws_region': 'us-east-1', 'domain_name': 'example.com'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('')
            f.flush()
            result = create_website_config(Path(f.name), shared_config)
        assert result['website_fqdn'] == 'www.example.com'

    def test_constructs_website_bucket_name(self):
        """Test that website_bucket_name replaces dots with hyphens."""
        shared_config = {'aws_region': 'us-east-1', 'domain_name': 'example.com'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('')
            f.flush()
            result = create_website_config(Path(f.name), shared_config)
        assert result['website_bucket_name'] == 'www-example-com'

    def test_includes_apex_fqdn(self):
        """Test that apex_fqdn is the domain_name."""
        shared_config = {'aws_region': 'us-east-1', 'domain_name': 'example.com'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('')
            f.flush()
            result = create_website_config(Path(f.name), shared_config)
        assert result['apex_fqdn'] == 'example.com'

    def test_includes_hosted_zone_id(self):
        """Test that hosted_zone_id is passed through."""
        shared_config = {'aws_region': 'us-east-1', 'domain_name': 'example.com'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('')
            f.flush()
            result = create_website_config(Path(f.name), shared_config, 'Z12345')
        assert result['hosted_zone_id'] == 'Z12345'

    def test_constructs_github_repo(self):
        """Test that github_repo is constructed from org and repo name."""
        shared_config = {
            'aws_region': 'us-east-1',
            'domain_name': 'example.com',
            'github_org': 'myorg',
            'name_for_github_repo': 'myrepo',
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('')
            f.flush()
            result = create_website_config(Path(f.name), shared_config)
        assert result['github_repo'] == 'myorg/myrepo'

    def test_includes_resource_prefix_from_locals(self):
        """Test that resource_prefix is extracted from locals file."""
        shared_config = {'aws_region': 'us-east-1', 'domain_name': 'example.com'}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('  resource_prefix = "my-prefix"\n')
            f.flush()
            result = create_website_config(Path(f.name), shared_config)
        assert result['resource_prefix'] == 'my-prefix'

    def test_includes_central_logs_bucket(self):
        """Test that central_logs_bucket is included from shared_config."""
        shared_config = {
            'aws_region': 'us-east-1',
            'domain_name': 'example.com',
            'name_for_central_logs_bucket': 'my-logs-bucket',
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tf', delete=False) as f:
            f.write('')
            f.flush()
            result = create_website_config(Path(f.name), shared_config)
        assert result['central_logs_bucket'] == 'my-logs-bucket'
