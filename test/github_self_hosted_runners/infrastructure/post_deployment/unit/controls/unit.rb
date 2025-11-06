# frozen_string_literal: true

#
# Post-Deployment Validation for GitHub Self-Hosted Runners Infrastructure
#
# This CINC profile validates that the AWS infrastructure for GitHub
# self-hosted runners was deployed correctly and follows our cost optimization
# and security best practices.
#

# Load configuration from inputs
vpc_name = input('vpc_name')
vpc_cidr = input('vpc_cidr')
cluster_name = input('cluster_name')
lambda_name = input('lambda_name')
lambda_timeout = input('lambda_timeout')
lambda_memory = input('lambda_memory')
api_gateway_name = input('api_gateway_name')

# Helper: Get VPC ID from name
def get_vpc_id(vpc_name)
  result = json(command: "aws ec2 describe-vpcs --filters Name=tag:Name,Values=#{vpc_name} --output json")
  result['Vpcs'].first['VpcId'] if result['Vpcs']&.any?
end

vpc_id = get_vpc_id(vpc_name)

# =============================================================================
# CloudFormation Stacks
# =============================================================================

control 'cloudformation-stacks' do
  impact 1.0
  title 'CloudFormation Stacks Deployed Successfully'
  desc 'Verify that all required CloudFormation stacks are deployed and in a stable state'

  describe aws_cloudformation_stack(stack_name: 'GitHubRunnersVpc') do
    it { should exist }
    its('stack_status') { should match /COMPLETE$/ }
  end

  describe aws_cloudformation_stack(stack_name: 'GitHubRunnersWebhook') do
    it { should exist }
    its('stack_status') { should match /COMPLETE$/ }
  end
end

# =============================================================================
# VPC Resources
# =============================================================================

control 'vpc-infrastructure' do
  impact 1.0
  title 'VPC Infrastructure'
  desc 'Verify VPC exists with correct configuration'

  describe aws_vpc(vpc_id) do
    it { should exist }
    its('state') { should eq 'available' }
    its('cidr_block') { should eq vpc_cidr }
    its('is_default') { should be false }
  end
end

control 'vpc-subnets' do
  impact 1.0
  title 'VPC Subnets'
  desc 'Verify public subnets exist in ALL available availability zones'

  # Get all available AZs in the region
  az_result = json(command: "aws ec2 describe-availability-zones --filters Name=state,Values=available --output json")
  available_azs = az_result['AvailabilityZones'].map { |az| az['ZoneName'] }
  available_az_count = available_azs.length

  describe aws_subnets.where(vpc_id: vpc_id) do
    it { should exist }
    # Should have at least 2 subnets (multi-AZ)
    its('count') { should be >= 2 }
  end

  # CRITICAL: Verify we're using ALL available AZs in the region
  describe 'All Available Availability Zones' do
    it 'VPC subnets span all available AZs in the region' do
      # Collect AZs from individual subnets (aws_subnets doesn't have availability_zones method)
      subnet_azs = aws_subnets.where(vpc_id: vpc_id).subnet_ids.map do |subnet_id|
        aws_subnet(subnet_id).availability_zone
      end.uniq
      expect(subnet_azs.length).to eq(available_az_count),
        "Expected #{available_az_count} AZs (#{available_azs.join(', ')}) but found #{subnet_azs.length} (#{subnet_azs.join(', ')})"
    end
  end

  # Verify all subnets are available
  aws_subnets.where(vpc_id: vpc_id).subnet_ids.each do |subnet_id|
    describe aws_subnet(subnet_id) do
      it { should exist }
      its('available_ip_address_count') { should be > 0 }
    end
  end
end

