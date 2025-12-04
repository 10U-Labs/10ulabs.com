"""Tests for s3_versioning_checker hook."""


def test_is_iac_file_returns_true_for_tf(s3_versioning_checker):
    """Test that Is iac file returns true for tf."""
    tf_file_is_iac = s3_versioning_checker.is_iac_file('main.tf')
    assert tf_file_is_iac


def test_is_iac_file_returns_true_for_json(s3_versioning_checker):
    """Test that Is iac file returns true for json."""
    json_file_is_iac = s3_versioning_checker.is_iac_file('template.json')
    assert json_file_is_iac


def test_is_iac_file_returns_true_for_yaml(s3_versioning_checker):
    """Test that Is iac file returns true for yaml."""
    yaml_file_is_iac = s3_versioning_checker.is_iac_file('template.yaml')
    assert yaml_file_is_iac


def test_is_iac_file_returns_true_for_yml(s3_versioning_checker):
    """Test that Is iac file returns true for yml."""
    yml_file_is_iac = s3_versioning_checker.is_iac_file('template.yml')
    assert yml_file_is_iac


def test_is_iac_file_returns_true_for_ts(s3_versioning_checker):
    """Test that Is iac file returns true for ts."""
    ts_file_is_iac = s3_versioning_checker.is_iac_file('stack.ts')
    assert ts_file_is_iac


def test_is_iac_file_returns_true_for_py(s3_versioning_checker):
    """Test that Is iac file returns true for py."""
    py_file_is_iac = s3_versioning_checker.is_iac_file('stack.py')
    assert py_file_is_iac


def test_is_iac_file_returns_false_for_md(s3_versioning_checker):
    """Test that Is iac file returns false for md."""
    md_file_is_not_iac = not s3_versioning_checker.is_iac_file('README.md')
    assert md_file_is_not_iac


def test_is_iac_file_returns_false_for_txt(s3_versioning_checker):
    """Test that Is iac file returns false for txt."""
    txt_file_is_not_iac = not s3_versioning_checker.is_iac_file('notes.txt')
    assert txt_file_is_not_iac


def test_check_terraform_detects_versioning_enabled(s3_versioning_checker):
    """Test that Check terraform detects versioning enabled."""
    content = '''
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"
  versioning {
    enabled = true
  }
}
'''
    violations = s3_versioning_checker.check_terraform(content)
    terraform_versioning_enabled_is_detected = len(violations) > 0
    assert terraform_versioning_enabled_is_detected


def test_check_terraform_allows_versioning_disabled(s3_versioning_checker):
    """Test that Check terraform allows versioning disabled."""
    content = '''
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"
  versioning {
    enabled = false
  }
}
'''
    violations = s3_versioning_checker.check_terraform(content)
    terraform_versioning_disabled_is_allowed = len(violations) == 0
    assert terraform_versioning_disabled_is_allowed


def test_check_terraform_allows_no_versioning_block(s3_versioning_checker):
    """Test that Check terraform allows no versioning block."""
    content = '''
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"
}
'''
    violations = s3_versioning_checker.check_terraform(content)
    terraform_no_versioning_is_allowed = len(violations) == 0
    assert terraform_no_versioning_is_allowed


def test_check_cloudformation_detects_versioning_enabled(s3_versioning_checker):
    """Test that Check cloudformation detects versioning enabled."""
    content = '''
Resources:
  S3Bucket:
    Type: AWS::S3::Bucket
    Properties:
      VersioningConfiguration:
        Status: Enabled
'''
    violations = s3_versioning_checker.check_cloudformation(content)
    cloudformation_versioning_enabled_is_detected = len(violations) > 0
    assert cloudformation_versioning_enabled_is_detected


def test_check_cloudformation_allows_versioning_suspended(s3_versioning_checker):
    """Test that Check cloudformation allows versioning suspended."""
    content = '''
Resources:
  S3Bucket:
    Type: AWS::S3::Bucket
    Properties:
      VersioningConfiguration:
        Status: Suspended
'''
    violations = s3_versioning_checker.check_cloudformation(content)
    cloudformation_versioning_suspended_is_allowed = len(violations) == 0
    assert cloudformation_versioning_suspended_is_allowed


def test_check_cdk_typescript_detects_versioned_true(s3_versioning_checker):
    """Test that Check cdk typescript detects versioned true."""
    content = '''
new s3.Bucket(this, 'MyBucket', {
  versioned: true,
});
'''
    violations = s3_versioning_checker.check_cdk_typescript(content)
    cdk_typescript_versioned_true_is_detected = len(violations) > 0
    assert cdk_typescript_versioned_true_is_detected


def test_check_cdk_typescript_allows_versioned_false(s3_versioning_checker):
    """Test that Check cdk typescript allows versioned false."""
    content = '''
new s3.Bucket(this, 'MyBucket', {
  versioned: false,
});
'''
    violations = s3_versioning_checker.check_cdk_typescript(content)
    cdk_typescript_versioned_false_is_allowed = len(violations) == 0
    assert cdk_typescript_versioned_false_is_allowed


def test_check_cdk_python_detects_versioned_true(s3_versioning_checker):
    """Test that Check cdk python detects versioned true."""
    content = '''
s3.Bucket(self, "MyBucket",
    versioned=True
)
'''
    violations = s3_versioning_checker.check_cdk_python(content)
    cdk_python_versioned_true_is_detected = len(violations) > 0
    assert cdk_python_versioned_true_is_detected


def test_check_cdk_python_allows_versioned_false(s3_versioning_checker):
    """Test that Check cdk python allows versioned false."""
    content = '''
s3.Bucket(self, "MyBucket",
    versioned=False
)
'''
    violations = s3_versioning_checker.check_cdk_python(content)
    cdk_python_versioned_false_is_allowed = len(violations) == 0
    assert cdk_python_versioned_false_is_allowed


def test_check_content_skips_non_iac_files(s3_versioning_checker):
    """Test that Check content skips non iac files."""
    content = 'versioned: true'
    violations = s3_versioning_checker.check_content(content, 'README.md')
    non_iac_file_is_skipped = len(violations) == 0
    assert non_iac_file_is_skipped


def test_check_content_skips_files_without_s3_or_bucket(s3_versioning_checker):
    """Test that Check content skips files without s3 or bucket."""
    content = 'versioned: true'
    violations = s3_versioning_checker.check_content(content, 'lambda.py')
    file_without_s3_is_skipped = len(violations) == 0
    assert file_without_s3_is_skipped


def test_check_content_processes_tf_file_with_bucket(s3_versioning_checker):
    """Test that Check content processes tf file with bucket."""
    content = '''
resource "aws_s3_bucket" "example" {
  bucket = "my-bucket"
  versioning {
    enabled = true
  }
}
'''
    violations = s3_versioning_checker.check_content(content, 'main.tf')
    tf_file_with_bucket_is_processed = len(violations) > 0
    assert tf_file_with_bucket_is_processed
