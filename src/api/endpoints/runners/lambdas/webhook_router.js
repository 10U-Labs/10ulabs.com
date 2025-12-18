const crypto = require('crypto');
const {
  getSSMClient,
  getDynamoDBClient,
  getSQSClient,
  getCloudWatchClient,
  parseLabels,
  validateLabels,
  LabelParseError,
  LabelValidationError,
  IngressHandler
} = require('/opt/nodejs/runners-layer');
const { GetParameterCommand } = require('@aws-sdk/client-ssm');
const { PutItemCommand } = require('@aws-sdk/client-dynamodb');
const { SendMessageCommand, GetQueueAttributesCommand } = require('@aws-sdk/client-sqs');
const { PutMetricDataCommand } = require('@aws-sdk/client-cloudwatch');

const logger = {
  info: (...args) => console.log('[INFO]', ...args),
  warn: (...args) => console.warn('[WARN]', ...args),
  error: (...args) => console.error('[ERROR]', ...args)
};

const webhookSecretCache = { value: null };
let testModeEnabled = false;

function setTestMode(enabled) {
  testModeEnabled = enabled;
}

async function publishMetric(metricName, value, unit = 'None') {
  if (testModeEnabled) {
    return;
  }
  try {
    await getCloudWatchClient().send(new PutMetricDataCommand({
      Namespace: 'WebhookRouter',
      MetricData: [{
        MetricName: metricName,
        Value: value,
        Unit: unit,
        Timestamp: new Date()
      }]
    }));
  } catch (err) {
    logger.warn('Failed to publish metric', metricName, ':', err.message);
  }
}

async function checkAndRecordIdempotency(requestId) {
  const tableName = process.env.IDEMPOTENCY_TABLE_NAME;
  if (!tableName) {
    logger.warn('IDEMPOTENCY_TABLE_NAME not set, skipping idempotency check');
    return false;
  }

  try {
    const ttl = Math.floor(Date.now() / 1000) + 86400;
    await getDynamoDBClient().send(new PutItemCommand({
      TableName: tableName,
      Item: {
        request_id: { S: requestId },
        ttl: { N: String(ttl) },
        timestamp: { N: String(Math.floor(Date.now() / 1000)) }
      },
      ConditionExpression: 'attribute_not_exists(request_id)'
    }));
    return false;
  } catch (err) {
    if (err.name === 'ConditionalCheckFailedException') {
      logger.warn('Duplicate request detected:', requestId);
      return true;
    }
    logger.error('Failed to check idempotency:', err.message);
    return false;
  }
}

async function enqueueJob(jobData) {
  const queueUrl = process.env.JOB_QUEUE_URL;
  if (!queueUrl) {
    logger.error('JOB_QUEUE_URL not set, cannot enqueue job');
    return { success: false, error: 'Job queue not configured' };
  }

  try {
    const response = await getSQSClient().send(new SendMessageCommand({
      QueueUrl: queueUrl,
      MessageBody: JSON.stringify(jobData)
    }));
    logger.info('Enqueued job to SQS:', response.MessageId);

    const attrs = await getSQSClient().send(new GetQueueAttributesCommand({
      QueueUrl: queueUrl,
      AttributeNames: ['ApproximateNumberOfMessages']
    }));
    const queueDepth = parseInt(attrs.Attributes?.ApproximateNumberOfMessages || '0', 10);
    publishMetric('QueueDepth', queueDepth, 'Count');

    return { success: true, message_id: response.MessageId };
  } catch (err) {
    logger.error('Failed to enqueue job:', err.message);
    return { success: false, error: err.message };
  }
}

