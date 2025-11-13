from pathlib import Path
import json
import importlib.util
import aws_cdk as cdk
from aws_cdk.assertions import Template


def test_config_file_exists():
    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    assert config_path.exists()


def test_config_has_domain_name():
    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)
    assert "domain_name" in config


def test_config_has_google_site_verification():
    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)
    assert "google_site_verification" in config


def test_config_has_aws_account_id():
    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)
    assert "aws_account_id" in config


def test_config_has_aws_region():
    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)
    assert "aws_region" in config


def test_stack_creates_txt_record():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "gmail_email_provider" / "stack.py"
    spec = importlib.util.spec_from_file_location("gmail_stack", stack_path)
    gmail_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gmail_module)
    GmailEmailProviderStack = gmail_module.GmailEmailProviderStack

    domain_config_path = Path(__file__).parents[2] / "config" / "cloudtrail_and_domain_name.json"
    with open(domain_config_path) as f:
        domain_config = json.load(f)

    domain_stack_path = Path(__file__).parents[2] / "src" / "cloudtrail_and_domain_name" / "stack.py"
    domain_spec = importlib.util.spec_from_file_location("domain_stack", domain_stack_path)
    domain_module = importlib.util.module_from_spec(domain_spec)
    domain_spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    domain_stack = DomainStack(
        app,
        "TestDomainStack",
        config=domain_config,
        env=cdk.Environment(
            account=str(domain_config["aws"]["account_id"]),
            region=domain_config["aws"]["region"]
        )
    )

    stack = GmailEmailProviderStack(
        app,
        "TestGmailStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)
    template.has_resource_properties(
        "AWS::Route53::RecordSet",
        {
            "Type": "TXT"
        }
    )


def test_stack_has_google_verification_output():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "gmail_email_provider" / "stack.py"
    spec = importlib.util.spec_from_file_location("gmail_stack", stack_path)
    gmail_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gmail_module)
    GmailEmailProviderStack = gmail_module.GmailEmailProviderStack

    domain_config_path = Path(__file__).parents[2] / "config" / "cloudtrail_and_domain_name.json"
    with open(domain_config_path) as f:
        domain_config = json.load(f)

    domain_stack_path = Path(__file__).parents[2] / "src" / "cloudtrail_and_domain_name" / "stack.py"
    domain_spec = importlib.util.spec_from_file_location("domain_stack", domain_stack_path)
    domain_module = importlib.util.module_from_spec(domain_spec)
    domain_spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    domain_stack = DomainStack(
        app,
        "TestDomainStack",
        config=domain_config,
        env=cdk.Environment(
            account=str(domain_config["aws"]["account_id"]),
            region=domain_config["aws"]["region"]
        )
    )

    stack = GmailEmailProviderStack(
        app,
        "TestGmailStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)
    outputs = template.find_outputs("*")
    assert "GoogleVerificationRecord" in outputs


def test_stack_has_google_verification_value_output():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "gmail_email_provider" / "stack.py"
    spec = importlib.util.spec_from_file_location("gmail_stack", stack_path)
    gmail_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gmail_module)
    GmailEmailProviderStack = gmail_module.GmailEmailProviderStack

    domain_config_path = Path(__file__).parents[2] / "config" / "cloudtrail_and_domain_name.json"
    with open(domain_config_path) as f:
        domain_config = json.load(f)

    domain_stack_path = Path(__file__).parents[2] / "src" / "cloudtrail_and_domain_name" / "stack.py"
    domain_spec = importlib.util.spec_from_file_location("domain_stack", domain_stack_path)
    domain_module = importlib.util.module_from_spec(domain_spec)
    domain_spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    domain_stack = DomainStack(
        app,
        "TestDomainStack",
        config=domain_config,
        env=cdk.Environment(
            account=str(domain_config["aws"]["account_id"]),
            region=domain_config["aws"]["region"]
        )
    )

    stack = GmailEmailProviderStack(
        app,
        "TestGmailStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)
    outputs = template.find_outputs("*")
    assert "GoogleVerificationValue" in outputs


def test_stack_creates_mx_record():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "gmail_email_provider" / "stack.py"
    spec = importlib.util.spec_from_file_location("gmail_stack", stack_path)
    gmail_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gmail_module)
    GmailEmailProviderStack = gmail_module.GmailEmailProviderStack

    domain_config_path = Path(__file__).parents[2] / "config" / "cloudtrail_and_domain_name.json"
    with open(domain_config_path) as f:
        domain_config = json.load(f)

    domain_stack_path = Path(__file__).parents[2] / "src" / "cloudtrail_and_domain_name" / "stack.py"
    domain_spec = importlib.util.spec_from_file_location("domain_stack", domain_stack_path)
    domain_module = importlib.util.module_from_spec(domain_spec)
    domain_spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    domain_stack = DomainStack(
        app,
        "TestDomainStack",
        config=domain_config,
        env=cdk.Environment(
            account=str(domain_config["aws"]["account_id"]),
            region=domain_config["aws"]["region"]
        )
    )

    stack = GmailEmailProviderStack(
        app,
        "TestGmailStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)
    template.has_resource_properties(
        "AWS::Route53::RecordSet",
        {
            "Type": "MX"
        }
    )


def test_stack_has_gmail_mx_output():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "gmail_email_provider" / "stack.py"
    spec = importlib.util.spec_from_file_location("gmail_stack", stack_path)
    gmail_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gmail_module)
    GmailEmailProviderStack = gmail_module.GmailEmailProviderStack

    domain_config_path = Path(__file__).parents[2] / "config" / "cloudtrail_and_domain_name.json"
    with open(domain_config_path) as f:
        domain_config = json.load(f)

    domain_stack_path = Path(__file__).parents[2] / "src" / "cloudtrail_and_domain_name" / "stack.py"
    domain_spec = importlib.util.spec_from_file_location("domain_stack", domain_stack_path)
    domain_module = importlib.util.module_from_spec(domain_spec)
    domain_spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    domain_stack = DomainStack(
        app,
        "TestDomainStack",
        config=domain_config,
        env=cdk.Environment(
            account=str(domain_config["aws"]["account_id"]),
            region=domain_config["aws"]["region"]
        )
    )

    stack = GmailEmailProviderStack(
        app,
        "TestGmailStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)
    outputs = template.find_outputs("*")
    assert "GmailMxRecordOutput" in outputs


def test_stack_txt_record_has_correct_value_format():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "gmail_email_provider" / "stack.py"
    spec = importlib.util.spec_from_file_location("gmail_stack", stack_path)
    gmail_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gmail_module)
    GmailEmailProviderStack = gmail_module.GmailEmailProviderStack

    domain_config_path = Path(__file__).parents[2] / "config" / "cloudtrail_and_domain_name.json"
    with open(domain_config_path) as f:
        domain_config = json.load(f)

    domain_stack_path = Path(__file__).parents[2] / "src" / "cloudtrail_and_domain_name" / "stack.py"
    domain_spec = importlib.util.spec_from_file_location("domain_stack", domain_stack_path)
    domain_module = importlib.util.module_from_spec(domain_spec)
    domain_spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    domain_stack = DomainStack(
        app,
        "TestDomainStack",
        config=domain_config,
        env=cdk.Environment(
            account=str(domain_config["aws"]["account_id"]),
            region=domain_config["aws"]["region"]
        )
    )

    stack = GmailEmailProviderStack(
        app,
        "TestGmailStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)
    expected_value = f'"google-site-verification={config["google_site_verification"]}"'
    template.has_resource_properties(
        "AWS::Route53::RecordSet",
        {
            "Type": "TXT",
            "ResourceRecords": [expected_value]
        }
    )


def test_stack_txt_record_has_correct_ttl():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "gmail_email_provider" / "stack.py"
    spec = importlib.util.spec_from_file_location("gmail_stack", stack_path)
    gmail_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gmail_module)
    GmailEmailProviderStack = gmail_module.GmailEmailProviderStack

    domain_config_path = Path(__file__).parents[2] / "config" / "cloudtrail_and_domain_name.json"
    with open(domain_config_path) as f:
        domain_config = json.load(f)

    domain_stack_path = Path(__file__).parents[2] / "src" / "cloudtrail_and_domain_name" / "stack.py"
    domain_spec = importlib.util.spec_from_file_location("domain_stack", domain_stack_path)
    domain_module = importlib.util.module_from_spec(domain_spec)
    domain_spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    domain_stack = DomainStack(
        app,
        "TestDomainStack",
        config=domain_config,
        env=cdk.Environment(
            account=str(domain_config["aws"]["account_id"]),
            region=domain_config["aws"]["region"]
        )
    )

    stack = GmailEmailProviderStack(
        app,
        "TestGmailStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)
    template.has_resource_properties(
        "AWS::Route53::RecordSet",
        {
            "Type": "TXT",
            "TTL": "300"
        }
    )


def test_stack_mx_record_has_priority_one():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "gmail_email_provider" / "stack.py"
    spec = importlib.util.spec_from_file_location("gmail_stack", stack_path)
    gmail_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gmail_module)
    GmailEmailProviderStack = gmail_module.GmailEmailProviderStack

    domain_config_path = Path(__file__).parents[2] / "config" / "cloudtrail_and_domain_name.json"
    with open(domain_config_path) as f:
        domain_config = json.load(f)

    domain_stack_path = Path(__file__).parents[2] / "src" / "cloudtrail_and_domain_name" / "stack.py"
    domain_spec = importlib.util.spec_from_file_location("domain_stack", domain_stack_path)
    domain_module = importlib.util.module_from_spec(domain_spec)
    domain_spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    domain_stack = DomainStack(
        app,
        "TestDomainStack",
        config=domain_config,
        env=cdk.Environment(
            account=str(domain_config["aws"]["account_id"]),
            region=domain_config["aws"]["region"]
        )
    )

    stack = GmailEmailProviderStack(
        app,
        "TestGmailStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)
    template.has_resource_properties(
        "AWS::Route53::RecordSet",
        {
            "Type": "MX",
            "ResourceRecords": ["1 smtp.google.com."]
        }
    )


def test_stack_mx_record_has_correct_ttl():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "gmail_email_provider" / "stack.py"
    spec = importlib.util.spec_from_file_location("gmail_stack", stack_path)
    gmail_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gmail_module)
    GmailEmailProviderStack = gmail_module.GmailEmailProviderStack

    domain_config_path = Path(__file__).parents[2] / "config" / "cloudtrail_and_domain_name.json"
    with open(domain_config_path) as f:
        domain_config = json.load(f)

    domain_stack_path = Path(__file__).parents[2] / "src" / "cloudtrail_and_domain_name" / "stack.py"
    domain_spec = importlib.util.spec_from_file_location("domain_stack", domain_stack_path)
    domain_module = importlib.util.module_from_spec(domain_spec)
    domain_spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    domain_stack = DomainStack(
        app,
        "TestDomainStack",
        config=domain_config,
        env=cdk.Environment(
            account=str(domain_config["aws"]["account_id"]),
            region=domain_config["aws"]["region"]
        )
    )

    stack = GmailEmailProviderStack(
        app,
        "TestGmailStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)
    template.has_resource_properties(
        "AWS::Route53::RecordSet",
        {
            "Type": "MX",
            "TTL": "300"
        }
    )


def test_stack_creates_exactly_one_txt_record():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "gmail_email_provider" / "stack.py"
    spec = importlib.util.spec_from_file_location("gmail_stack", stack_path)
    gmail_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gmail_module)
    GmailEmailProviderStack = gmail_module.GmailEmailProviderStack

    domain_config_path = Path(__file__).parents[2] / "config" / "cloudtrail_and_domain_name.json"
    with open(domain_config_path) as f:
        domain_config = json.load(f)

    domain_stack_path = Path(__file__).parents[2] / "src" / "cloudtrail_and_domain_name" / "stack.py"
    domain_spec = importlib.util.spec_from_file_location("domain_stack", domain_stack_path)
    domain_module = importlib.util.module_from_spec(domain_spec)
    domain_spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    domain_stack = DomainStack(
        app,
        "TestDomainStack",
        config=domain_config,
        env=cdk.Environment(
            account=str(domain_config["aws"]["account_id"]),
            region=domain_config["aws"]["region"]
        )
    )

    stack = GmailEmailProviderStack(
        app,
        "TestGmailStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)
    template.resource_count_is("AWS::Route53::RecordSet", 2)


def test_stack_creates_exactly_one_mx_record():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)

    stack_path = Path(__file__).parents[2] / "src" / "gmail_email_provider" / "stack.py"
    spec = importlib.util.spec_from_file_location("gmail_stack", stack_path)
    gmail_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gmail_module)
    GmailEmailProviderStack = gmail_module.GmailEmailProviderStack

    domain_config_path = Path(__file__).parents[2] / "config" / "cloudtrail_and_domain_name.json"
    with open(domain_config_path) as f:
        domain_config = json.load(f)

    domain_stack_path = Path(__file__).parents[2] / "src" / "cloudtrail_and_domain_name" / "stack.py"
    domain_spec = importlib.util.spec_from_file_location("domain_stack", domain_stack_path)
    domain_module = importlib.util.module_from_spec(domain_spec)
    domain_spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    domain_stack = DomainStack(
        app,
        "TestDomainStack",
        config=domain_config,
        env=cdk.Environment(
            account=str(domain_config["aws"]["account_id"]),
            region=domain_config["aws"]["region"]
        )
    )

    stack = GmailEmailProviderStack(
        app,
        "TestGmailStack",
        config=config,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)
    template.resource_count_is("AWS::Route53::RecordSet", 2)


