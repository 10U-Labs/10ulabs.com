import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mockClient } from 'aws-sdk-client-mock';
import { SSMClient, GetParameterCommand } from '@aws-sdk/client-ssm';
import { SNSClient, PublishCommand } from '@aws-sdk/client-sns';
import { EC2Client, DescribeSubnetsCommand, DescribeSecurityGroupsCommand } from '@aws-sdk/client-ec2';

const ssmMock = mockClient(SSMClient);
const snsMock = mockClient(SNSClient);
const ec2Mock = mockClient(EC2Client);

describe('drift_recovery', () => {
  let driftRecovery;

  beforeEach(async () => {
    vi.resetModules();
    ssmMock.reset();
    snsMock.reset();
    ec2Mock.reset();

    vi.stubEnv('MANAGED_VPC_ID', 'vpc-123456');
    vi.stubEnv('GITHUB_TOKEN_PARAMETER_NAME', '/github/token');
    vi.stubEnv('GITHUB_REPO', 'owner/repo');
    vi.stubEnv('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-2:123456789012:alerts');

    ssmMock.on(GetParameterCommand).resolves({
      Parameter: { Value: 'test-github-token' }
    });
    snsMock.on(PublishCommand).resolves({});

    driftRecovery = await import('lambdas/drift_recovery.js');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  describe('handler - VPC checks', () => {
    it('should skip VPC resource not matching managed VPC', async () => {
      const sqsEvent = {
        Records: [{
          body: JSON.stringify({
            configRuleName: 'vpc-rule',
            resourceType: 'AWS::EC2::VPC',
            resourceId: 'vpc-different',
            awsRegion: 'us-east-2'
          })
        }]
      };

      const result = await driftRecovery.handler(sqsEvent, {});

      expect(result.statusCode).toBe(200);
      expect(result.body).toContain('not in managed VPC');
    });

    it('should skip subnet not in managed VPC', async () => {
      ec2Mock.on(DescribeSubnetsCommand).resolves({
        Subnets: [{ VpcId: 'vpc-different' }]
      });

      const sqsEvent = {
        Records: [{
          body: JSON.stringify({
            configRuleName: 'subnet-rule',
            resourceType: 'AWS::EC2::Subnet',
            resourceId: 'subnet-123',
            awsRegion: 'us-east-2'
          })
        }]
      };

      const result = await driftRecovery.handler(sqsEvent, {});

      expect(result.statusCode).toBe(200);
      expect(result.body).toContain('not in managed VPC');
    });

    it('should skip default security group', async () => {
      ec2Mock.on(DescribeSecurityGroupsCommand).resolves({
        SecurityGroups: [{
          VpcId: 'vpc-123456',
          GroupName: 'default'
        }]
      });

      const sqsEvent = {
        Records: [{
          body: JSON.stringify({
            configRuleName: 'sg-rule',
            resourceType: 'AWS::EC2::SecurityGroup',
            resourceId: 'sg-123',
            awsRegion: 'us-east-2'
          })
        }]
      };

      const result = await driftRecovery.handler(sqsEvent, {});

      expect(result.statusCode).toBe(200);
      expect(result.body).toContain('not in managed VPC');
    });

    it('should skip security group not in managed VPC', async () => {
      ec2Mock.on(DescribeSecurityGroupsCommand).resolves({
        SecurityGroups: [{
          VpcId: 'vpc-other',
          GroupName: 'my-sg'
        }]
      });

      const sqsEvent = {
        Records: [{
          body: JSON.stringify({
            configRuleName: 'sg-rule',
            resourceType: 'AWS::EC2::SecurityGroup',
            resourceId: 'sg-456',
            awsRegion: 'us-east-2'
          })
        }]
      };

      const result = await driftRecovery.handler(sqsEvent, {});

      expect(result.statusCode).toBe(200);
      expect(result.body).toContain('not in managed VPC');
    });
  });

  describe('handler - GitHub token', () => {
    it('should return 500 when GitHub token unavailable', async () => {
      vi.stubEnv('GITHUB_TOKEN_PARAMETER_NAME', '');
      vi.resetModules();
      driftRecovery = await import('lambdas/drift_recovery.js');

      const sqsEvent = {
        Records: [{
          body: JSON.stringify({
            configRuleName: 'vpc-rule',
            resourceType: 'AWS::EC2::VPC',
            resourceId: 'vpc-123456',
            awsRegion: 'us-east-2'
          })
        }]
      };

      const result = await driftRecovery.handler(sqsEvent, {});

      expect(result.statusCode).toBe(500);
      expect(result.body).toContain('Failed to retrieve GitHub token');
    });

    it('should retrieve token from SSM for valid parameter', async () => {
      const sqsEvent = {
        Records: [{
          body: JSON.stringify({
            configRuleName: 'vpc-rule',
            resourceType: 'AWS::EC2::VPC',
            resourceId: 'vpc-123456',
            awsRegion: 'us-east-2'
          })
        }]
      };

      await driftRecovery.handler(sqsEvent, {});

      const ssmCalls = ssmMock.calls();
      expect(ssmCalls.length).toBeGreaterThan(0);
      expect(ssmCalls[0].args[0].input).toEqual({
        Name: '/github/token',
        WithDecryption: true
      });
    });
  });

  describe('handler - event parsing', () => {
    it('should handle empty Records array', async () => {
      vi.stubEnv('GITHUB_TOKEN_PARAMETER_NAME', '');
      vi.resetModules();
      driftRecovery = await import('lambdas/drift_recovery.js');

      const sqsEvent = { Records: [] };

      const result = await driftRecovery.handler(sqsEvent, {});

      expect(result.statusCode).toBeDefined();
    });

    it('should parse drift details from SQS message', async () => {
      const sqsEvent = {
        Records: [{
          body: JSON.stringify({
            configRuleName: 'test-rule-name',
            resourceType: 'AWS::EC2::VPC',
            resourceId: 'vpc-different',
            awsRegion: 'us-west-2'
          })
        }]
      };

      const result = await driftRecovery.handler(sqsEvent, {});

      expect(result.body).toContain('not in managed VPC');
    });

    it('should handle direct event without SQS wrapping', async () => {
      const directEvent = {
        configRuleName: 'test-rule',
        resourceType: 'AWS::EC2::VPC',
        resourceId: 'vpc-different',
        awsRegion: 'us-east-2'
      };

      const result = await driftRecovery.handler(directEvent, {});

      expect(result.statusCode).toBe(200);
      expect(result.body).toContain('not in managed VPC');
    });
  });

  describe('handler - notifications', () => {
    it('should send SNS notification on failure', async () => {
      vi.stubEnv('GITHUB_TOKEN_PARAMETER_NAME', '');
      vi.resetModules();
      snsMock.reset();
      snsMock.on(PublishCommand).resolves({});
      driftRecovery = await import('lambdas/drift_recovery.js');

      const sqsEvent = {
        Records: [{
          body: JSON.stringify({
            configRuleName: 'vpc-rule',
            resourceType: 'AWS::EC2::VPC',
            resourceId: 'vpc-123456',
            awsRegion: 'us-east-2'
          })
        }]
      };

      await driftRecovery.handler(sqsEvent, {});

      const snsCalls = snsMock.calls();
      expect(snsCalls.length).toBeGreaterThan(0);
    });

    it('should handle missing SNS topic ARN gracefully', async () => {
      vi.stubEnv('SNS_TOPIC_ARN', '');
      vi.stubEnv('GITHUB_TOKEN_PARAMETER_NAME', '');
      vi.resetModules();
      driftRecovery = await import('lambdas/drift_recovery.js');

      const sqsEvent = {
        Records: [{
          body: JSON.stringify({
            configRuleName: 'test-rule',
            resourceType: 'AWS::EC2::VPC',
            resourceId: 'vpc-123456',
            awsRegion: 'us-east-2'
          })
        }]
      };

      const result = await driftRecovery.handler(sqsEvent, {});

      expect(result.statusCode).toBe(500);
    });
  });

  describe('handler - EC2 API error handling', () => {
    it('should handle EC2 API error for subnet check', async () => {
      ec2Mock.on(DescribeSubnetsCommand).rejects(new Error('API Error'));

      const sqsEvent = {
        Records: [{
          body: JSON.stringify({
            configRuleName: 'subnet-rule',
            resourceType: 'AWS::EC2::Subnet',
            resourceId: 'subnet-123',
            awsRegion: 'us-east-2'
          })
        }]
      };

      const result = await driftRecovery.handler(sqsEvent, {});

      expect(result.statusCode).toBe(200);
      expect(result.body).toContain('not in managed VPC');
    });

    it('should handle EC2 API error for security group check', async () => {
      ec2Mock.on(DescribeSecurityGroupsCommand).rejects(new Error('API Error'));

      const sqsEvent = {
        Records: [{
          body: JSON.stringify({
            configRuleName: 'sg-rule',
            resourceType: 'AWS::EC2::SecurityGroup',
            resourceId: 'sg-123',
            awsRegion: 'us-east-2'
          })
        }]
      };

      const result = await driftRecovery.handler(sqsEvent, {});

      expect(result.statusCode).toBe(200);
      expect(result.body).toContain('not in managed VPC');
    });
  });
});
