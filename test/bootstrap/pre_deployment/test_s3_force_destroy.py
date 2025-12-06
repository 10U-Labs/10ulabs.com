"""Unit tests for S3 bucket force_destroy configuration."""
import hcl2


def test_terraform_state_bucket_has_force_destroy(bootstrap_dir):
    """Test that terraform state bucket has force_destroy enabled."""
    with open(bootstrap_dir / "state.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    bucket_resource = tf_config['resource'][0]['aws_s3_bucket']['terraform_state']
    assert bucket_resource['force_destroy'] is True


def test_central_logs_bucket_has_force_destroy(bootstrap_dir):
    """Test that central logs bucket has force_destroy enabled."""
    with open(bootstrap_dir / "modules" / "central_logs" / "main.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f)
    bucket_resource = tf_config['resource'][0]['aws_s3_bucket']['central_logs']
    assert bucket_resource['force_destroy'] is True
