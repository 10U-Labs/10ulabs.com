domain_name = input('domain_name', value: '10ulabs.com')

control '10uf-org-hosted-zone-exists' do
  impact 1.0
  title '10ulabs.com Route53 Hosted Zone Exists'
  desc 'Verify that the Route53 hosted zone for 10ulabs.com exists'

  describe aws_hosted_zone(zone_name: "#{domain_name}.") do
    it { should exist }
  end
end

control '10uf-org-hosted-zone-name' do
  impact 1.0
  title '10ulabs.com Hosted Zone Has Correct Name'
  desc 'Verify that the hosted zone has the correct domain name'

  describe aws_hosted_zone(zone_name: "#{domain_name}.") do
    its('zone_name') { should eq "#{domain_name}." }
  end
end

control '10uf-org-hosted-zone-has-records' do
  impact 1.0
  title '10ulabs.com Hosted Zone Has DNS Records'
  desc 'Verify that the hosted zone has at least NS and SOA records'

  describe aws_hosted_zone(zone_name: "#{domain_name}.") do
    its('resource_record_set_count') { should be >= 2 }
  end
end

control '10uf-org-hosted-zone-nameservers' do
  impact 1.0
  title '10ulabs.com Hosted Zone Name Servers'
  desc 'Verify that the hosted zone has name servers configured'

  describe aws_hosted_zone(zone_name: "#{domain_name}.") do
    its('name_servers.count') { should be >= 4 }
  end
end
