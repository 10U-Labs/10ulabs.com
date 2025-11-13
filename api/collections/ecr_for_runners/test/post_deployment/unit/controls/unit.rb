vpc_name = input('vpc_name')
vpc_cidr = input('vpc_cidr')
cluster_name = input('cluster_name')
lambda_name = input('lambda_name')
lambda_timeout = input('lambda_timeout')
lambda_memory = input('lambda_memory')
api_gateway_name = input('api_gateway_name')

def get_vpc_id(vpc_name)
  result = json(command: "aws ec2 describe-vpcs --filters Name=tag:Name,Values=#{vpc_name} --output json")
  result['Vpcs'].first['VpcId'] if result['Vpcs']&.any?
end

vpc_id = get_vpc_id(vpc_name)

control 'cloudformation-vpc-stack' do
  impact 1.0
  title 'CloudFormation VPC Stack Deployed Successfully'
  desc 'Verify that VPC stack is deployed and in a stable state'

  describe aws_cloudformation_stack(stack_name: 'GitHubRunnersVpc') do
    it { should exist }
    its('stack_status') { should match /COMPLETE$/ }
  end
end

control 'cloudformation-webhook-stack' do
  impact 1.0
  title 'CloudFormation Webhook Stack Deployed Successfully'
  desc 'Verify that webhook stack is deployed and in a stable state'

  describe aws_cloudformation_stack(stack_name: 'GitHubRunnersWebhook') do
    it { should exist }
    its('stack_status') { should match /COMPLETE$/ }
  end
end

control 'vpc-exists' do
  impact 1.0
  title 'VPC Exists'
  desc 'Verify VPC exists'

  describe aws_vpc(vpc_id) do
    it { should exist }
  end
end

control 'vpc-is-available' do
  impact 1.0
  title 'VPC Is Available'
  desc 'Verify VPC state is available'

  describe aws_vpc(vpc_id) do
    its('state') { should eq 'available' }
  end
end

control 'vpc-has-correct-cidr' do
  impact 1.0
  title 'VPC Has Correct CIDR Block'
  desc 'Verify VPC CIDR block matches configuration'

  describe aws_vpc(vpc_id) do
    its('cidr_block') { should eq vpc_cidr }
  end
end

control 'vpc-is-not-default' do
  impact 1.0
  title 'VPC Is Not Default VPC'
  desc 'Verify this is not the default VPC'

  describe aws_vpc(vpc_id) do
    its('is_default') { should be false }
  end
end

control 'vpc-subnets-exist' do
  impact 1.0
  title 'VPC Subnets Exist'
  desc 'Verify public subnets exist'

  describe aws_subnets.where(vpc_id: vpc_id) do
    it { should exist }
  end
end

control 'vpc-has-multi-az-subnets' do
  impact 1.0
  title 'VPC Has Multi-AZ Subnets'
  desc 'Verify at least 2 subnets exist for high availability'

  describe aws_subnets.where(vpc_id: vpc_id) do
    its('count') { should be >= 2 }
  end
end

control 'vpc-uses-all-availability-zones' do
  impact 1.0
  title 'VPC Uses All Available Availability Zones'
  desc 'Verify VPC subnets span all available AZs in the region for maximum resilience'

  az_result = json(command: "aws ec2 describe-availability-zones --filters Name=state,Values=available --output json")
  available_azs = az_result['AvailabilityZones'].map { |az| az['ZoneName'] }
  available_az_count = available_azs.length

  describe 'All Available Availability Zones' do
    it 'VPC subnets span all available AZs in the region' do
      subnet_azs = aws_subnets.where(vpc_id: vpc_id).subnet_ids.map do |subnet_id|
        aws_subnet(subnet_id).availability_zone
      end.uniq
      expect(subnet_azs.length).to eq(available_az_count),
        "Expected #{available_az_count} AZs (#{available_azs.join(', ')}) but found #{subnet_azs.length} (#{subnet_azs.join(', ')})"
    end
  end
end

control 'vpc-subnets-have-available-ips' do
  impact 1.0
  title 'VPC Subnets Have Available IP Addresses'
  desc 'Verify all subnets have available IP addresses'

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
    its('count') { should eq 0 }
  end
end

