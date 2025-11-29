from pathlib import Path
import pytest


@pytest.fixture(name="website_src_path")
def fixture_website_src_path():
    return Path(__file__).parent.parent.parent.parent / "src" / "home_page"


@pytest.fixture(name="cloudfront_s3_tf_content")
def fixture_cloudfront_s3_tf_content(website_src_path):
    with open(website_src_path / "cloudfront_s3.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(name="certificate_dns_tf_content")
def fixture_certificate_dns_tf_content(website_src_path):
    with open(website_src_path / "certificate_dns.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(name="contact_form_tf_content")
def fixture_contact_form_tf_content(website_src_path):
    with open(website_src_path / "contact_form.tf", encoding="utf-8") as f:
        return f.read()


@pytest.fixture(name="contact_lambda_content")
def fixture_contact_lambda_content(website_src_path):
    with open(website_src_path / "lambdas" / "contact.py", encoding="utf-8") as f:
        return f.read()
