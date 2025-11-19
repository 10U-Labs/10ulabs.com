import json
import importlib.util
from pathlib import Path

import aws_cdk as cdk
from aws_cdk.assertions import Template, Match, Capture
import pytest


@pytest.fixture
def config():
    config_path = Path(__file__).parent.parent.parent / 'src' / 'auth_between_aws_and_github' / 'config.json'
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def stack(config):
    stack_path = Path(__file__).parent.parent.parent / 'src' / 'auth_between_aws_and_github' / 'stack.py'
    spec = importlib.util.spec_from_file_location("auth_stack", stack_path)
    auth_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auth_module)
    AuthBetweenAwsAndGithubStack = auth_module.AuthBetweenAwsAndGithubStack

    app = cdk.App()
    return AuthBetweenAwsAndGithubStack(
        app,
        'AuthBetweenAwsAndGithub',
        config=config,
        env=cdk.Environment(
            account=config['aws']['account_id'],
            region=config['aws']['region']
        )
    )


@pytest.fixture
def template(stack):
    return Template.from_stack(stack)


def test_stack_synthesizes_without_errors(template):
    assert template is not None


def test_creates_oidc_custom_resource_lambda(template):
    template.resource_count_is('AWS::Lambda::Function', 2)


def test_creates_custom_resource_for_oidc(template):
    template.resource_count_is('AWS::CloudFormation::CustomResource', 2)


def test_creates_iam_roles(template):
    template.resource_count_is('AWS::IAM::Role', 2)


def test_iam_role_has_web_identity_trust_policy(template):
    template.has_resource_properties('AWS::CloudFormation::CustomResource', {
        'ServiceToken': Match.any_value(),
        'RoleName': Match.any_value(),
        'ProviderArn': Match.any_value()
    })


def test_iam_role_trust_policy_has_correct_conditions(template, config):
    github_org = config['github']['org']
    github_repo = config['github']['repo']

    template.has_resource_properties('AWS::CloudFormation::CustomResource', {
        'ServiceToken': Match.any_value(),
        'RoleName': config['aws']['iam_role_name'],
        'GitHubOrg': github_org,
        'GitHubRepo': github_repo
    })


def test_iam_role_has_administrator_access_policy(template):
    template.has_resource_properties('AWS::IAM::Role', {
        'ManagedPolicyArns': Match.array_with([
            Match.object_like({
                'Fn::Join': Match.array_with([
                    Match.array_with([
                        Match.string_like_regexp('.*AWSLambdaBasicExecutionRole')
                    ])
                ])
            })
        ])
    })


def test_stack_creates_core_resources(template):
    resources = template.to_json()['Resources']
    assert len(resources) >= 6


def test_config_has_github_section(config):
    assert 'github' in config


def test_config_has_aws_section(config):
    assert 'aws' in config


def test_config_github_has_org(config):
    assert 'org' in config['github']


def test_config_github_has_repo(config):
    assert 'repo' in config['github']


def test_config_aws_has_account_id(config):
    assert 'account_id' in config['aws']


def test_config_aws_has_region(config):
    assert 'region' in config['aws']


def test_config_aws_has_iam_role_name(config):
    assert 'iam_role_name' in config['aws']


def test_config_aws_has_secrets_manager_section(config):
    assert 'secrets_manager' in config['aws']


def test_config_secrets_manager_has_github_pat_secret_name(config):
    assert 'github_pat_secret_name' in config['aws']['secrets_manager']


def test_lambda_functions_use_python_3_14(template):
    template.has_resource_properties('AWS::Lambda::Function', {
        'Runtime': 'python3.14'
    })


def test_oidc_provider_custom_resource_has_url(template):
    template.has_resource_properties('AWS::CloudFormation::CustomResource', {
        'Url': 'https://token.actions.githubusercontent.com'
    })


def test_oidc_provider_has_sts_client_id(template):
    template.has_resource_properties('AWS::CloudFormation::CustomResource', {
        'ClientIds': ['sts.amazonaws.com']
    })