def test_config_ttl_defaults_to_300():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)

    config_without_ttl = {k: v for k, v in config.items() if k != "ttl"}

    stack_path = Path(__file__).parents[2] / "src" / "gmail_email_provider" / "stack.py"
    spec = importlib.util.spec_from_file_location("gmail_stack", stack_path)
    gmail_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gmail_module)
    GmailEmailProviderStack = gmail_module.GmailEmailProviderStack

    domain_config_path = Path(__file__).parents[2] / "config" / "cloudtrail_and_domain_name.json"
    with open(domain_config_path) as f:
        domain_config = json.load(f)

    domain_stack_path = Path(__file__).parents[2] / "src" / "cloudtrail_and_domain_name" / "stack.py"
    domain_spec = importlib.util.spec_from_file_location("domain_stack", domain_stack_path)
    domain_module = importlib.util.module_from_spec(domain_spec)
    domain_spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    domain_stack = DomainStack(
        app,
        "TestDomainStack",
        config=domain_config,
        env=cdk.Environment(
            account=str(domain_config["aws"]["account_id"]),
            region=domain_config["aws"]["region"]
        )
    )

    stack = GmailEmailProviderStack(
        app,
        "TestGmailStack",
        config=config_without_ttl,
        env=cdk.Environment(
            account=str(config["aws"]["account_id"]),
            region=config["aws"]["region"]
        )
    )

    template = Template.from_stack(stack)
    template.has_resource_properties(
        "AWS::Route53::RecordSet",
        {
            "Type": "TXT",
            "TTL": "300"
        }
    )


