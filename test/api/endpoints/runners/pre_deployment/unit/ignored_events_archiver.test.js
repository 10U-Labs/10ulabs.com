import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { mockClient } from 'aws-sdk-client-mock';
import { S3Client, PutObjectCommand } from '@aws-sdk/client-s3';
import { CloudWatchClient, PutMetricDataCommand } from '@aws-sdk/client-cloudwatch';

const s3Mock = mockClient(S3Client);
const cloudwatchMock = mockClient(CloudWatchClient);

describe('ignored_events_archiver', () => {
  let handler;

  beforeEach(async () => {
    vi.resetModules();
    s3Mock.reset();
    cloudwatchMock.reset();

    vi.stubEnv('ARCHIVE_BUCKET_NAME', 'test-archive-bucket');

    s3Mock.on(PutObjectCommand).resolves({});
    cloudwatchMock.on(PutMetricDataCommand).resolves({});

    handler = await import('../../../../src/api/endpoints/runners/lambdas/ignored_events_archiver.js');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
    vi.clearAllMocks();
  });

  describe('buildS3Key', () => {
    it('should build correct S3 key with date partitioning', () => {
      const timestamp = '2025-03-15T14:30:00.000Z';
      const messageId = 'msg-12345';

      const key = handler.buildS3Key(timestamp, messageId);

      expect(key).toBe('ignored-events/2025/03/15/14/msg-12345.json');
    });

    it('should pad single digit months and days', () => {
      const timestamp = '2025-01-05T09:15:00.000Z';
      const messageId = 'msg-67890';

      const key = handler.buildS3Key(timestamp, messageId);

      expect(key).toBe('ignored-events/2025/01/05/09/msg-67890.json');
    });
  });

  describe('archiveEvent', () => {
    it('should archive event to S3 successfully', async () => {
      const record = {
        messageId: 'test-message-id',
        body: JSON.stringify({
          timestamp: '2025-03-15T14:30:00.000Z',
          event_data: { action: 'ping' },
          reason: 'Event type not handled'
        }),
        attributes: { ApproximateReceiveCount: '1' }
      };

      const result = await handler.archiveEvent(record);

      expect(result.success).toBe(true);
      expect(result.key).toContain('ignored-events/2025/03/15/14/test-message-id.json');
    });

    it('should fail when ARCHIVE_BUCKET_NAME is not set', async () => {
      vi.stubEnv('ARCHIVE_BUCKET_NAME', '');
      vi.resetModules();
      const freshHandler = await import('../../../../src/api/endpoints/runners/lambdas/ignored_events_archiver.js');

      const record = {
        messageId: 'test-message-id',
        body: JSON.stringify({ timestamp: '2025-03-15T14:30:00.000Z' })
      };

      const result = await freshHandler.archiveEvent(record);

      expect(result.success).toBe(false);
      expect(result.error).toContain('Archive bucket not configured');
    });

    it('should handle S3 put errors', async () => {
      s3Mock.on(PutObjectCommand).rejects(new Error('S3 access denied'));

      const record = {
        messageId: 'test-message-id',
        body: JSON.stringify({
          timestamp: '2025-03-15T14:30:00.000Z',
          event_data: { action: 'ping' }
        })
      };

      const result = await handler.archiveEvent(record);

      expect(result.success).toBe(false);
      expect(result.error).toContain('S3 access denied');
    });

    it('should use current timestamp when event has no timestamp', async () => {
      const record = {
        messageId: 'test-message-id',
        body: JSON.stringify({
          event_data: { action: 'ping' },
          reason: 'Event type not handled'
        })
      };

      const result = await handler.archiveEvent(record);

      expect(result.success).toBe(true);
      expect(result.key).toContain('ignored-events/');
      expect(result.key).toContain('test-message-id.json');
    });
  });

  describe('handler', () => {
    it('should return success for empty event', async () => {
      const event = { Records: [] };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body);
      expect(body.message).toBe('No records to process');
    });

    it('should archive multiple events successfully', async () => {
      const event = {
        Records: [
          {
            messageId: 'msg-1',
            body: JSON.stringify({
              timestamp: '2025-03-15T14:30:00.000Z',
              event_data: { action: 'ping' },
              reason: 'ping event'
            })
          },
          {
            messageId: 'msg-2',
            body: JSON.stringify({
              timestamp: '2025-03-15T14:31:00.000Z',
              event_data: { action: 'push' },
              reason: 'push event not handled'
            })
          }
        ]
      };

      const result = await handler.handler(event, {});

      expect(result.statusCode).toBe(200);
      const body = JSON.parse(result.body);
      expect(body.message).toBe('Archived');
      expect(body.count).toBe(2);
      expect(body.success).toBe(2);
      expect(body.failed).toBe(0);
    });

    it('should throw error when some events fail to archive', async () => {
      s3Mock.on(PutObjectCommand)
        .resolvesOnce({})
        .rejectsOnce(new Error('S3 error'));

      const event = {
        Records: [
          {
            messageId: 'msg-1',
            body: JSON.stringify({ timestamp: '2025-03-15T14:30:00.000Z' })
          },
          {
            messageId: 'msg-2',
            body: JSON.stringify({ timestamp: '2025-03-15T14:31:00.000Z' })
          }
        ]
      };

      await expect(handler.handler(event, {})).rejects.toThrow('1 event(s) failed to archive');
    });
  });
});
