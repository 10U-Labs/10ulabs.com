# frozen_string_literal: true

#
# IAM Role and Trust Policy Compliance Control
#
# Validates that the GitHub Actions IAM role is configured securely
# with proper trust policy restrictions.
#

control 'iam-role-exists' do
  impact 1.0
  title 'GitHub Actions IAM Role Exists'
  desc 'Verify IAM role for GitHub Actions exists'

  describe 'IAM Role Existence' do
    it 'should exist' do
      role_name = input('iam_role_name')

      role = aws_iam_role(role_name)
      expect(role.exists?).to be true
    end
  end
end

control 'iam-role-trust-policy-oidc-only' do
  impact 1.0
  title 'Trust Policy Allows OIDC Authentication Only'
  desc 'Verify role can only be assumed via OIDC, not by AWS accounts or users'

  describe 'Trust Policy Principal' do
    it 'should only allow Federated (OIDC) principal' do
      role_name = input('iam_role_name')
      region = input('region')

      role_data = json(command: "aws iam get-role --role-name #{role_name} --region #{region} --output json")
      trust_policy = role_data['Role']['AssumeRolePolicyDocument']
      statements = trust_policy['Statement']

      expect(statements.length).to be >= 1

      statements.each do |statement|
        # Each statement should have Federated principal
        expect(statement['Principal']).to have_key('Federated')
        # Should NOT have AWS principal (accounts/users)
        expect(statement['Principal']).not_to have_key('AWS')
        # Should NOT have Service principal
        expect(statement['Principal']).not_to have_key('Service')
        # Should NOT be wildcard
        expect(statement['Principal']).not_to eq('*')
      end
    end
  end
end

control 'iam-role-trust-policy-github-oidc' do
  impact 1.0
  title 'Trust Policy Uses GitHub Actions OIDC Provider'
  desc 'Verify trust policy references the correct GitHub Actions OIDC provider'

  describe 'Trust Policy OIDC Provider' do
    it 'should reference GitHub Actions OIDC provider' do
      account_id = input('account_id')
      role_name = input('iam_role_name')
      region = input('region')

      role_data = json(command: "aws iam get-role --role-name #{role_name} --region #{region} --output json")
      trust_policy = role_data['Role']['AssumeRolePolicyDocument']
      expected_oidc_arn = "arn:aws:iam::#{account_id}:oidc-provider/token.actions.githubusercontent.com"

      statements = trust_policy['Statement']
      oidc_principals = statements.map { |s| s.dig('Principal', 'Federated') }.compact

      expect(oidc_principals).to include(expected_oidc_arn)
    end
  end
end

control 'iam-role-trust-policy-action' do
  impact 1.0
  title 'Trust Policy Only Allows AssumeRoleWithWebIdentity'
  desc 'Verify trust policy only allows AssumeRoleWithWebIdentity action, not AssumeRole'

  describe 'Trust Policy Action' do
    it 'should only allow AssumeRoleWithWebIdentity' do
      role_name = input('iam_role_name')
      region = input('region')

      role_data = json(command: "aws iam get-role --role-name #{role_name} --region #{region} --output json")
      trust_policy = role_data['Role']['AssumeRolePolicyDocument']
      statements = trust_policy['Statement']

      statements.each do |statement|
        action = statement['Action']
        # Action should be AssumeRoleWithWebIdentity (string or array)
        if action.is_a?(Array)
          expect(action).to include('sts:AssumeRoleWithWebIdentity')
          expect(action).not_to include('sts:AssumeRole')
        else
          expect(action).to eq('sts:AssumeRoleWithWebIdentity')
        end
      end
    end
  end
end

