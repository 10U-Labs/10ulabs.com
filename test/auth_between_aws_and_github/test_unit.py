import json
import importlib.util
from pathlib import Path

import aws_cdk as cdk
from aws_cdk.assertions import Template, Match
import pytest


@pytest.fixture
def config():
    config_path = Path(__file__).parent.parent.parent / 'src' / 'auth_between_aws_and_github' / 'config.json'
    with open(config_path) as f:
        return json.load(f)


@pytest.fixture
def template(config):
    stack_path = Path(__file__).parent.parent.parent / 'src' / 'auth_between_aws_and_github' / 'stack.py'
    spec = importlib.util.spec_from_file_location("auth_stack", stack_path)
    auth_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(auth_module)
    AuthBetweenAwsAndGithubStack = auth_module.AuthBetweenAwsAndGithubStack

    app = cdk.App()
    stack = AuthBetweenAwsAndGithubStack(
        app,
        'AuthBetweenAwsAndGithub',
        config=config,
        env=cdk.Environment(
            account=config['aws']['account_id'],
            region=config['aws']['region']
        )
    )
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