control 'vpc-no-nat-gateways' do
  impact 1.0
  title 'No NAT Gateways (Cost Optimization)'
  desc 'Verify NO NAT Gateways exist - we use public subnets to save $32/month'

  describe json(command: "aws ec2 describe-nat-gateways --filter Name=vpc-id,Values=#{vpc_id} Name=state,Values=available --output json") do
    its(['NatGateways', 'length']) { should eq 0 }
  end
end

control 'ecs-cluster-exists' do
  impact 1.0
  title 'ECS Cluster Exists'
  desc 'Verify ECS cluster exists'

  describe aws_ecs_cluster(cluster_name: cluster_name) do
    it { should exist }
  end
end

control 'ecs-cluster-is-active' do
  impact 1.0
  title 'ECS Cluster Is Active'
  desc 'Verify ECS cluster is in active state'

  describe aws_ecs_cluster(cluster_name: cluster_name) do
    its('status') { should eq 'ACTIVE' }
  end
end

control 'ecs-cluster-has-correct-name' do
  impact 1.0
  title 'ECS Cluster Has Correct Name'
  desc 'Verify ECS cluster name matches configuration'

  describe aws_ecs_cluster(cluster_name: cluster_name) do
    its('cluster_name') { should eq cluster_name }
  end
end

control 'lambda-webhook-function-exists' do
  impact 1.0
  title 'Lambda Webhook Function Exists'
  desc 'Verify Lambda webhook handler exists'

  describe aws_lambda(lambda_name: lambda_name) do
    it { should exist }
  end
end

control 'lambda-webhook-function-uses-python' do
  impact 1.0
  title 'Lambda Uses Python Runtime'
  desc 'Verify Lambda uses Python 3.x runtime'

  describe aws_lambda(lambda_name: lambda_name) do
    its('runtime') { should match /python3\./ }
  end
end

control 'lambda-webhook-function-has-correct-handler' do
  impact 1.0
  title 'Lambda Has Correct Handler'
  desc 'Verify Lambda handler is configured correctly'

  describe aws_lambda(lambda_name: lambda_name) do
    its('handler') { should match /lambda_handler/ }
  end
end

control 'lambda-webhook-function-has-correct-timeout' do
  impact 1.0
  title 'Lambda Has Correct Timeout'
  desc 'Verify Lambda timeout matches configuration'

  describe aws_lambda(lambda_name: lambda_name) do
    its('timeout') { should eq lambda_timeout }
  end
end

control 'lambda-webhook-function-has-correct-memory' do
  impact 1.0
  title 'Lambda Has Correct Memory Size'
  desc 'Verify Lambda memory size matches configuration'

  describe aws_lambda(lambda_name: lambda_name) do
    its('memory_size') { should eq lambda_memory }
  end
end

control 'api-gateway-exists' do
  impact 1.0
  title 'API Gateway Exists'
  desc 'Verify API Gateway HTTP API exists with correct name'

  describe 'API Gateway Configuration' do
    it 'has an HTTP API with the correct name' do
      result = json(command: "aws apigatewayv2 get-apis --output json")
      api = result['Items'].find { |a| a['Name'] == api_gateway_name }
      expect(api).not_to be_nil
    end
  end
end

control 'api-gateway-uses-http-protocol' do
  impact 1.0
  title 'API Gateway Uses HTTP Protocol'
  desc 'Verify API Gateway uses HTTP protocol type'

  describe 'API Gateway Protocol' do
    it 'uses HTTP protocol type' do
      result = json(command: "aws apigatewayv2 get-apis --output json")
      api = result['Items'].find { |a| a['Name'] == api_gateway_name }
      expect(api['ProtocolType']).to eq('HTTP')
    end
  end
end

control 'security-groups-exist' do
  impact 1.0
  title 'Security Groups Exist'
  desc 'Verify security groups exist in VPC'

  describe aws_security_groups.where(vpc_id: vpc_id) do
    it { should exist }
  end
end

control 'security-groups-count' do
  impact 1.0
  title 'Security Groups Count'
  desc 'Verify at least 2 security groups exist (default + runner)'

  describe aws_security_groups.where(vpc_id: vpc_id) do
    its('count') { should be >= 2 }
  end
end

control 'security-groups-allow-outbound' do
  impact 1.0
  title 'Security Groups Allow Outbound Traffic'
  desc 'Verify security groups have outbound rules configured'

  aws_security_groups.where(vpc_id: vpc_id).group_ids.each do |sg_id|
    describe aws_security_group(sg_id) do
      its('outbound_rules.count') { should be > 0 }
    end
  end
end