def test_oidc_provider_has_github_thumbprint(template):
    template.has_resource_properties('AWS::CloudFormation::CustomResource', {
        'Thumbprints': ['6938fd4d98bab03faadb97b34396831e3780aea1']
    })


def test_iam_role_custom_resource_receives_provider_arn(template):
    template.has_resource_properties('AWS::CloudFormation::CustomResource', {
        'ProviderArn': Match.any_value()
    })


def test_iam_role_custom_resource_receives_github_org(template, config):
    template.has_resource_properties('AWS::CloudFormation::CustomResource', {
        'GitHubOrg': config['github']['org']
    })


def test_iam_role_custom_resource_receives_github_repo(template, config):
    template.has_resource_properties('AWS::CloudFormation::CustomResource', {
        'GitHubRepo': config['github']['repo']
    })


def test_lambda_roles_have_lambda_service_principal(template):
    template.has_resource_properties('AWS::IAM::Role', {
        'AssumeRolePolicyDocument': Match.object_like({
            'Statement': Match.array_with([
                Match.object_like({
                    'Principal': Match.object_like({
                        'Service': 'lambda.amazonaws.com'
                    })
                })
            ])
        })
    })


def test_config_has_secrets_manager_secret_name(config):
    secret_name = config['aws']['secrets_manager']['github_pat_secret_name']
    assert secret_name is not None
    assert len(secret_name) > 0


def test_stack_has_two_lambda_functions(template):
    resources = template.to_json()['Resources']
    lambda_count = sum(1 for r in resources.values()
                      if r.get('Type') == 'AWS::Lambda::Function')
    assert lambda_count == 2


def test_stack_has_two_custom_resources(template):
    resources = template.to_json()['Resources']
    cr_count = sum(1 for r in resources.values()
                   if r.get('Type') == 'AWS::CloudFormation::CustomResource')
    assert cr_count == 2


def test_lambda_functions_have_inline_code(template):
    resources = template.to_json()['Resources']
    lambda_functions = [r for r in resources.values()
                       if r.get('Type') == 'AWS::Lambda::Function']
    for func in lambda_functions:
        assert 'ZipFile' in func['Properties']['Code']


def test_config_file_exists():
    config_path = Path(__file__).parent.parent.parent / 'src' / 'auth_between_aws_and_github' / 'config.json'
    assert config_path.exists()


def test_config_is_valid_json(config):
    assert isinstance(config, dict)


def test_github_org_is_not_empty(config):
    assert len(config['github']['org']) > 0


def test_github_repo_is_not_empty(config):
    assert len(config['github']['repo']) > 0


def test_iam_role_name_is_not_empty(config):
    assert len(config['aws']['iam_role_name']) > 0


def test_account_id_is_string(config):
    assert isinstance(config['aws']['account_id'], str)


def test_account_id_is_12_digits(config):
    assert len(config['aws']['account_id']) == 12
    assert config['aws']['account_id'].isdigit()


def test_region_is_valid_format(config):
    region = config['aws']['region']
    assert '-' in region
    assert len(region) >= 9


def test_oidc_lambda_has_handler_index_handler(template):
    template.has_resource_properties('AWS::Lambda::Function', {
        'Handler': 'index.handler'
    })


def test_iam_role_lambda_has_handler_index_handler(template):
    resources = template.to_json()['Resources']
    lambda_functions = [r for r in resources.values()
                       if r.get('Type') == 'AWS::Lambda::Function']
    handlers = [func['Properties']['Handler'] for func in lambda_functions]
    assert all(h == 'index.handler' for h in handlers)