def test_stack_raises_error_when_google_verification_missing():
    app = cdk.App()

    config_path = Path(__file__).parents[2] / "config" / "gmail_email_provider.json"
    with open(config_path) as f:
        config = json.load(f)

    config_without_verification = {k: v for k, v in config.items() if k != "google_site_verification"}

    stack_path = Path(__file__).parents[2] / "src" / "gmail_email_provider" / "stack.py"
    spec = importlib.util.spec_from_file_location("gmail_stack", stack_path)
    gmail_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gmail_module)
    GmailEmailProviderStack = gmail_module.GmailEmailProviderStack

    domain_config_path = Path(__file__).parents[2] / "config" / "cloudtrail_and_domain_name.json"
    with open(domain_config_path) as f:
        domain_config = json.load(f)

    domain_stack_path = Path(__file__).parents[2] / "src" / "cloudtrail_and_domain_name" / "stack.py"
    domain_spec = importlib.util.spec_from_file_location("domain_stack", domain_stack_path)
    domain_module = importlib.util.module_from_spec(domain_spec)
    domain_spec.loader.exec_module(domain_module)
    DomainStack = domain_module.DomainStack

    domain_stack = DomainStack(
        app,
        "TestDomainStack",
        config=domain_config,
        env=cdk.Environment(
            account=str(domain_config["aws"]["account_id"]),
            region=domain_config["aws"]["region"]
        )
    )

    try:
        stack = GmailEmailProviderStack(
            app,
            "TestGmailStack",
            config=config_without_verification,
            env=cdk.Environment(
                account=str(config["aws"]["account_id"]),
                region=config["aws"]["region"]
            )
        )
        assert False
    except ValueError:
        assert True
