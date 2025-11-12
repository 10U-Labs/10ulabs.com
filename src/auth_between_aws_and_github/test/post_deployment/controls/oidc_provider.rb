# frozen_string_literal: true

#
# OIDC Provider Compliance Control
#
# Validates that the GitHub Actions OIDC provider is configured correctly
# for secure authentication with AWS.
#

control 'oidc-provider-exists' do
  impact 1.0
  title 'GitHub Actions OIDC Provider Exists'
  desc 'Verify OIDC provider for GitHub Actions exists in AWS account'

  describe 'OIDC Provider Configuration' do
    it 'should exist and have correct URL' do
      account_id = input('account_id')
      region = input('region')
      oidc_provider_arn = "arn:aws:iam::#{account_id}:oidc-provider/token.actions.githubusercontent.com"

      provider = json(command: "aws iam get-open-id-connect-provider --open-id-connect-provider-arn #{oidc_provider_arn} --region #{region} --output json")

      expect(provider['Url']).to eq('token.actions.githubusercontent.com')
      expect(provider['ClientIDList']).to include('sts.amazonaws.com')
    end
  end
end

control 'oidc-provider-thumbprint' do
  impact 1.0
  title 'OIDC Provider Has Correct Thumbprint'
  desc 'Verify OIDC provider has the correct GitHub Actions thumbprint for SSL verification'

  describe 'OIDC Provider Thumbprint' do
    it 'should have the correct GitHub Actions thumbprint' do
      account_id = input('account_id')
      region = input('region')
      oidc_provider_arn = "arn:aws:iam::#{account_id}:oidc-provider/token.actions.githubusercontent.com"

      # GitHub Actions OIDC thumbprint (SHA-1 fingerprint of GitHub's root CA)
      expected_thumbprint = '6938fd4d98bab03faadb97b34396831e3780aea1'

      provider = json(command: "aws iam get-open-id-connect-provider --open-id-connect-provider-arn #{oidc_provider_arn} --region #{region} --output json")

      expect(provider['ThumbprintList']).to include(expected_thumbprint)
    end
  end
end

control 'oidc-provider-audience' do
  impact 1.0
  title 'OIDC Provider Audience Configuration'
  desc 'Verify OIDC provider is configured with correct audience (sts.amazonaws.com) for AWS STS'

  describe 'OIDC Provider Audience' do
    it 'should be configured with sts.amazonaws.com audience' do
      account_id = input('account_id')
      region = input('region')
      oidc_provider_arn = "arn:aws:iam::#{account_id}:oidc-provider/token.actions.githubusercontent.com"

      provider = json(command: "aws iam get-open-id-connect-provider --open-id-connect-provider-arn #{oidc_provider_arn} --region #{region} --output json")

      expect(provider['ClientIDList']).to include('sts.amazonaws.com')
      # Should not have wildcard audience
      expect(provider['ClientIDList']).not_to include('*')
    end
  end
end

control 'oidc-provider-url' do
  impact 1.0
  title 'OIDC Provider URL is GitHub Actions'
  desc 'Verify OIDC provider URL points to GitHub Actions and not another provider'

  describe 'OIDC Provider URL' do
    it 'should point to GitHub Actions' do
      account_id = input('account_id')
      region = input('region')
      oidc_provider_arn = "arn:aws:iam::#{account_id}:oidc-provider/token.actions.githubusercontent.com"

      provider = json(command: "aws iam get-open-id-connect-provider --open-id-connect-provider-arn #{oidc_provider_arn} --region #{region} --output json")

      expect(provider['Url']).to eq('token.actions.githubusercontent.com')
      # Should not be generic OIDC provider
      expect(provider['Url']).not_to match(/amazonaws\.com/)
      expect(provider['Url']).not_to match(/google/)
      expect(provider['Url']).not_to match(/okta/)
    end
  end
end