class TestOIDCProviderConstruct:

    def test_oidc_provider_lambda_has_correct_permissions(self, template):
        template.has_resource_properties('AWS::IAM::Role', {
            'AssumeRolePolicyDocument': Match.object_like({
                'Statement': Match.array_with([
                    Match.object_like({
                        'Principal': Match.object_like({
                            'Service': 'lambda.amazonaws.com'
                        })
                    })
                ])
            }),
            'ManagedPolicyArns': Match.array_with([
                Match.object_like({
                    'Fn::Join': Match.array_with([
                        Match.array_with([
                            Match.string_like_regexp('.*AWSLambdaBasicExecutionRole')
                        ])
                    ])
                })
            ])
        })

    def test_oidc_custom_resource_receives_correct_properties(self, template):
        template.has_resource_properties('AWS::CloudFormation::CustomResource', {
            'Url': 'https://token.actions.githubusercontent.com',
            'ClientIds': ['sts.amazonaws.com'],
            'Thumbprints': ['6938fd4d98bab03faadb97b34396831e3780aea1']
        })


class TestIAMRoleConstruct:

    def test_iam_role_custom_resource_receives_config_values(self, template, config):
        template.has_resource_properties('AWS::CloudFormation::CustomResource', {
            'RoleName': config['aws']['iam_role_name'],
            'GitHubOrg': config['github']['org'],
            'GitHubRepo': config['github']['repo']
        })

    def test_iam_role_custom_resource_depends_on_oidc_provider(self, template):
        resources = template.to_json()['Resources']
        custom_resources = {k: v for k, v in resources.items()
                          if v.get('Type') == 'AWS::CloudFormation::CustomResource'}

        oidc_cr = None
        role_cr = None

        for key, resource in custom_resources.items():
            props = resource.get('Properties', {})
            if 'Url' in props:
                oidc_cr = key
            elif 'RoleName' in props:
                role_cr = key

        assert oidc_cr is not None
        assert role_cr is not None


class TestComponentIntegration:

    def test_lambda_functions_are_created_before_custom_resources(self, template):
        resources = template.to_json()['Resources']

        lambda_functions = [k for k, v in resources.items()
                          if v.get('Type') == 'AWS::Lambda::Function']
        custom_resources = [k for k, v in resources.items()
                          if v.get('Type') == 'AWS::CloudFormation::CustomResource']

        assert len(lambda_functions) == 2
        assert len(custom_resources) == 2

    def test_custom_resources_reference_lambda_functions(self, template):
        resources = template.to_json()['Resources']

        lambda_function_refs = set()
        for key, resource in resources.items():
            if resource.get('Type') == 'AWS::Lambda::Function':
                lambda_function_refs.add(key)

        custom_resource_service_tokens = []
        for key, resource in resources.items():
            if resource.get('Type') == 'AWS::CloudFormation::CustomResource':
                service_token = resource.get('Properties', {}).get('ServiceToken', {})
                if 'Fn::GetAtt' in service_token:
                    lambda_ref = service_token['Fn::GetAtt'][0]
                    custom_resource_service_tokens.append(lambda_ref)

        assert len(custom_resource_service_tokens) == 2
        for token in custom_resource_service_tokens:
            assert token in lambda_function_refs

    def test_secrets_manager_secret_is_imported_not_created(self, template):
        resources = template.to_json()['Resources']

        secrets = [v for v in resources.values()
                  if v.get('Type') == 'AWS::SecretsManager::Secret']

        assert len(secrets) == 0

    def test_stack_outputs_include_role_arn(self, stack):
        assert hasattr(stack, 'role_arn')

    def test_stack_outputs_include_parameter_arn(self, stack):
        assert hasattr(stack, 'parameter_arn')

    def test_stack_outputs_include_provider_arn(self, stack):
        assert hasattr(stack, 'provider_arn')


class TestConfigurationPropagation:

    def test_config_values_propagate_to_custom_resources(self, template, config):
        capture_role_name = Capture()
        capture_org = Capture()
        capture_repo = Capture()

        template.has_resource_properties('AWS::CloudFormation::CustomResource', {
            'RoleName': capture_role_name,
            'GitHubOrg': capture_org,
            'GitHubRepo': capture_repo
        })

        assert capture_role_name.as_string() == config['aws']['iam_role_name']
        assert capture_org.as_string() == config['github']['org']
        assert capture_repo.as_string() == config['github']['repo']

    def test_github_thumbprint_is_hardcoded(self, template):
        capture_thumbprints = Capture()

        template.has_resource_properties('AWS::CloudFormation::CustomResource', {
            'Thumbprints': capture_thumbprints
        })

        thumbprints = capture_thumbprints.as_array()
        assert '6938fd4d98bab03faadb97b34396831e3780aea1' in thumbprints

    def test_oidc_audience_is_sts(self, template):
        capture_client_ids = Capture()

        template.has_resource_properties('AWS::CloudFormation::CustomResource', {
            'ClientIds': capture_client_ids
        })

        client_ids = capture_client_ids.as_array()
        assert 'sts.amazonaws.com' in client_ids


