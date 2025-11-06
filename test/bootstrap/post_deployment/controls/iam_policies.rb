# frozen_string_literal: true

#
# IAM Policies Compliance Control
#
# Validates that the GitHub Actions IAM role has the correct permissions
# (PowerUserAccess + IAM management) for infrastructure deployment.
#

control 'iam-role-has-poweruser-access' do
  impact 1.0
  title 'IAM Role Has PowerUserAccess Managed Policy'
  desc 'Verify role has AWS managed PowerUserAccess policy attached'

  describe 'PowerUserAccess Policy' do
    it 'should have attached policies' do
      region = input('region')
      role_name = input('iam_role_name')

      attached_policies_data = json(command: "aws iam list-attached-role-policies --role-name #{role_name} --region #{region} --output json")
      
      expect(attached_policies_data['AttachedPolicies']).not_to be_empty
    end

    it 'should be attached to the role' do
      region = input('region')
      role_name = input('iam_role_name')
      poweruser_policy_arn = 'arn:aws:iam::aws:policy/PowerUserAccess'

      attached_policies = json(command: "aws iam list-attached-role-policies --role-name #{role_name} --region #{region} --output json")
      policy_arns = attached_policies['AttachedPolicies'].map { |p| p['PolicyArn'] }
      
      expect(policy_arns).to include(poweruser_policy_arn)
    end
  end
end

control 'iam-role-has-iam-management-inline-policy' do
  impact 1.0
  title 'IAM Role Has IAM Management Inline Policy'
  desc 'Verify role has inline policy for IAM management permissions'

  describe 'IAM Management Inline Policy' do
    it 'should exist with correct name' do
      region = input('region')
      role_name = input('iam_role_name')
      inline_policy_name = 'IAMRoleManagement'

      policy_data = json(command: "aws iam get-role-policy --role-name #{role_name} --policy-name #{inline_policy_name} --region #{region} --output json 2>&1")
      
      expect(policy_data['PolicyName']).to eq(inline_policy_name)
    end
  end
end

control 'iam-role-iam-policy-has-required-permissions' do
  impact 1.0
  title 'IAM Management Policy Has Required Permissions'
  desc 'Verify IAM management inline policy includes all necessary IAM permissions'

  required_iam_actions = [
    'iam:CreateRole',
    'iam:DeleteRole',
    'iam:GetRole',
    'iam:AttachRolePolicy',
    'iam:DetachRolePolicy',
    'iam:PutRolePolicy',
    'iam:DeleteRolePolicy',
    'iam:GetRolePolicy',
    'iam:ListAttachedRolePolicies',
    'iam:ListRolePolicies',
    'iam:PassRole',
    'iam:CreateOpenIDConnectProvider',
    'iam:DeleteOpenIDConnectProvider',
    'iam:GetOpenIDConnectProvider',
    'iam:UpdateAssumeRolePolicy'
  ]

  describe 'IAM Management Policy Actions' do
    required_iam_actions.each do |action|
      it "should include #{action}" do
        region = input('region')
        role_name = input('iam_role_name')
        inline_policy_name = 'IAMRoleManagement'

        policy_data = json(command: "aws iam get-role-policy --role-name #{role_name} --policy-name #{inline_policy_name} --region #{region} --output json")
        policy_document = policy_data['PolicyDocument']

        # Extract all actions from the policy
        all_actions = []
        policy_document['Statement'].each do |statement|
          actions = statement['Action']
          if actions.is_a?(Array)
            all_actions.concat(actions)
          else
            all_actions << actions
          end
        end

        expect(all_actions).to include(action)
      end
    end
  end
end

control 'iam-role-no-admin-access' do
  impact 1.0
  title 'IAM Role Does Not Have AdministratorAccess'
  desc 'Verify role does not have overly permissive AdministratorAccess policy'

  describe 'Administrator Access Policy' do
    it 'should NOT be attached to the role' do
      region = input('region')
      role_name = input('iam_role_name')
      admin_policy_arn = 'arn:aws:iam::aws:policy/AdministratorAccess'

      attached_policies = json(command: "aws iam list-attached-role-policies --role-name #{role_name} --region #{region} --output json")
      policy_arns = attached_policies['AttachedPolicies'].map { |p| p['PolicyArn'] }
      
      expect(policy_arns).not_to include(admin_policy_arn)
    end
  end
end

control 'iam-role-inline-policies-limited' do
  impact 0.7
  title 'Limited Number of Inline Policies'
  desc 'Verify role does not have excessive number of inline policies (security hygiene)'

  describe 'Inline Policies Count' do
    it 'should have a reasonable number of inline policies' do
      region = input('region')
      role_name = input('iam_role_name')

      inline_policies = json(command: "aws iam list-role-policies --role-name #{role_name} --region #{region} --output json")
      policy_count = inline_policies['PolicyNames'].length
      
      # Should typically have 1 inline policy (IAMRoleManagement)
      # More than 3 might indicate policy sprawl
      expect(policy_count).to be <= 3
    end
  end
end

control 'iam-role-managed-policies-limited' do
  impact 0.5
  title 'Limited Number of Managed Policies'
  desc 'Verify role does not have excessive number of managed policies (security hygiene)'

  describe 'Managed Policies Count' do
    it 'should have a reasonable number of managed policies' do
      region = input('region')
      role_name = input('iam_role_name')

      attached_policies = json(command: "aws iam list-attached-role-policies --role-name #{role_name} --region #{region} --output json")
      policy_count = attached_policies['AttachedPolicies'].length
      
      # Should typically have 1 managed policy (PowerUserAccess)
      # More than 5 might indicate policy sprawl
      expect(policy_count).to be <= 5
    end
  end
end

control 'iam-role-policy-least-privilege' do
  impact 0.8
  title 'IAM Management Policy Follows Least Privilege'
  desc 'Verify IAM management policy does not grant excessive wildcard permissions'

  describe 'IAM Policy Least Privilege' do
    it 'should not grant wildcard actions on all resources' do
      region = input('region')
      role_name = input('iam_role_name')
      inline_policy_name = 'IAMRoleManagement'

      policy_data = json(command: "aws iam get-role-policy --role-name #{role_name} --policy-name #{inline_policy_name} --region #{region} --output json")
      policy_document = policy_data['PolicyDocument']

      policy_document['Statement'].each do |statement|
        # If Effect is Allow
        if statement['Effect'] == 'Allow'
          action = statement['Action']
          resource = statement['Resource']

          # If action is wildcard AND resource is wildcard, that's too permissive
          # (except for specific services that require it like IAM)
          if (action == '*' || (action.is_a?(Array) && action.include?('*'))) &&
             (resource == '*')
            # This is overly permissive - should fail
            # Note: IAM actions require Resource: * but Action should be scoped
            expect(action).not_to eq('*'), 'Policy should not grant Action: * on Resource: *'
          end
        end
      end
    end

    it 'should have specific IAM actions, not iam:*' do
      region = input('region')
      role_name = input('iam_role_name')
      inline_policy_name = 'IAMRoleManagement'

      policy_data = json(command: "aws iam get-role-policy --role-name #{role_name} --policy-name #{inline_policy_name} --region #{region} --output json")
      policy_document = policy_data['PolicyDocument']

      policy_document['Statement'].each do |statement|
        if statement['Effect'] == 'Allow'
          action = statement['Action']
          if action.is_a?(Array)
            expect(action).not_to include('iam:*')
          else
            expect(action).not_to eq('iam:*')
          end
        end
      end
    end
  end
end
