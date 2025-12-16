const logger = {
  info: (...args) => console.log('[INFO]', ...args),
  warn: (...args) => console.warn('[WARN]', ...args),
  error: (...args) => console.error('[ERROR]', ...args)
};

function getMessageAttribute(record, attrName) {
  const attrs = record.messageAttributes || {};
  const attr = attrs[attrName] || {};
  return attr.stringValue || null;
}

function isWebhookIngressQueue(eventSourceArn) {
  return eventSourceArn.includes('Ingress');
}

class IngressHandler {
  constructor(deps) {
    this._deps = deps;
  }

  getDeps() {
    return this._deps;
  }

  _verifySignature(bodyStr, signature, deliveryId) {
    if (!signature) {
      logger.warn('No signature header in webhook ingress message');
      return null;
    }
    try {
      const webhookSecret = this._deps.getWebhookSecret();
      if (!this._deps.verifySignature(bodyStr, signature, webhookSecret)) {
        logger.error('Invalid signature for delivery', deliveryId);
        this._deps.publishMetric('InvalidSignature', 1.0, 'Count');
        return { success: true, skipped: true, reason: 'invalid_signature' };
      }
    } catch (err) {
      logger.error('Cannot verify signature:', err.message);
      return { success: false, error: err.message };
    }
    return null;
  }

  _routeWorkflowJob(payload) {
    const action = payload.action;
    if (action !== 'queued') {
      logger.info(`Ignoring workflow_job action '${action}'`);
      this._deps.enqueueIgnored(payload, `workflow_job action ${action} ignored`);
      return { success: true, routed: 'ignored_events' };
    }

    const job = payload.workflow_job || {};
    const jobLabels = job.labels || [];
    const [runnerType] = this._deps.getRunnerType(jobLabels);

    if (!runnerType) {
      logger.info(`Job labels ${JSON.stringify(jobLabels)} don't match EC2/Fargate`);
      this._deps.enqueueIgnored(payload, 'no matching runner type');
      return { success: true, routed: 'ignored_events' };
    }

    const jobData = {
      job_id: job.id,
      job_labels: jobLabels,
      github_repo: (payload.repository || {}).full_name,
      run_id: job.run_id,
      runner_type: runnerType
    };
    const result = this._deps.enqueueJob(jobData);
    return { success: result.success, routed: 'job_queue' };
  }

  _routeWorkflowRun(payload) {
    const action = payload.action;
    const workflowRun = payload.workflow_run || {};
    const runId = workflowRun.id;
    const conclusion = workflowRun.conclusion;
    logger.info(
      `Workflow run ${runId} ${action} (conclusion=${conclusion}) - no cleanup needed with ephemeral runners`
    );
    return { success: true, routed: 'acknowledged' };
  }

  _routeEvent(githubEvent, payload) {
    if (githubEvent === 'workflow_job') {
      return this._routeWorkflowJob(payload);
    }
    if (githubEvent === 'workflow_run') {
      return this._routeWorkflowRun(payload);
    }
    if (githubEvent === 'ping') {
      logger.info('Received ping event via ingress queue');
      return { success: true, routed: 'ping_acknowledged' };
    }
    logger.info(`Ignoring event type: ${githubEvent}`);
    this._deps.enqueueIgnored(payload, `event type ${githubEvent} ignored`);
    return { success: true, routed: 'ignored_events' };
  }

  _extractHeadersAndBody(record) {
    const rawBody = record.body || '';

    const headers = {
      'x-github-event': getMessageAttribute(record, 'x-github-event'),
      'x-hub-signature-256': getMessageAttribute(record, 'x-hub-signature-256'),
      'x-github-delivery': getMessageAttribute(record, 'x-github-delivery')
    };

    // Remove null values
    for (const key of Object.keys(headers)) {
      if (headers[key] === null) {
        delete headers[key];
      }
    }

    let payload = null;
    try {
      payload = JSON.parse(rawBody);
    } catch {
      payload = null;
    }

    return [headers, rawBody, payload];
  }

  handle(record) {
    const startTime = Date.now();

    const [headers, bodyStr, payload] = this._extractHeadersAndBody(record);
    const githubEvent = headers['x-github-event'];
    const signature = headers['x-hub-signature-256'];
    const deliveryId = headers['x-github-delivery'];

    logger.info(`Processing webhook ingress: event=${githubEvent}, delivery=${deliveryId}`);

    const sigError = this._verifySignature(bodyStr, signature, deliveryId);
    if (sigError) {
      return sigError;
    }

    if (deliveryId && this._deps.checkIdempotency(deliveryId)) {
      logger.info(`Duplicate webhook delivery ${deliveryId} detected`);
      return { success: true, skipped: true, reason: 'duplicate' };
    }

    if (payload === null) {
      logger.error('Failed to parse webhook body');
      return { success: true, skipped: true, reason: 'invalid_json' };
    }

    const elapsedMs = Date.now() - startTime;
    this._deps.publishMetric('WebhookIngressProcessingTime', elapsedMs, 'Milliseconds');
    return this._routeEvent(githubEvent, payload);
  }
}

module.exports = {
  getMessageAttribute,
  isWebhookIngressQueue,
  IngressHandler
};