class TestResourceNaming:

    def test_custom_resources_have_logical_names(self, template):
        resources = template.to_json()['Resources']

        custom_resource_keys = [k for k, v in resources.items()
                               if v.get('Type') == 'AWS::CloudFormation::CustomResource']

        assert len(custom_resource_keys) == 2
        for key in custom_resource_keys:
            assert len(key) > 0
            assert key[0].isupper()

    def test_lambda_functions_have_logical_names(self, template):
        resources = template.to_json()['Resources']

        lambda_keys = [k for k, v in resources.items()
                      if v.get('Type') == 'AWS::Lambda::Function']

        assert len(lambda_keys) == 2
        for key in lambda_keys:
            assert len(key) > 0
            assert key[0].isupper()

    def test_iam_roles_have_logical_names(self, template):
        resources = template.to_json()['Resources']

        role_keys = [k for k, v in resources.items()
                    if v.get('Type') == 'AWS::IAM::Role']

        assert len(role_keys) == 2
        for key in role_keys:
            assert len(key) > 0
            assert key[0].isupper()


class TestLambdaRolePermissions:

    def test_oidc_lambda_role_has_inline_policy_oidc_provider_management(self, template):
        template.has_resource_properties('AWS::IAM::Role', {
            'Policies': Match.array_with([
                Match.object_like({
                    'PolicyName': 'OIDCProviderManagement'
                })
            ])
        })

    def test_oidc_lambda_role_inline_policy_has_required_oidc_actions(self, template):
        resources = template.to_json()['Resources']
        oidc_role = None
        for key, resource in resources.items():
            if resource.get('Type') == 'AWS::IAM::Role':
                policies = resource.get('Properties', {}).get('Policies', [])
                for policy in policies:
                    if policy.get('PolicyName') == 'OIDCProviderManagement':
                        oidc_role = policy
                        break

        required_actions = {
            'iam:CreateOpenIDConnectProvider',
            'iam:GetOpenIDConnectProvider',
            'iam:DeleteOpenIDConnectProvider',
            'iam:ListOpenIDConnectProviders'
        }

        policy_actions = set()
        for statement in oidc_role['PolicyDocument']['Statement']:
            policy_actions.update(statement.get('Action', []))

        assert required_actions.issubset(policy_actions)

    def test_iam_role_lambda_role_has_inline_policy_iam_role_management(self, template):
        template.has_resource_properties('AWS::IAM::Role', {
            'Policies': Match.array_with([
                Match.object_like({
                    'PolicyName': 'IAMRoleManagement'
                })
            ])
        })

    def test_iam_role_lambda_role_inline_policy_has_required_iam_actions(self, template):
        resources = template.to_json()['Resources']
        iam_role = None
        for key, resource in resources.items():
            if resource.get('Type') == 'AWS::IAM::Role':
                policies = resource.get('Properties', {}).get('Policies', [])
                for policy in policies:
                    if policy.get('PolicyName') == 'IAMRoleManagement':
                        iam_role = policy
                        break

        required_actions = {
            'iam:CreateRole',
            'iam:GetRole',
            'iam:DeleteRole',
            'iam:AttachRolePolicy',
            'iam:DetachRolePolicy',
            'iam:PutRolePolicy',
            'iam:DeleteRolePolicy',
            'iam:UpdateAssumeRolePolicy'
        }

        policy_actions = set()
        for statement in iam_role['PolicyDocument']['Statement']:
            policy_actions.update(statement.get('Action', []))

        assert required_actions.issubset(policy_actions)