control 'vpc-no-endpoints' do
  impact 1.0
  title 'No VPC Endpoints (Cost Optimization)'
  desc 'Verify NO VPC endpoints exist - we use public internet to save $86/month'

  describe aws_vpc_endpoints.where(vpc_id: vpc_id) do
    # Should have ZERO VPC endpoints for cost optimization
    its('count') { should eq 0 }
  end

  # Document cost savings
  describe 'Cost Optimization: VPC Endpoints' do
    it 'saves $86/month by using public internet instead of VPC endpoints' do
      # 6 interface endpoints @ $14.40/month each = $86.40/month
      # This test passing means we're saving that money!
      expect(aws_vpc_endpoints.where(vpc_id: vpc_id).count).to eq(0)
    end
  end
end

control 'vpc-no-nat-gateways' do
  impact 1.0
  title 'No NAT Gateways (Cost Optimization)'
  desc 'Verify NO NAT Gateways exist - we use public subnets to save $32/month'

  # Note: CINC doesn't have aws_nat_gateways resource, so we check via AWS CLI
  describe json(command: "aws ec2 describe-nat-gateways --filter Name=vpc-id,Values=#{vpc_id} Name=state,Values=available --output json") do
    its(['NatGateways', 'length']) { should eq 0 }
  end

  # Document cost savings
  describe 'Cost Optimization: NAT Gateways' do
    it 'saves $32/month by using public subnets instead of NAT Gateways' do
      result = json(command: "aws ec2 describe-nat-gateways --filter Name=vpc-id,Values=#{vpc_id} Name=state,Values=available --output json")
      expect(result['NatGateways'].length).to eq(0)
    end
  end
end

# =============================================================================
# ECS Resources
# =============================================================================

control 'ecs-cluster' do
  impact 1.0
  title 'ECS Cluster'
  desc 'Verify ECS cluster exists and is active'

  describe aws_ecs_cluster(cluster_name: cluster_name) do
    it { should exist }
    its('status') { should eq 'ACTIVE' }
    its('cluster_name') { should eq cluster_name }
  end
end

# Note: ECS task definitions are created dynamically by the Lambda webhook handler
# when processing GitHub webhook events. They won't exist immediately after deployment.

# =============================================================================
# Lambda Resources
# =============================================================================

control 'lambda-webhook-function' do
  impact 1.0
  title 'Lambda Webhook Function'
  desc 'Verify Lambda webhook handler exists and is properly configured'

  describe aws_lambda(lambda_name: lambda_name) do
    it { should exist }
    its('runtime') { should match /python3\./ }
    its('handler') { should match /lambda_handler/ }
    its('timeout') { should eq lambda_timeout }
    its('memory_size') { should eq lambda_memory }
  end
end

# =============================================================================
# API Gateway Resources
# =============================================================================

control 'api-gateway' do
  impact 1.0
  title 'API Gateway'
  desc 'Verify API Gateway exists and is configured'

  # Note: CINC AWS doesn't have aws_api_gateway_v2 resource yet
  # So we use AWS CLI directly
  describe json(command: "aws apigatewayv2 get-apis --output json") do
    # Find our API by name
    its(['Items']) { should_not be_empty }
  end

  describe 'API Gateway Configuration' do
    it 'has an HTTP API with the correct name' do
      result = json(command: "aws apigatewayv2 get-apis --output json")
      api = result['Items'].find { |a| a['Name'] == api_gateway_name }
      expect(api).not_to be_nil
      expect(api['ProtocolType']).to eq('HTTP')
    end
  end
end

# =============================================================================
# Security Groups
# =============================================================================

control 'security-groups' do
  impact 1.0
  title 'Security Groups'
  desc 'Verify security groups exist and have appropriate rules'

  describe aws_security_groups.where(vpc_id: vpc_id) do
    it { should exist }
    # Should have at least 2 SGs (default + runner SG)
    its('count') { should be >= 2 }
  end

  # Verify runner security group allows outbound traffic
  aws_security_groups.where(vpc_id: vpc_id).group_ids.each do |sg_id|
    describe aws_security_group(sg_id) do
      # Should allow outbound traffic (egress)
      its('outbound_rules.count') { should be > 0 }
    end
  end
end

