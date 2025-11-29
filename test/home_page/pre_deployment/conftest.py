import pytest
from pathlib import Path


@pytest.fixture
def website_src_path():
    return Path(__file__).parent.parent.parent.parent / "src" / "website"


@pytest.fixture
def cloudfront_s3_tf_content(website_src_path):
    with open(website_src_path / "cloudfront_s3.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def certificate_dns_tf_content(website_src_path):
    with open(website_src_path / "certificate_dns.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def contact_form_tf_content(website_src_path):
    with open(website_src_path / "contact_form.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture
def contact_lambda_content(website_src_path):
    with open(website_src_path / "lambdas" / "contact.py", encoding="utf-8") as f:
        return f.read()