async function enqueueIgnoredEvent(eventData, reason) {
  const queueUrl = process.env.IGNORED_EVENTS_QUEUE_URL;
  if (!queueUrl) {
    logger.warn('IGNORED_EVENTS_QUEUE_URL not set, skipping ignored event enqueue');
    return { success: false, error: 'Ignored events queue not configured' };
  }

  try {
    const messageBody = {
      event_data: eventData,
      reason,
      timestamp: new Date().toISOString()
    };
    const response = await getSQSClient().send(new SendMessageCommand({
      QueueUrl: queueUrl,
      MessageBody: JSON.stringify(messageBody)
    }));
    logger.info('Enqueued ignored event to SQS:', response.MessageId, '(reason:', reason, ')');
    return { success: true, message_id: response.MessageId };
  } catch (err) {
    logger.error('Failed to enqueue ignored event:', err.message);
    return { success: false, error: err.message };
  }
}

async function enqueueCancellation(cancellationData) {
  const queueUrl = process.env.CANCELLATION_QUEUE_URL;
  if (!queueUrl) {
    logger.warn('CANCELLATION_QUEUE_URL not set, skipping cancellation enqueue');
    return { success: false, error: 'Cancellation queue not configured' };
  }

  try {
    const response = await getSQSClient().send(new SendMessageCommand({
      QueueUrl: queueUrl,
      MessageBody: JSON.stringify(cancellationData)
    }));
    logger.info('Enqueued cancellation to SQS:', response.MessageId,
      '(job_id:', cancellationData.job_id, ', run_id:', cancellationData.run_id, ')');
    return { success: true, message_id: response.MessageId };
  } catch (err) {
    logger.error('Failed to enqueue cancellation:', err.message);
    return { success: false, error: err.message };
  }
}

function handleWorkflowRun(eventData) {
  const action = eventData.action;
  const workflowRun = eventData.workflow_run || {};
  const runId = workflowRun.id;
  const workflowName = workflowRun.name;
  const conclusion = workflowRun.conclusion;

  logger.info(
    'Workflow run', runId, action, ': workflow=', workflowName,
    ', conclusion=', conclusion, '(ephemeral runners self-cleanup)'
  );

  return {
    statusCode: 200,
    body: JSON.stringify({
      message: `Workflow run ${action} acknowledged`,
      run_id: runId,
      conclusion
    })
  };
}

async function getWebhookSecret(forceRefresh = false) {
  if (forceRefresh) {
    webhookSecretCache.value = null;
  }
  if (webhookSecretCache.value) {
    return webhookSecretCache.value;
  }

  const parameterName = process.env.WEBHOOK_SECRET_NAME;
  try {
    const response = await getSSMClient().send(new GetParameterCommand({
      Name: parameterName,
      WithDecryption: true
    }));
    const secret = response.Parameter?.Value;
    webhookSecretCache.value = secret;
    return secret;
  } catch (err) {
    logger.error('Failed to retrieve webhook secret:', err.message);
    throw new Error(`Cannot retrieve webhook secret: ${err.message}`);
  }
}

function verifySignature(payloadBody, signatureHeader, secret) {
  if (!signatureHeader) {
    return false;
  }
  const parts = signatureHeader.split('=');
  if (parts.length !== 2) {
    return false;
  }
  const githubSignature = parts[1];
  const computedSignature = crypto
    .createHmac('sha256', secret)
    .update(payloadBody)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(computedSignature),
    Buffer.from(githubSignature)
  );
}

function getRunnerTypeFromLabels(jobLabels) {
  let runnerType = null;
  let endpointSuffix = null;

  try {
    const parsed = parseLabels(jobLabels);
    validateLabels(parsed);
    const isE2e = jobLabels.includes('e2e');

    if (parsed.platform === 'ec2') {
      runnerType = isE2e ? 'ec2-e2e' : 'ec2';
      endpointSuffix = 'ec2-runner';
    } else if (parsed.platform === 'ecs') {
      runnerType = isE2e ? 'fargate-e2e' : 'fargate';
      endpointSuffix = 'ecs-runner';
    }
  } catch (err) {
    if (!(err instanceof LabelParseError || err instanceof LabelValidationError)) {
      throw err;
    }
  }

  return [runnerType, endpointSuffix];
}

