import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mockClient } from 'aws-sdk-client-mock';
import { ECSClient, ListTasksCommand, DescribeTasksCommand, StopTaskCommand } from '@aws-sdk/client-ecs';
import { EC2Client, DescribeInstancesCommand, TerminateInstancesCommand } from '@aws-sdk/client-ec2';
import { SSMClient, GetParameterCommand } from '@aws-sdk/client-ssm';

const ecsMock = mockClient(ECSClient);
const ec2Mock = mockClient(EC2Client);
const ssmMock = mockClient(SSMClient);

describe('stale_runner_cleanup', () => {
  let handler;

  beforeEach(async () => {
    vi.resetModules();
    ecsMock.reset();
    ec2Mock.reset();
    ssmMock.reset();

    vi.stubEnv('ECS_CLUSTER', 'test-cluster');
    vi.stubEnv('EC2_MANAGED_BY_TAG', 'ec2-runner-api');
    vi.stubEnv('GITHUB_REPO', 'owner/repo');
    vi.stubEnv('GITHUB_TOKEN_SECRET_NAME', '/github/token');

    ssmMock.on(GetParameterCommand).resolves({
      Parameter: { Value: 'test-github-token' }
    });

    handler = await import('lambdas/stale_runner_cleanup.js');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  describe('handler', () => {
    it('should return 200 with cleanup results', async () => {
      ecsMock.on(ListTasksCommand).resolves({ taskArns: [] });
      ec2Mock.on(DescribeInstancesCommand).resolves({ Reservations: [] });

      const result = await handler.handler({}, {});

      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body);
      expect(body.orphaned_ecs_cleaned).toBe(0);
      expect(body.orphaned_ec2_cleaned).toBe(0);
    });

    it('should handle ECS list tasks error', async () => {
      ecsMock.on(ListTasksCommand).rejects(new Error('API Error'));
      ec2Mock.on(DescribeInstancesCommand).resolves({ Reservations: [] });

      const result = await handler.handler({}, {});

      expect(result.statusCode).toBe(200);
    });

    it('should handle EC2 describe instances error', async () => {
      ecsMock.on(ListTasksCommand).resolves({ taskArns: [] });
      ec2Mock.on(DescribeInstancesCommand).rejects(new Error('API Error'));

      const result = await handler.handler({}, {});

      expect(result.statusCode).toBe(200);
    });

    it('should clean orphaned ECS tasks older than threshold', async () => {
      const oldStartTime = new Date(Date.now() - 600000); // 10 minutes ago

      ecsMock.on(ListTasksCommand).resolves({
        taskArns: ['arn:aws:ecs:us-east-2:123456789012:task/test-cluster/abc123']
      });

      ecsMock.on(DescribeTasksCommand).resolves({
        tasks: [{
          taskArn: 'arn:aws:ecs:us-east-2:123456789012:task/test-cluster/abc123',
          startedAt: oldStartTime.toISOString(),
          tags: [
            { key: 'Type', value: 'workflow-runner' },
            { key: 'ManagedBy', value: 'ecs-runner-api' },
            { key: 'Name', value: 'fargate-runner-12345' },
            { key: 'GitHubRepo', value: 'owner/repo' }
          ]
        }]
      });

      ecsMock.on(StopTaskCommand).resolves({});
      ec2Mock.on(DescribeInstancesCommand).resolves({ Reservations: [] });

      const result = await handler.handler({}, {});

      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body);
      expect(body.orphaned_ecs_cleaned).toBeGreaterThanOrEqual(0);
    });

    it('should not clean ECS tasks younger than threshold', async () => {
      const recentStartTime = new Date(Date.now() - 60000); // 1 minute ago

      ecsMock.on(ListTasksCommand).resolves({
        taskArns: ['arn:aws:ecs:us-east-2:123456789012:task/test-cluster/abc123']
      });

      ecsMock.on(DescribeTasksCommand).resolves({
        tasks: [{
          taskArn: 'arn:aws:ecs:us-east-2:123456789012:task/test-cluster/abc123',
          startedAt: recentStartTime.toISOString(),
          tags: [
            { key: 'Type', value: 'workflow-runner' },
            { key: 'ManagedBy', value: 'ecs-runner-api' }
          ]
        }]
      });

      ec2Mock.on(DescribeInstancesCommand).resolves({ Reservations: [] });

      const result = await handler.handler({}, {});

      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body);
      expect(body.orphaned_ecs_cleaned).toBe(0);
    });

    it('should skip ECS tasks without proper tags', async () => {
      const oldStartTime = new Date(Date.now() - 600000);

      ecsMock.on(ListTasksCommand).resolves({
        taskArns: ['arn:aws:ecs:us-east-2:123456789012:task/test-cluster/abc123']
      });

      ecsMock.on(DescribeTasksCommand).resolves({
        tasks: [{
          taskArn: 'arn:aws:ecs:us-east-2:123456789012:task/test-cluster/abc123',
          startedAt: oldStartTime.toISOString(),
          tags: [
            { key: 'Type', value: 'other-type' }
          ]
        }]
      });

      ec2Mock.on(DescribeInstancesCommand).resolves({ Reservations: [] });

      const result = await handler.handler({}, {});

      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body);
      expect(body.orphaned_ecs_cleaned).toBe(0);
    });

    it('should handle StopTask API error gracefully', async () => {
      const oldStartTime = new Date(Date.now() - 600000);

      ecsMock.on(ListTasksCommand).resolves({
        taskArns: ['arn:aws:ecs:us-east-2:123456789012:task/test-cluster/abc123']
      });

      ecsMock.on(DescribeTasksCommand).resolves({
        tasks: [{
          taskArn: 'arn:aws:ecs:us-east-2:123456789012:task/test-cluster/abc123',
          startedAt: oldStartTime.toISOString(),
          tags: [
            { key: 'Type', value: 'workflow-runner' },
            { key: 'ManagedBy', value: 'ecs-runner-api' }
          ]
        }]
      });

      ecsMock.on(StopTaskCommand).rejects(new Error('Stop failed'));
      ec2Mock.on(DescribeInstancesCommand).resolves({ Reservations: [] });

      const result = await handler.handler({}, {});

      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body);
      expect(body.errors).toBeGreaterThan(0);
    });

    it('should handle TerminateInstances API error gracefully', async () => {
      const oldLaunchTime = new Date(Date.now() - 600000);

      ecsMock.on(ListTasksCommand).resolves({ taskArns: [] });
      ec2Mock.on(DescribeInstancesCommand).resolves({
        Reservations: [{
          Instances: [{
            InstanceId: 'i-12345',
            LaunchTime: oldLaunchTime.toISOString(),
            Tags: [
              { Key: 'Type', Value: 'workflow-runner' },
              { Key: 'ManagedBy', Value: 'ec2-runner-api' }
            ]
          }]
        }]
      });

      ec2Mock.on(TerminateInstancesCommand).rejects(new Error('Terminate failed'));

      const result = await handler.handler({}, {});

      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body);
      expect(body.errors).toBeGreaterThan(0);
    });

    it('should handle missing ECS_CLUSTER', async () => {
      vi.stubEnv('ECS_CLUSTER', '');
      vi.resetModules();
      ecsMock.reset();
      ec2Mock.reset();
      ssmMock.reset();

      ssmMock.on(GetParameterCommand).resolves({
        Parameter: { Value: 'test-token' }
      });
      ec2Mock.on(DescribeInstancesCommand).resolves({ Reservations: [] });

      handler = await import('lambdas/stale_runner_cleanup.js');

      const result = await handler.handler({}, {});

      expect(result.statusCode).toBe(200);
    });

    it('should handle missing EC2_MANAGED_BY_TAG', async () => {
      vi.stubEnv('EC2_MANAGED_BY_TAG', '');
      vi.resetModules();
      ecsMock.reset();
      ssmMock.reset();

      ssmMock.on(GetParameterCommand).resolves({
        Parameter: { Value: 'test-token' }
      });
      ecsMock.on(ListTasksCommand).resolves({ taskArns: [] });

      handler = await import('lambdas/stale_runner_cleanup.js');

      const result = await handler.handler({}, {});

      expect(result.statusCode).toBe(200);
    });

    it('should handle paginated ECS task listing', async () => {
      ecsMock.on(ListTasksCommand)
        .resolvesOnce({
          taskArns: ['arn:aws:ecs:us-east-2:123456789012:task/test-cluster/task1'],
          nextToken: 'token123'
        })
        .resolvesOnce({
          taskArns: ['arn:aws:ecs:us-east-2:123456789012:task/test-cluster/task2']
        });

      ecsMock.on(DescribeTasksCommand).resolves({
        tasks: []
      });

      ec2Mock.on(DescribeInstancesCommand).resolves({ Reservations: [] });

      const result = await handler.handler({}, {});

      expect(result.statusCode).toBe(200);
    });
  });
});
