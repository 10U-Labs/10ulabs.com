# frozen_string_literal: true

#
# Integration Tests for GitHub Self-Hosted Runners Infrastructure
#
# These tests validate cross-resource relationships and integrations:
# - VPC ↔ Internet Gateway attachment
# - Lambda ↔ IAM role permissions
# - API Gateway ↔ Lambda integration
#

# Load configuration from inputs
vpc_name = input('vpc_name')
lambda_name = input('lambda_name')
api_gateway_name = input('api_gateway_name')

# Helper: Get VPC ID from name
def get_vpc_id(vpc_name)
  result = json(command: "aws ec2 describe-vpcs --filters Name=tag:Name,Values=#{vpc_name} --output json")
  result['Vpcs'].first['VpcId'] if result['Vpcs']&.any?
end

vpc_id = get_vpc_id(vpc_name)

# =============================================================================
# VPC Integration Tests
# =============================================================================

control 'vpc-internet-gateway' do
  impact 1.0
  title 'Internet Gateway Integration'
  desc 'Verify Internet Gateway is attached to VPC'

  # Get IGW ID from VPC
  igw_result = json(command: "aws ec2 describe-internet-gateways --filters Name=attachment.vpc-id,Values=#{vpc_id} --output json")
  igw_id = igw_result['InternetGateways'].first['InternetGatewayId'] if igw_result['InternetGateways']&.any?

  describe aws_internet_gateway(id: igw_id) do
    it { should exist }
    it { should be_attached }
  end
end

# =============================================================================
# Lambda Integration Tests
# =============================================================================

control 'lambda-has-iam-role' do
  impact 1.0
  title 'Lambda IAM Role Integration'
  desc 'Verify Lambda has an execution role with appropriate permissions'

  lambda = aws_lambda(lambda_name: lambda_name)
  role_arn = lambda.role

  describe aws_iam_role(role_arn.split('/')[-1]) do
    it { should exist }
  end
end

# =============================================================================
# API Gateway Integration Tests
# =============================================================================

control 'api-gateway-lambda-integration' do
  impact 1.0
  title 'API Gateway Lambda Integration'
  desc 'Verify API Gateway is integrated with Lambda function'

  # Get API ID
  api_result = json(command: "aws apigatewayv2 get-apis --output json")
  api = api_result['Items'].find { |a| a['Name'] == api_gateway_name }

  if api
    api_id = api['ApiId']

    describe "API Gateway #{api_id} integrations" do
      it 'has at least one Lambda integration' do
        integrations = json(command: "aws apigatewayv2 get-integrations --api-id #{api_id} --output json")
        lambda_integrations = integrations['Items'].select { |i| i['IntegrationType'] == 'AWS_PROXY' }
        expect(lambda_integrations.length).to be >= 1
      end
    end
  end
end
