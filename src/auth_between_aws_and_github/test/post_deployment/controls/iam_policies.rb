# frozen_string_literal: true

#
# IAM Policies Compliance Control
#
# Validates that the GitHub Actions IAM role has AdministratorAccess
# for full infrastructure deployment capabilities.
#

control 'iam-role-has-administrator-access' do
  impact 1.0
  title 'IAM Role Has AdministratorAccess Managed Policy'
  desc 'Verify role has AWS managed AdministratorAccess policy attached'

  describe 'AdministratorAccess Policy' do
    it 'should have attached policies' do
      region = input('region')
      role_name = input('iam_role_name')

      attached_policies_data = json(command: "aws iam list-attached-role-policies --role-name #{role_name} --region #{region} --output json")

      expect(attached_policies_data['AttachedPolicies']).not_to be_empty
    end

    it 'should be attached to the role' do
      region = input('region')
      role_name = input('iam_role_name')
      admin_policy_arn = 'arn:aws:iam::aws:policy/AdministratorAccess'

      attached_policies = json(command: "aws iam list-attached-role-policies --role-name #{role_name} --region #{region} --output json")
      policy_arns = attached_policies['AttachedPolicies'].map { |p| p['PolicyArn'] }

      expect(policy_arns).to include(admin_policy_arn)
    end
  end
end

control 'iam-role-has-no-inline-policies' do
  impact 1.0
  title 'IAM Role Has No Inline Policies'
  desc 'Verify role has no inline policies (all permissions via managed policy)'

  describe 'Inline Policies' do
    it 'should have zero inline policies' do
      region = input('region')
      role_name = input('iam_role_name')

      inline_policies = json(command: "aws iam list-role-policies --role-name #{role_name} --region #{region} --output json")
      policy_count = inline_policies['PolicyNames'].length

      expect(policy_count).to eq(0)
    end
  end
end

control 'iam-role-has-only-administrator-access' do
  impact 1.0
  title 'IAM Role Has Only AdministratorAccess Policy'
  desc 'Verify role has exactly one managed policy (AdministratorAccess) and no others'

  describe 'Managed Policies' do
    it 'should have exactly one managed policy' do
      region = input('region')
      role_name = input('iam_role_name')

      attached_policies = json(command: "aws iam list-attached-role-policies --role-name #{role_name} --region #{region} --output json")
      policy_count = attached_policies['AttachedPolicies'].length

      expect(policy_count).to eq(1)
    end

    it 'should be AdministratorAccess and nothing else' do
      region = input('region')
      role_name = input('iam_role_name')
      admin_policy_arn = 'arn:aws:iam::aws:policy/AdministratorAccess'

      attached_policies = json(command: "aws iam list-attached-role-policies --role-name #{role_name} --region #{region} --output json")
      policy_arns = attached_policies['AttachedPolicies'].map { |p| p['PolicyArn'] }

      expect(policy_arns).to eq([admin_policy_arn])
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

      # Should have exactly 1 managed policy (AdministratorAccess)
      # More than 2 might indicate policy sprawl
      expect(policy_count).to be <= 2
    end
  end
end
