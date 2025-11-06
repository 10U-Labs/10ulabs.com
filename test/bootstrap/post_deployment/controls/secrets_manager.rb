# frozen_string_literal: true

#
# Secrets Manager Compliance Control
#
# Validates that GitHub PAT secret is stored securely in AWS Secrets Manager
# with proper encryption and structure.
#

control 'secrets-manager-secret-exists' do
  impact 1.0
  title 'GitHub PAT Secret Exists'
  desc 'Verify GitHub PAT secret exists in AWS Secrets Manager'

  describe 'GitHub PAT Secret' do
    it 'should exist with correct name and ARN' do
      region = input('region')
      secret_name = input('github_pat_secret_name')

      secret_data = json(command: "aws secretsmanager describe-secret --secret-id #{secret_name} --region #{region} --output json")

      expect(secret_data['Name']).to eq(secret_name)
      expect(secret_data['ARN']).not_to be_nil
    end
  end
end

control 'secrets-manager-secret-encrypted' do
  impact 1.0
  title 'Secret is Encrypted with KMS'
  desc 'Verify secret is encrypted at rest using AWS KMS'

  describe 'Secret Encryption' do
    it 'should have KMS key ID' do
      region = input('region')
      secret_name = input('github_pat_secret_name')

      secret_data = json(command: "aws secretsmanager describe-secret --secret-id #{secret_name} --region #{region} --output json")

      # Should have KMS key ID (either custom or default)
      expect(secret_data['KmsKeyId']).not_to be_nil
    end
  end
end

control 'secrets-manager-secret-not-deleted' do
  impact 1.0
  title 'Secret is Not Scheduled for Deletion'
  desc 'Verify secret is active and not scheduled for deletion'

  describe 'Secret Deletion Status' do
    it 'should not be scheduled for deletion' do
      region = input('region')
      secret_name = input('github_pat_secret_name')

      secret_data = json(command: "aws secretsmanager describe-secret --secret-id #{secret_name} --region #{region} --output json")

      # DeletedDate should not exist
      expect(secret_data['DeletedDate']).to be_nil
    end
  end
end

control 'secrets-manager-secret-structure' do
  impact 1.0
  title 'Secret Has Correct Structure'
  desc 'Verify secret contains all required fields with correct values'

  describe 'Secret Structure' do
    it 'should have auth_method field' do
      region = input('region')
      secret_name = input('github_pat_secret_name')

      secret_value = json(command: "aws secretsmanager get-secret-value --secret-id #{secret_name} --region #{region} --query SecretString --output text")

      expect(secret_value['auth_method']).to eq('classic-pat')
    end

    it 'should have github_token field' do
      region = input('region')
      secret_name = input('github_pat_secret_name')

      secret_value = json(command: "aws secretsmanager get-secret-value --secret-id #{secret_name} --region #{region} --query SecretString --output text")

      expect(secret_value['github_token']).not_to be_nil
      expect(secret_value['github_token']).not_to be_empty
    end

    it 'should have github_org field matching configuration' do
      region = input('region')
      secret_name = input('github_pat_secret_name')
      github_org = input('github_org')

      secret_value = json(command: "aws secretsmanager get-secret-value --secret-id #{secret_name} --region #{region} --query SecretString --output text")

      expect(secret_value['github_org']).to eq(github_org)
    end

    it 'should have github_repo field matching configuration' do
      region = input('region')
      secret_name = input('github_pat_secret_name')
      github_repo = input('github_repo')

      secret_value = json(command: "aws secretsmanager get-secret-value --secret-id #{secret_name} --region #{region} --query SecretString --output text")

      expect(secret_value['github_repo']).to eq(github_repo)
    end

    it 'should have created_by field' do
      region = input('region')
      secret_name = input('github_pat_secret_name')

      secret_value = json(command: "aws secretsmanager get-secret-value --secret-id #{secret_name} --region #{region} --query SecretString --output text")

      expect(secret_value['created_by']).to eq('bootstrap-script')
    end

    it 'should have created_at timestamp' do
      region = input('region')
      secret_name = input('github_pat_secret_name')

      secret_value = json(command: "aws secretsmanager get-secret-value --secret-id #{secret_name} --region #{region} --query SecretString --output text")

      expect(secret_value['created_at']).not_to be_nil
      expect(secret_value['created_at']).not_to be_empty
    end
  end
end

control 'secrets-manager-secret-token-format' do
  impact 1.0
  title 'GitHub Token Has Valid Format'
  desc 'Verify GitHub PAT token follows expected format'

  describe 'GitHub Token Format' do
    it 'should start with ghp_ prefix for classic PAT' do
      region = input('region')
      secret_name = input('github_pat_secret_name')

      secret_value = json(command: "aws secretsmanager get-secret-value --secret-id #{secret_name} --region #{region} --query SecretString --output text")

      token = secret_value['github_token']
      expect(token).to match(/^ghp_/)
    end

    it 'should not be a placeholder or test value' do
      region = input('region')
      secret_name = input('github_pat_secret_name')

      secret_value = json(command: "aws secretsmanager get-secret-value --secret-id #{secret_name} --region #{region} --query SecretString --output text")

      token = secret_value['github_token']
      expect(token).not_to match(/test|example|placeholder|dummy/i)
    end
  end
end

control 'secrets-manager-no-public-access' do
  impact 1.0
  title 'Secret Has No Resource Policy Allowing Public Access'
  desc 'Verify secret does not have a resource policy allowing public access'

  describe 'Secret Resource Policy' do
    it 'should not allow public access if policy exists' do
      region = input('region')
      secret_name = input('github_pat_secret_name')

      # Check if secret has resource policy
      policy_result = command("aws secretsmanager get-resource-policy --secret-id #{secret_name} --region #{region} --output json 2>&1")

      if policy_result.exit_status == 0
        policy_data = JSON.parse(policy_result.stdout)

        if policy_data.key?('ResourcePolicy')
          policy = JSON.parse(policy_data['ResourcePolicy'])
          statements = policy['Statement'] || []

          statements.each do |statement|
            # Principal should not be wildcard
            expect(statement['Principal']).not_to eq('*')

            if statement['Principal'].is_a?(Hash)
              expect(statement['Principal']['AWS']).not_to eq('*') if statement['Principal'].key?('AWS')
            end
          end
        end
      end
      # If no policy exists (ResourceNotFoundException), that's fine - defaults to private
    end
  end
end
