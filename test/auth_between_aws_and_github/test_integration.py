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

    def test_oidc_custom_resource_exists(self, template):
        resources = template.to_json()['Resources']
        custom_resources = {k: v for k, v in resources.items()
                          if v.get('Type') == 'AWS::CloudFormation::CustomResource'}

        oidc_cr = None
        for key, resource in custom_resources.items():
            props = resource.get('Properties', {})
            if 'Url' in props:
                oidc_cr = key
                break

        assert oidc_cr is not None

    def test_iam_role_custom_resource_exists(self, template):
        resources = template.to_json()['Resources']
        custom_resources = {k: v for k, v in resources.items()
                          if v.get('Type') == 'AWS::CloudFormation::CustomResource'}

        role_cr = None
        for key, resource in custom_resources.items():
            props = resource.get('Properties', {})
            if 'RoleName' in props:
                role_cr = key
                break

        assert role_cr is not None


class TestComponentIntegration:

    def test_has_two_lambda_functions(self, template):
        resources = template.to_json()['Resources']
        lambda_functions = [k for k, v in resources.items()
                          if v.get('Type') == 'AWS::Lambda::Function']
        assert len(lambda_functions) == 2

    def test_has_two_custom_resources(self, template):
        resources = template.to_json()['Resources']
        custom_resources = [k for k, v in resources.items()
                          if v.get('Type') == 'AWS::CloudFormation::CustomResource']
        assert len(custom_resources) == 2

    def test_custom_resources_count_matches_lambda_functions(self, template):
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

    def test_all_custom_resources_reference_valid_lambda_functions(self, template):
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

        all_valid = all(token in lambda_function_refs for token in custom_resource_service_tokens)
        assert all_valid

    def test_secrets_manager_secret_is_imported_not_created(self, template):
        resources = template.to_json()['Resources']
        secrets = [v for v in resources.values()
                  if v.get('Type') == 'AWS::SecretsManager::Secret']
        assert len(secrets) == 0

    def test_stack_outputs_include_role_arn(self, stack):
        assert hasattr(stack, 'role_arn')

    def test_stack_outputs_include_secret_arn(self, stack):
        assert hasattr(stack, 'secret_arn')

    def test_stack_outputs_include_provider_arn(self, stack):
        assert hasattr(stack, 'provider_arn')


class TestConfigurationPropagation:

    def test_role_name_propagates_to_custom_resource(self, template, config):
        capture_role_name = Capture()
        template.has_resource_properties('AWS::CloudFormation::CustomResource', {
            'RoleName': capture_role_name
        })
        assert capture_role_name.as_string() == config['aws']['iam_role_name']

    def test_github_org_propagates_to_custom_resource(self, template, config):
        capture_org = Capture()
        template.has_resource_properties('AWS::CloudFormation::CustomResource', {
            'GitHubOrg': capture_org
        })
        assert capture_org.as_string() == config['github']['org']

    def test_github_repo_propagates_to_custom_resource(self, template, config):
        capture_repo = Capture()
        template.has_resource_properties('AWS::CloudFormation::CustomResource', {
            'GitHubRepo': capture_repo
        })
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

    def test_has_two_custom_resources_with_names(self, template):
        resources = template.to_json()['Resources']
        custom_resource_keys = [k for k, v in resources.items()
                               if v.get('Type') == 'AWS::CloudFormation::CustomResource']
        assert len(custom_resource_keys) == 2

    def test_custom_resource_names_are_not_empty(self, template):
        resources = template.to_json()['Resources']
        custom_resource_keys = [k for k, v in resources.items()
                               if v.get('Type') == 'AWS::CloudFormation::CustomResource']
        all_non_empty = all(len(key) > 0 for key in custom_resource_keys)
        assert all_non_empty

    def test_custom_resource_names_start_uppercase(self, template):
        resources = template.to_json()['Resources']
        custom_resource_keys = [k for k, v in resources.items()
                               if v.get('Type') == 'AWS::CloudFormation::CustomResource']
        all_uppercase = all(key[0].isupper() for key in custom_resource_keys)
        assert all_uppercase

    def test_has_two_lambda_functions_with_names(self, template):
        resources = template.to_json()['Resources']
        lambda_keys = [k for k, v in resources.items()
                      if v.get('Type') == 'AWS::Lambda::Function']
        assert len(lambda_keys) == 2

    def test_lambda_function_names_are_not_empty(self, template):
        resources = template.to_json()['Resources']
        lambda_keys = [k for k, v in resources.items()
                      if v.get('Type') == 'AWS::Lambda::Function']
        all_non_empty = all(len(key) > 0 for key in lambda_keys)
        assert all_non_empty

    def test_lambda_function_names_start_uppercase(self, template):
        resources = template.to_json()['Resources']
        lambda_keys = [k for k, v in resources.items()
                      if v.get('Type') == 'AWS::Lambda::Function']
        all_uppercase = all(key[0].isupper() for key in lambda_keys)
        assert all_uppercase

    def test_has_two_iam_roles_with_names(self, template):
        resources = template.to_json()['Resources']
        role_keys = [k for k, v in resources.items()
                    if v.get('Type') == 'AWS::IAM::Role']
        assert len(role_keys) == 2

    def test_iam_role_names_are_not_empty(self, template):
        resources = template.to_json()['Resources']
        role_keys = [k for k, v in resources.items()
                    if v.get('Type') == 'AWS::IAM::Role']
        all_non_empty = all(len(key) > 0 for key in role_keys)
        assert all_non_empty

    def test_iam_role_names_start_uppercase(self, template):
        resources = template.to_json()['Resources']
        role_keys = [k for k, v in resources.items()
                    if v.get('Type') == 'AWS::IAM::Role']
        all_uppercase = all(key[0].isupper() for key in role_keys)
        assert all_uppercase


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
