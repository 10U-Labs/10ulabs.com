import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mockClient } from 'aws-sdk-client-mock';
import { ECSClient, DescribeTasksCommand } from '@aws-sdk/client-ecs';
import { EC2Client, DescribeInstancesCommand } from '@aws-sdk/client-ec2';
import { SSMClient, GetParameterCommand } from '@aws-sdk/client-ssm';

const ecsMock = mockClient(ECSClient);
const ec2Mock = mockClient(EC2Client);
const ssmMock = mockClient(SSMClient);

describe('spot_interruption_handler', () => {
  let handler;

  beforeEach(async () => {
    vi.resetModules();
    ecsMock.reset();
    ec2Mock.reset();
    ssmMock.reset();

    vi.stubEnv('ECS_CLUSTER', 'test-cluster');
    vi.stubEnv('GITHUB_TOKEN_SECRET_NAME', '/github/token');

    ssmMock.on(GetParameterCommand).resolves({
      Parameter: { Value: 'test-github-token' }
    });

    handler = await import('lambdas/spot_interruption_handler.js');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  describe('handler', () => {
    it('should ignore non-ECS and non-EC2 events', async () => {
      const event = {
        source: 'aws.lambda',
        'detail-type': 'Lambda Function State Change'
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(200);
      expect(result.body).toContain('Event ignored');
    });

    it('should ignore ECS events that are not task stopped', async () => {
      const event = {
        source: 'aws.ecs',
        'detail-type': 'ECS Task State Change',
        detail: {
          lastStatus: 'RUNNING'
        }
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(200);
      expect(result.body).toContain('Event ignored');
    });

    it('should handle ECS task stopped event without RunId tag', async () => {
      ecsMock.on(DescribeTasksCommand).resolves({
        tasks: [{
          taskArn: 'arn:aws:ecs:us-east-2:123456789012:task/test-cluster/abc123',
          tags: [
            { key: 'Name', value: 'test-runner' }
          ]
        }]
      });

      const event = {
        source: 'aws.ecs',
        'detail-type': 'ECS Task State Change',
        detail: {
          lastStatus: 'STOPPED',
          stopCode: 'SpotInterruption',
          stoppedReason: 'spot capacity reclaimed',
          taskArn: 'arn:aws:ecs:us-east-2:123456789012:task/test-cluster/abc123'
        }
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(200);
      expect(result.body).toContain('No run_id');
    });

    it('should skip ECS task stopped if not spot interruption', async () => {
      ecsMock.on(DescribeTasksCommand).resolves({
        tasks: [{
          taskArn: 'arn:aws:ecs:us-east-2:123456789012:task/test-cluster/abc123',
          tags: [
            { key: 'RunId', value: '12345' },
            { key: 'GitHubRepo', value: 'owner/repo' }
          ]
        }]
      });

      const event = {
        source: 'aws.ecs',
        'detail-type': 'ECS Task State Change',
        detail: {
          lastStatus: 'STOPPED',
          stopCode: 'UserInitiated',
          stoppedReason: 'User stopped task',
          taskArn: 'arn:aws:ecs:us-east-2:123456789012:task/test-cluster/abc123'
        }
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(200);
      expect(result.body).toContain('Not a spot interruption');
    });

    it('should handle EC2 spot interruption event without RunId tag', async () => {
      ec2Mock.on(DescribeInstancesCommand).resolves({
        Reservations: [{
          Instances: [{
            InstanceId: 'i-12345',
            Tags: [
              { Key: 'Name', Value: 'test-runner' }
            ]
          }]
        }]
      });

      const event = {
        source: 'aws.ec2',
        'detail-type': 'EC2 Spot Instance Interruption Warning',
        detail: {
          'instance-id': 'i-12345'
        }
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(200);
      expect(result.body).toContain('No run_id');
    });

    it('should return 500 when GitHub token unavailable for ECS spot interruption', async () => {
      vi.stubEnv('GITHUB_TOKEN_SECRET_NAME', '');
      vi.resetModules();
      ssmMock.reset();
      ecsMock.reset();

      ecsMock.on(DescribeTasksCommand).resolves({
        tasks: [{
          taskArn: 'arn:aws:ecs:us-east-2:123456789012:task/test-cluster/abc123',
          tags: [
            { key: 'RunId', value: '12345' },
            { key: 'GitHubRepo', value: 'owner/repo' }
          ]
        }]
      });

      handler = await import('lambdas/spot_interruption_handler.js');

      const event = {
        source: 'aws.ecs',
        'detail-type': 'ECS Task State Change',
        detail: {
          lastStatus: 'STOPPED',
          stopCode: 'SpotInterruption',
          stoppedReason: 'spot capacity reclaimed',
          taskArn: 'arn:aws:ecs:us-east-2:123456789012:task/test-cluster/abc123'
        }
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(500);
      expect(result.body).toContain('No GitHub token');
    });

    it('should return 500 when instance tags cannot be retrieved', async () => {
      ec2Mock.on(DescribeInstancesCommand).resolves({
        Reservations: []
      });

      const event = {
        source: 'aws.ec2',
        'detail-type': 'EC2 Spot Instance Interruption Warning',
        detail: {
          'instance-id': 'i-nonexistent'
        }
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(500);
      expect(result.body).toContain('Failed to get instance tags');
    });

    it('should handle missing instance-id in EC2 event', async () => {
      ec2Mock.on(DescribeInstancesCommand).resolves({
        Reservations: []
      });

      const event = {
        source: 'aws.ec2',
        'detail-type': 'EC2 Spot Instance Interruption Warning',
        detail: {}
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(500);
    });

    it('should handle ECS task tags retrieval error', async () => {
      ecsMock.on(DescribeTasksCommand).rejects(new Error('API Error'));

      const event = {
        source: 'aws.ecs',
        'detail-type': 'ECS Task State Change',
        detail: {
          lastStatus: 'STOPPED',
          stopCode: 'SpotInterruption',
          stoppedReason: 'capacity',
          taskArn: 'arn:aws:ecs:us-east-2:123456789012:task/test-cluster/abc123'
        }
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(200);
      expect(result.body).toContain('No run_id');
    });

    it('should handle EC2 describe instances API error', async () => {
      ec2Mock.on(DescribeInstancesCommand).rejects(new Error('API Error'));

      const event = {
        source: 'aws.ec2',
        'detail-type': 'EC2 Spot Instance Interruption Warning',
        detail: {
          'instance-id': 'i-12345'
        }
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(500);
    });
  });
});
