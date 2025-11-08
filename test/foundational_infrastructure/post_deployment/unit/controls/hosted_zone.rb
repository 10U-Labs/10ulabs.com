# Test that 10ulabs.com hosted zone exists and is configured correctly

domain_name = input('domain_name', value: '10ulabs.com')

control '10uf-org-hosted-zone' do
  impact 1.0
  title '10ulabs.com Route53 Hosted Zone'
  desc 'Verify that the Route53 hosted zone for 10ulabs.com exists'

  describe aws_route53_hosted_zone(zone_name: "#{domain_name}.") do
    it { should exist }
    its('name') { should eq "#{domain_name}." }
    its('resource_record_set_count') { should be >= 2 }  # At least NS and SOA records
  end
end

control '10uf-org-hosted-zone-nameservers' do
  impact 1.0
  title '10ulabs.com Hosted Zone Name Servers'
  desc 'Verify that the hosted zone has name servers configured'

  describe aws_route53_hosted_zone(zone_name: "#{domain_name}.") do
    it { should exist }
    its('name_servers.count') { should be >= 4 }  # AWS provides 4 name servers
  end
end