async function handleWorkflowJob(eventData) {
  const action = eventData.action;
  const job = eventData.workflow_job || {};
  const jobId = job.id;
  const jobName = job.name;
  const jobLabels = job.labels || [];
  const jobStatus = job.status;
  const runId = job.run_id;
  const repoFullName = (eventData.repository || {}).full_name;

  logger.info(
    'Received workflow_job event: action=', action, ', job=', jobName,
    ', status=', jobStatus, ', labels=', JSON.stringify(jobLabels)
  );
  logger.info('workflow_job context: repo=', repoFullName, ', run_id=', runId);

  if (action !== 'queued') {
    logger.info("Ignoring action '", action, "' (only handle 'queued')");
    return {
      statusCode: 200,
      body: JSON.stringify({ message: `Ignored action: ${action}` })
    };
  }

  const [runnerType] = getRunnerTypeFromLabels(jobLabels);
  if (!runnerType) {
    logger.info('Job labels', JSON.stringify(jobLabels), "don't contain EC2 or Fargate runner type labels");
    return {
      statusCode: 200,
      body: JSON.stringify({ message: 'No matching runner type, ignoring' })
    };
  }

  logger.info('Enqueueing runner request for job', jobId, '(', jobName, '), runner_type=', runnerType);

  const jobData = {
    job_id: jobId,
    job_labels: jobLabels,
    github_repo: repoFullName,
    run_id: runId,
    runner_type: runnerType
  };

  if (testModeEnabled) {
    logger.info('Test mode enabled - skipping SQS enqueue');
    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'Test mode - job not enqueued',
        job_id: jobId,
        run_id: runId,
        test_mode: true
      })
    };
  }

  const result = await enqueueJob(jobData);

  if (result.success) {
    return {
      statusCode: 200,
      body: JSON.stringify({
        message: 'Job enqueued successfully',
        job_id: jobId,
        run_id: runId,
        message_id: result.message_id
      })
    };
  }

  return {
    statusCode: 500,
    body: JSON.stringify({
      message: 'Failed to enqueue job',
      error: result.error,
      job_id: jobId
    })
  };
}

function handleHealthCheck() {
  const healthStatus = {
    status: 'healthy',
    timestamp: Math.floor(Date.now() / 1000)
  };
  return {
    statusCode: 200,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(healthStatus)
  };
}

function parseEventBody(event) {
  let bodyStr = event.body || '';
  if (event.isBase64Encoded) {
    bodyStr = Buffer.from(bodyStr, 'base64').toString('utf-8');
  }
  let payload;
  if (bodyStr.startsWith('payload=')) {
    const payloadJson = decodeURIComponent(bodyStr.slice(8));
    payload = JSON.parse(payloadJson);
  } else {
    payload = JSON.parse(bodyStr);
  }
  return [bodyStr, payload];
}

async function verifyWebhookSignature(bodyStr, signatureHeader) {
  try {
    const webhookSecret = await getWebhookSecret();
    if (!verifySignature(bodyStr, signatureHeader, webhookSecret)) {
      logger.error('Webhook signature verification failed');
      return { statusCode: 401, body: JSON.stringify({ error: 'Invalid signature' }) };
    }
    return {};
  } catch (err) {
    logger.error('Cannot verify signature, secret unavailable:', err.message);
    return { statusCode: 500, body: JSON.stringify({ error: 'Authentication system unavailable' }) };
  }
}

function getHeaderCaseInsensitive(headers, key) {
  const lowerKey = key.toLowerCase();
  for (const [headerName, headerValue] of Object.entries(headers || {})) {
    if (headerName.toLowerCase() === lowerKey) {
      return headerValue;
    }
  }
  return null;
}

