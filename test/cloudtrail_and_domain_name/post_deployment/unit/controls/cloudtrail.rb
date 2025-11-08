aws_account_id = input('aws_account_id', value: '781581267945')
aws_region = input('aws_region', value: 'us-east-1')

control 'cloudtrail-trail-exists' do
  impact 1.0
  title 'CloudTrail Trail Exists'
  desc 'Verify that a CloudTrail trail exists and is configured correctly'

  describe aws_cloudtrail_trails do
    it { should exist }
    its('trail_arns.count') { should be >= 1 }
  end
end

control 'cloudtrail-is-multi-region' do
  impact 1.0
  title 'CloudTrail Is Multi-Region'
  desc 'Verify that CloudTrail is configured as a multi-region trail'

  aws_cloudtrail_trails.trail_arns.each do |trail_arn|
    describe aws_cloudtrail_trail(trail_arn) do
      it { should be_multi_region_trail }
    end
  end
end

control 'cloudtrail-includes-global-events' do
  impact 1.0
  title 'CloudTrail Includes Global Service Events'
  desc 'Verify that CloudTrail is configured to include global service events'

  aws_cloudtrail_trails.trail_arns.each do |trail_arn|
    describe aws_cloudtrail_trail(trail_arn) do
      its('include_global_service_events') { should be true }
    end
  end
end

control 'cloudtrail-is-logging' do
  impact 1.0
  title 'CloudTrail Is Actively Logging'
  desc 'Verify that CloudTrail is actively logging events'

  aws_cloudtrail_trails.trail_arns.each do |trail_arn|
    describe aws_cloudtrail_trail(trail_arn) do
      it { should be_logging }
    end
  end
end

control 'cloudtrail-s3-bucket-exists' do
  impact 1.0
  title 'CloudTrail S3 Bucket Exists'
  desc 'Verify that CloudTrail S3 bucket exists'

  aws_cloudtrail_trails.trail_arns.each do |trail_arn|
    trail = aws_cloudtrail_trail(trail_arn)
    bucket_name = trail.s3_bucket_name

    describe aws_s3_bucket(bucket_name: bucket_name) do
      it { should exist }
    end
  end
end

control 'cloudtrail-s3-bucket-encrypted' do
  impact 1.0
  title 'CloudTrail S3 Bucket Is Encrypted'
  desc 'Verify that CloudTrail S3 bucket has encryption enabled'

  aws_cloudtrail_trails.trail_arns.each do |trail_arn|
    trail = aws_cloudtrail_trail(trail_arn)
    bucket_name = trail.s3_bucket_name

    describe aws_s3_bucket(bucket_name: bucket_name) do
      it { should have_default_encryption_enabled }
    end
  end
end

control 'cloudtrail-s3-bucket-not-public' do
  impact 1.0
  title 'CloudTrail S3 Bucket Is Not Public'
  desc 'Verify that CloudTrail S3 bucket blocks all public access'

  aws_cloudtrail_trails.trail_arns.each do |trail_arn|
    trail = aws_cloudtrail_trail(trail_arn)
    bucket_name = trail.s3_bucket_name

    describe aws_s3_bucket(bucket_name: bucket_name) do
      it { should have_access_logging_enabled }
    end
  end
end

control 'cloudtrail-logs-to-cloudwatch' do
  impact 1.0
  title 'CloudTrail Logs To CloudWatch'
  desc 'Verify that CloudTrail is configured to send logs to CloudWatch Logs'

  aws_cloudtrail_trails.trail_arns.each do |trail_arn|
    describe aws_cloudtrail_trail(trail_arn) do
      its('cloud_watch_logs_log_group_arn') { should_not be_nil }
    end
  end
end

control 'cloudtrail-log-group-exists' do
  impact 1.0
  title 'CloudWatch Logs Group For CloudTrail Exists'
  desc 'Verify that CloudWatch Logs log group for CloudTrail exists'

  aws_cloudtrail_trails.trail_arns.each do |trail_arn|
    trail = aws_cloudtrail_trail(trail_arn)
    log_group_arn = trail.cloud_watch_logs_log_group_arn

    if log_group_arn
      log_group_name = log_group_arn.split(':').last.gsub('log-group:', '').split(':').first

      describe aws_cloudwatch_log_group(log_group_name: log_group_name) do
        it { should exist }
      end
    end
  end
end

control 'cloudtrail-log-group-retention' do
  impact 1.0
  title 'CloudWatch Logs Group Has Proper Retention'
  desc 'Verify that CloudWatch Logs log group has 1-year retention configured'

  aws_cloudtrail_trails.trail_arns.each do |trail_arn|
    trail = aws_cloudtrail_trail(trail_arn)
    log_group_arn = trail.cloud_watch_logs_log_group_arn

    if log_group_arn
      log_group_name = log_group_arn.split(':').last.gsub('log-group:', '').split(':').first

      describe aws_cloudwatch_log_group(log_group_name: log_group_name) do
        its('retention_in_days') { should eq 365 }
      end
    end
  end
end
