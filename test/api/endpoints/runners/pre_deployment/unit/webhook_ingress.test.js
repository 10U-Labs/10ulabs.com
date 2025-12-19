import { describe, it, expect, vi, beforeEach } from 'vitest';

describe('webhook_ingress', () => {
  let webhookIngress;

  beforeEach(async () => {
    vi.resetModules();
    webhookIngress = await import('common/webhook_ingress.js');
  });

  describe('getMessageAttribute', () => {
    it('should return attribute value when present', () => {
      const record = {
        messageAttributes: {
          'x-github-event': { stringValue: 'workflow_job' }
        }
      };
      expect(webhookIngress.getMessageAttribute(record, 'x-github-event')).toBe('workflow_job');
    });

    it('should return null when attribute is missing', () => {
      const record = {
        messageAttributes: {}
      };
      expect(webhookIngress.getMessageAttribute(record, 'x-github-event')).toBeNull();
    });

    it('should return null when messageAttributes is missing', () => {
      const record = {};
      expect(webhookIngress.getMessageAttribute(record, 'x-github-event')).toBeNull();
    });

    it('should return null when stringValue is missing', () => {
      const record = {
        messageAttributes: {
          'x-github-event': { dataType: 'String' }
        }
      };
      expect(webhookIngress.getMessageAttribute(record, 'x-github-event')).toBeNull();
    });
  });

  describe('isWebhookIngressQueue', () => {
    it('should return true for ingress queue ARN', () => {
      const arn = 'arn:aws:sqs:us-east-2:123456789012:RunnersWebhookIngress';
      expect(webhookIngress.isWebhookIngressQueue(arn)).toBe(true);
    });

    it('should return false for job queue ARN', () => {
      const arn = 'arn:aws:sqs:us-east-2:123456789012:RunnersJobQueue';
      expect(webhookIngress.isWebhookIngressQueue(arn)).toBe(false);
    });

    it('should be case sensitive', () => {
      const arn = 'arn:aws:sqs:us-east-2:123456789012:RunnersWebhookingress';
      expect(webhookIngress.isWebhookIngressQueue(arn)).toBe(false);
    });
  });

  describe('IngressHandler', () => {
    let mockDeps;
    let handler;

    beforeEach(() => {
      mockDeps = {
        getWebhookSecret: vi.fn(() => 'test-webhook-secret'),
        verifySignature: vi.fn(() => true),
        publishMetric: vi.fn(),
        enqueueIgnored: vi.fn(),
        enqueueJob: vi.fn(() => ({ success: true })),
        enqueueCancellation: vi.fn(() => ({ success: true })),
        getRunnerType: vi.fn(() => ['ecs']),
        checkIdempotency: vi.fn(() => false)
      };
      handler = new webhookIngress.IngressHandler(mockDeps);
    });

    describe('getDeps', () => {
      it('should return the injected dependencies', () => {
        expect(handler.getDeps()).toBe(mockDeps);
      });
    });

    describe('handle - signature verification', () => {
      it('should continue processing when signature is missing (logs warning only)', async () => {
        const record = {
          body: '{"action": "in_progress"}',
          messageAttributes: {
            'x-github-event': { stringValue: 'workflow_job' },
            'x-github-delivery': { stringValue: 'delivery-123' }
          }
        };

        const result = await handler.handle(record);

        expect(result).toEqual({ success: true, routed: 'ignored_events' });
      });

      it('should skip message with invalid signature', async () => {
        mockDeps.verifySignature.mockReturnValue(false);

        const record = {
          body: '{}',
          messageAttributes: {
            'x-github-event': { stringValue: 'workflow_job' },
            'x-hub-signature-256': { stringValue: 'sha256=invalid' },
            'x-github-delivery': { stringValue: 'delivery-123' }
          }
        };

        const result = await handler.handle(record);

        expect(result).toEqual({ success: true, skipped: true, reason: 'invalid_signature' });
        expect(mockDeps.publishMetric).toHaveBeenCalledWith('InvalidSignature', 1.0, 'Count');
      });

      it('should return error when signature verification throws', async () => {
        mockDeps.getWebhookSecret.mockImplementation(() => {
          throw new Error('Secret not found');
        });

        const record = {
          body: '{}',
          messageAttributes: {
            'x-github-event': { stringValue: 'workflow_job' },
            'x-hub-signature-256': { stringValue: 'sha256=abc' },
            'x-github-delivery': { stringValue: 'delivery-123' }
          }
        };

        const result = await handler.handle(record);

        expect(result).toEqual({ success: false, error: 'Secret not found' });
      });
    });

    describe('handle - idempotency', () => {
      it('should skip duplicate deliveries', async () => {
        mockDeps.checkIdempotency.mockReturnValue(true);

        const record = {
          body: '{"action": "queued"}',
          messageAttributes: {
            'x-github-event': { stringValue: 'workflow_job' },
            'x-hub-signature-256': { stringValue: 'sha256=valid' },
            'x-github-delivery': { stringValue: 'delivery-duplicate' }
          }
        };

        const result = await handler.handle(record);

        expect(result).toEqual({ success: true, skipped: true, reason: 'duplicate' });
      });
    });

    describe('handle - JSON parsing', () => {
      it('should skip message with invalid JSON body', async () => {
        const record = {
          body: 'not-valid-json',
          messageAttributes: {
            'x-github-event': { stringValue: 'workflow_job' },
            'x-hub-signature-256': { stringValue: 'sha256=valid' },
            'x-github-delivery': { stringValue: 'delivery-123' }
          }
        };

        const result = await handler.handle(record);

        expect(result).toEqual({ success: true, skipped: true, reason: 'invalid_json' });
      });
    });

    describe('handle - workflow_job routing', () => {
      it('should enqueue job for queued workflow_job with matching labels', async () => {
        const payload = {
          action: 'queued',
          workflow_job: {
            id: 12345,
            run_id: 67890,
            labels: ['self-hosted', 'ecs', 'fargate', 'arm', 'spot', 'runner-999']
          },
          repository: { full_name: 'owner/repo' }
        };

        const record = {
          body: JSON.stringify(payload),
          messageAttributes: {
            'x-github-event': { stringValue: 'workflow_job' },
            'x-hub-signature-256': { stringValue: 'sha256=valid' },
            'x-github-delivery': { stringValue: 'delivery-123' }
          }
        };

        const result = await handler.handle(record);

        expect(result).toEqual({ success: true, routed: 'job_queue' });
        expect(mockDeps.enqueueJob).toHaveBeenCalledWith({
          job_id: 12345,
          job_labels: ['self-hosted', 'ecs', 'fargate', 'arm', 'spot', 'runner-999'],
          github_repo: 'owner/repo',
          run_id: 67890,
          runner_type: 'ecs'
        });
      });

      it('should route cancelled/completed actions to cancellation queue', async () => {
        const payload = {
          action: 'completed',
          workflow_job: { id: 12345, run_id: 67890, runner_name: 'runner-1' },
          repository: { full_name: 'owner/repo' }
        };

        const record = {
          body: JSON.stringify(payload),
          messageAttributes: {
            'x-github-event': { stringValue: 'workflow_job' },
            'x-hub-signature-256': { stringValue: 'sha256=valid' },
            'x-github-delivery': { stringValue: 'delivery-123' }
          }
        };

        const result = await handler.handle(record);

        expect(result).toEqual({ success: true, routed: 'cancellation_queue' });
        expect(mockDeps.enqueueCancellation).toHaveBeenCalledWith({
          action: 'completed',
          job_id: 12345,
          run_id: 67890,
          runner_name: 'runner-1',
          github_repo: 'owner/repo',
          timestamp: expect.any(String)
        });
      });

      it('should route in_progress actions to ignored events', async () => {
        const payload = {
          action: 'in_progress',
          workflow_job: { id: 12345 }
        };

        const record = {
          body: JSON.stringify(payload),
          messageAttributes: {
            'x-github-event': { stringValue: 'workflow_job' },
            'x-hub-signature-256': { stringValue: 'sha256=valid' },
            'x-github-delivery': { stringValue: 'delivery-123' }
          }
        };

        const result = await handler.handle(record);

        expect(result).toEqual({ success: true, routed: 'ignored_events' });
        expect(mockDeps.enqueueIgnored).toHaveBeenCalled();
      });

      it('should route jobs without matching runner type to ignored events', async () => {
        mockDeps.getRunnerType.mockReturnValue([null]);

        const payload = {
          action: 'queued',
          workflow_job: {
            id: 12345,
            labels: ['self-hosted', 'ubuntu-latest']
          }
        };

        const record = {
          body: JSON.stringify(payload),
          messageAttributes: {
            'x-github-event': { stringValue: 'workflow_job' },
            'x-hub-signature-256': { stringValue: 'sha256=valid' },
            'x-github-delivery': { stringValue: 'delivery-123' }
          }
        };

        const result = await handler.handle(record);

        expect(result).toEqual({ success: true, routed: 'ignored_events' });
      });
    });

    describe('handle - workflow_run routing', () => {
      it('should acknowledge workflow_run events', async () => {
        const payload = {
          action: 'completed',
          workflow_run: {
            id: 99999,
            conclusion: 'success'
          }
        };

        const record = {
          body: JSON.stringify(payload),
          messageAttributes: {
            'x-github-event': { stringValue: 'workflow_run' },
            'x-hub-signature-256': { stringValue: 'sha256=valid' },
            'x-github-delivery': { stringValue: 'delivery-123' }
          }
        };

        const result = await handler.handle(record);

        expect(result).toEqual({ success: true, routed: 'acknowledged' });
      });
    });

    describe('handle - ping event', () => {
      it('should acknowledge ping events', async () => {
        const payload = { zen: 'Testing is important' };

        const record = {
          body: JSON.stringify(payload),
          messageAttributes: {
            'x-github-event': { stringValue: 'ping' },
            'x-hub-signature-256': { stringValue: 'sha256=valid' },
            'x-github-delivery': { stringValue: 'delivery-123' }
          }
        };

        const result = await handler.handle(record);

        expect(result).toEqual({ success: true, routed: 'ping_acknowledged' });
      });
    });

    describe('handle - unknown event types', () => {
      it('should route unknown event types to ignored events', async () => {
        const payload = { data: 'test' };

        const record = {
          body: JSON.stringify(payload),
          messageAttributes: {
            'x-github-event': { stringValue: 'push' },
            'x-hub-signature-256': { stringValue: 'sha256=valid' },
            'x-github-delivery': { stringValue: 'delivery-123' }
          }
        };

        const result = await handler.handle(record);

        expect(result).toEqual({ success: true, routed: 'ignored_events' });
        expect(mockDeps.enqueueIgnored).toHaveBeenCalled();
      });
    });

    describe('handle - metrics', () => {
      it('should publish processing time metric on successful processing', async () => {
        const payload = { action: 'queued', workflow_job: { id: 1, labels: [] } };
        mockDeps.getRunnerType.mockReturnValue([null]);

        const record = {
          body: JSON.stringify(payload),
          messageAttributes: {
            'x-github-event': { stringValue: 'workflow_job' },
            'x-hub-signature-256': { stringValue: 'sha256=valid' },
            'x-github-delivery': { stringValue: 'delivery-123' }
          }
        };

        await handler.handle(record);

        expect(mockDeps.publishMetric).toHaveBeenCalledWith(
          'WebhookIngressProcessingTime',
          expect.any(Number),
          'Milliseconds'
        );
      });
    });

    describe('handle - edge cases', () => {
      it('should handle missing workflow_job object', async () => {
        const payload = { action: 'queued' };

        const record = {
          body: JSON.stringify(payload),
          messageAttributes: {
            'x-github-event': { stringValue: 'workflow_job' },
            'x-hub-signature-256': { stringValue: 'sha256=valid' },
            'x-github-delivery': { stringValue: 'delivery-123' }
          }
        };

        mockDeps.getRunnerType.mockReturnValue([null]);
        const result = await handler.handle(record);

        expect(result).toEqual({ success: true, routed: 'ignored_events' });
      });

      it('should handle missing repository object', async () => {
        const payload = {
          action: 'queued',
          workflow_job: { id: 1, labels: ['ecs'] }
        };

        const record = {
          body: JSON.stringify(payload),
          messageAttributes: {
            'x-github-event': { stringValue: 'workflow_job' },
            'x-hub-signature-256': { stringValue: 'sha256=valid' },
            'x-github-delivery': { stringValue: 'delivery-123' }
          }
        };

        await handler.handle(record);

        expect(mockDeps.enqueueJob).toHaveBeenCalledWith(
          expect.objectContaining({ github_repo: undefined })
        );
      });

      it('should handle empty body', async () => {
        const record = {
          body: '',
          messageAttributes: {
            'x-github-event': { stringValue: 'workflow_job' },
            'x-hub-signature-256': { stringValue: 'sha256=valid' },
            'x-github-delivery': { stringValue: 'delivery-123' }
          }
        };

        const result = await handler.handle(record);

        expect(result).toEqual({ success: true, skipped: true, reason: 'invalid_json' });
      });
    });
  });
});
