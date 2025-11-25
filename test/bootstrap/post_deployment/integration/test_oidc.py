def test_oidc_provider_exists_in_aws(iam_client, config):
    account_id = config['aws_account_id']
    provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    response = iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
    assert response['Url'] == 'token.actions.githubusercontent.com'


def test_oidc_provider_has_correct_thumbprint(iam_client, config):
    account_id = config['aws_account_id']
    provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    response = iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
    thumbprint = response['ThumbprintList'][0]
    assert thumbprint == '6938fd4d98bab03faadb97b34396831e3780aea1'


def test_oidc_provider_has_correct_client_id(iam_client, config):
    account_id = config['aws_account_id']
    provider_arn = f"arn:aws:iam::{account_id}:oidc-provider/token.actions.githubusercontent.com"
    response = iam_client.get_open_id_connect_provider(OpenIDConnectProviderArn=provider_arn)
    client_id = response['ClientIDList'][0]
    assert client_id == 'sts.amazonaws.com'