control 'iam-role-trust-policy-audience' do
  impact 1.0
  title 'Trust Policy Requires Correct Audience'
  desc 'Verify trust policy requires sts.amazonaws.com audience to prevent token replay attacks'

  describe 'Trust Policy Audience Condition' do
    it 'should require sts.amazonaws.com audience' do
      role_name = input('iam_role_name')
      region = input('region')

      role_data = json(command: "aws iam get-role --role-name #{role_name} --region #{region} --output json")
      trust_policy = role_data['Role']['AssumeRolePolicyDocument']
      statements = trust_policy['Statement']

      has_audience_condition = statements.any? do |statement|
        conditions = statement['Condition'] || {}
        string_equals = conditions['StringEquals'] || {}
        aud = string_equals['token.actions.githubusercontent.com:aud']
        aud == 'sts.amazonaws.com'
      end

      expect(has_audience_condition).to be true
    end
  end
end

control 'iam-role-trust-policy-repo-restriction' do
  impact 1.0
  title 'Trust Policy Restricts to Specific GitHub Repository'
  desc 'Verify trust policy only allows specific GitHub org/repo, not wildcards'

  describe 'Trust Policy Repository Restriction' do
    it 'should restrict to specific GitHub org/repo' do
      role_name = input('iam_role_name')
      region = input('region')
      github_org = input('github_org')
      github_repo = input('github_repo')

      role_data = json(command: "aws iam get-role --role-name #{role_name} --region #{region} --output json")
      trust_policy = role_data['Role']['AssumeRolePolicyDocument']
      expected_sub_pattern = "repo:#{github_org}/#{github_repo}:*"

      statements = trust_policy['Statement']

      has_repo_condition = statements.any? do |statement|
        conditions = statement['Condition'] || {}
        string_like = conditions['StringLike'] || {}
        sub = string_like['token.actions.githubusercontent.com:sub']
        sub == expected_sub_pattern
      end

      expect(has_repo_condition).to be true
    end

    it 'should not allow wildcard org or repo' do
      role_name = input('iam_role_name')
      region = input('region')

      role_data = json(command: "aws iam get-role --role-name #{role_name} --region #{region} --output json")
      trust_policy = role_data['Role']['AssumeRolePolicyDocument']

      statements = trust_policy['Statement']

      statements.each do |statement|
        conditions = statement['Condition'] || {}
        string_like = conditions['StringLike'] || {}
        sub = string_like['token.actions.githubusercontent.com:sub']

        next if sub.nil?

        # Should not allow 'repo:*/*:*' or 'repo:org/*:*'
        expect(sub).not_to match(/^repo:\*\//)
        expect(sub).not_to match(/^repo:[^\/]+\/\*:/)
      end
    end
  end
end

control 'iam-role-trust-policy-no-unconditional-access' do
  impact 1.0
  title 'Trust Policy Has Proper Conditions'
  desc 'Verify trust policy does not allow unconditional access'

  describe 'Trust Policy Conditions' do
    it 'should have conditions on all Allow statements' do
      role_name = input('iam_role_name')
      region = input('region')

      role_data = json(command: "aws iam get-role --role-name #{role_name} --region #{region} --output json")
      trust_policy = role_data['Role']['AssumeRolePolicyDocument']
      statements = trust_policy['Statement']

      allow_statements = statements.select { |s| s['Effect'] == 'Allow' }

      allow_statements.each do |statement|
        # Every Allow statement should have Condition
        expect(statement).to have_key('Condition')
        expect(statement['Condition']).not_to be_empty
      end
    end
  end
end

control 'iam-role-no-overly-permissive-trust' do
  impact 1.0
  title 'No Overly Permissive Trust Relationships'
  desc 'Verify role cannot be assumed by public or anonymous principals'

  describe 'Trust Policy Security' do
    it 'should not allow anonymous access' do
      role_name = input('iam_role_name')
      region = input('region')

      role_data = json(command: "aws iam get-role --role-name #{role_name} --region #{region} --output json")
      trust_policy = role_data['Role']['AssumeRolePolicyDocument']
      statements = trust_policy['Statement']

      statements.each do |statement|
        principal = statement['Principal']

        # Should not be wildcard principal
        expect(principal).not_to eq('*')

        # Should not have AWS: *
        if principal.is_a?(Hash) && principal.key?('AWS')
          expect(principal['AWS']).not_to eq('*')
        end
      end
    end
  end
end