async function processWebhookEvent(event, headers, startTime) {
  let bodyStr, payload;
  try {
    [bodyStr, payload] = parseEventBody(event);
  } catch (err) {
    logger.error('Failed to parse request body:', err.message);
    logger.error('Body content (first 500 chars):', String(event.body || '').slice(0, 500));
    return { statusCode: 400, body: JSON.stringify({ error: 'Invalid JSON payload' }) };
  }

  const signatureHeader = getHeaderCaseInsensitive(headers, 'x-hub-signature-256');
  if (signatureHeader) {
    const errorResponse = await verifyWebhookSignature(bodyStr, signatureHeader);
    if (errorResponse.statusCode) {
      return errorResponse;
    }
  } else {
    logger.warn('No signature header found, proceeding without verification');
  }

  const deliveryId = getHeaderCaseInsensitive(headers, 'x-github-delivery');
  if (deliveryId && await checkAndRecordIdempotency(deliveryId)) {
    logger.info('Duplicate webhook delivery detected, returning success');
    await publishMetric('ProcessingTime', (Date.now() - startTime), 'Milliseconds');
    return { statusCode: 200, body: JSON.stringify({ message: 'Duplicate request ignored' }) };
  }

  const eventType = getHeaderCaseInsensitive(headers, 'x-github-event') || payload.event_type;
  logger.info('GitHub event type:', eventType);
  await publishMetric('ProcessingTime', (Date.now() - startTime), 'Milliseconds');

  if (eventType === 'workflow_job') {
    return handleWorkflowJob(payload);
  }

  if (eventType === 'workflow_run') {
    return handleWorkflowRun(payload);
  }

  if (eventType === 'ping') {
    logger.info('Received ping event');
  } else {
    logger.info('Ignoring event type:', eventType);
  }

  const message = eventType === 'ping' ? 'pong' : `Event type ${eventType} ignored`;
  return { statusCode: 200, body: JSON.stringify({ message }) };
}

async function handleApiGatewayEvent(event, startTime) {
  const headers = event.headers || {};
  setTestMode(getHeaderCaseInsensitive(headers, 'x-test-mode') === 'true');

  const httpContext = (event.requestContext || {}).http || {};
  const httpMethod = event.httpMethod || httpContext.method || '';
  if (httpMethod === 'OPTIONS') {
    return {
      statusCode: 200,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
        'Access-Control-Allow-Headers': (
          'Content-Type,x-api-key,x-github-event,' +
          'x-hub-signature-256,x-github-delivery'
        )
      },
      body: ''
    };
  }

  const path = event.path || event.rawPath || '';
  if (path === '/v1/runners/health') {
    return handleHealthCheck();
  }

  return processWebhookEvent(event, headers, startTime);
}

function getIngressHandler() {
  const deps = {
    getWebhookSecret,
    verifySignature,
    publishMetric,
    checkIdempotency: checkAndRecordIdempotency,
    getRunnerType: getRunnerTypeFromLabels,
    enqueueJob,
    enqueueIgnored: enqueueIgnoredEvent,
    enqueueCancellation
  };
  return new IngressHandler(deps);
}

exports.handler = async (event, _context) => {
  const startTime = Date.now();
  logger.info('Received event:', JSON.stringify(event));

  const records = event.Records || [];
  const isSqs = records.length > 0 && records[0].eventSource === 'aws:sqs';

  if (isSqs) {
    // This Lambda only handles webhook_ingress queue
    // job_queue is handled by runner_starter Lambda
    // cancellation_queue is handled by runner_terminator Lambda
    logger.info('Processing SQS event from webhook_ingress queue');

    const ingressHandler = getIngressHandler();
    const results = [];
    for (const record of records) {
      const result = await ingressHandler.handle(record);
      results.push(result);
    }

    if (!results.every(r => r.success)) {
      throw new Error('One or more webhook_ingress messages failed');
    }
    return { statusCode: 200, body: JSON.stringify({ message: 'Processed' }) };
  }

  return handleApiGatewayEvent(event, startTime);
};
