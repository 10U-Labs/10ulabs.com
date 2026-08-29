import hcl2
from hcl2 import SerializationOptions


V7_COMPATIBLE = SerializationOptions(
    strip_string_quotes=True,
    explicit_blocks=False,
    with_comments=False,
    preserve_heredocs=False,
)


def test_terraform_state_bucket_has_force_destroy(bootstrap_dir):
    with open(bootstrap_dir / "state.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f, serialization_options=V7_COMPATIBLE)
    bucket_resource = tf_config['resource'][0]['aws_s3_bucket']['terraform_state']
    assert bucket_resource['force_destroy'] is True


def test_central_logs_bucket_has_force_destroy(bootstrap_dir):
    with open(bootstrap_dir / "modules" / "central_logs" / "main.tf", encoding='utf-8') as f:
        tf_config = hcl2.load(f, serialization_options=V7_COMPATIBLE)
    bucket_resource = tf_config['resource'][0]['aws_s3_bucket']['central_logs']
    assert bucket_resource['force_destroy'] is True
