const crypto = require('crypto');
const https = require('https');
const {
  getGitHubToken,
  getSSMClient,
  getDynamoDBClient,
  getSQSClient,
  getCloudWatchClient,
  getECSClient,
  getEC2Client,
  parseLabels,
  validateLabels,
  LabelParseError,
  LabelValidationError,
  isWebhookIngressQueue,
  IngressHandler
} = require('/opt/nodejs/runners-layer');
const { GetParameterCommand } = require('@aws-sdk/client-ssm');
const { PutItemCommand, QueryCommand, DeleteItemCommand } = require('@aws-sdk/client-dynamodb');
const { SendMessageCommand, GetQueueAttributesCommand } = require('@aws-sdk/client-sqs');
const { PutMetricDataCommand } = require('@aws-sdk/client-cloudwatch');
const { StopTaskCommand } = require('@aws-sdk/client-ecs');
const { TerminateInstancesCommand } = require('@aws-sdk/client-ec2');

const logger = {
  info: (...args) => console.log('[INFO]', ...args),
  warn: (...args) => console.warn('[WARN]', ...args),
  error: (...args) => console.error('[ERROR]', ...args)
};

const webhookSecretCache = { value: null };
const apiKeyCache = { value: null };
const githubTokenCache = { value: null };
let testModeEnabled = false;

const circuitBreakerState = {
  failures: 0,
  lastFailureTime: 0,
  state: 'closed'
};

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

function checkCircuitBreaker() {
  const currentTime = Date.now() / 1000;
  const failureThreshold = 5;
  const timeoutSeconds = 60;

  if (circuitBreakerState.state === 'open') {
    if (currentTime - circuitBreakerState.lastFailureTime > timeoutSeconds) {
      logger.info('Circuit breaker transitioning to half-open state');
      circuitBreakerState.state = 'half-open';
      circuitBreakerState.failures = 0;
      publishMetric('CircuitBreakerState', 1.0, 'Count');
      return true;
    }
    publishMetric('CircuitBreakerState', 2.0, 'Count');
    return false;
  }

  if (circuitBreakerState.failures >= failureThreshold) {
    logger.warn('Circuit breaker opening due to', circuitBreakerState.failures, 'failures');
    circuitBreakerState.state = 'open';
    circuitBreakerState.lastFailureTime = currentTime;
    publishMetric('CircuitBreakerState', 2.0, 'Count');
    return false;
  }

  publishMetric('CircuitBreakerState', 0.0, 'Count');
  return true;
}

function recordCircuitBreakerSuccess() {
  if (circuitBreakerState.state === 'half-open') {
    logger.info('Circuit breaker closing after successful request');
    circuitBreakerState.state = 'closed';
  }
  circuitBreakerState.failures = 0;
}

function recordCircuitBreakerFailure() {
  circuitBreakerState.failures++;
  circuitBreakerState.lastFailureTime = Date.now() / 1000;
  if (circuitBreakerState.state === 'half-open') {
    logger.warn('Circuit breaker reopening after failed request in half-open state');
    circuitBreakerState.state = 'open';
  }
}

function shouldRecordCircuitBreakerFailure(statusCode) {
  return statusCode === null;
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

async function getWorkflowRunners(runId) {
  const tableName = process.env.WORKFLOW_RUNNERS_TABLE;
  if (!tableName) {
    return [];
  }
  try {
    const response = await getDynamoDBClient().send(new QueryCommand({
      TableName: tableName,
      KeyConditionExpression: 'run_id = :rid',
      ExpressionAttributeValues: { ':rid': { S: String(runId) } }
    }));
    return (response.Items || []).map(item => ({
      run_id: item.run_id?.S,
      runner_type: item.runner_type?.S,
      resource_id: item.resource_id?.S,
      runner_name: item.runner_name?.S || '',
      github_repo: item.github_repo?.S || ''
    }));
  } catch (err) {
    logger.error('Failed to get workflow runners:', err.message);
    return [];
  }
}

async function deleteWorkflowRunner(runId, runnerType) {
  const tableName = process.env.WORKFLOW_RUNNERS_TABLE;
  if (!tableName) {
    return false;
  }
  try {
    await getDynamoDBClient().send(new DeleteItemCommand({
      TableName: tableName,
      Key: {
        run_id: { S: String(runId) },
        runner_type: { S: runnerType }
      }
    }));
    return true;
  } catch (err) {
    logger.error('Failed to delete workflow runner:', err.message);
    return false;
  }
}

function deleteGitHubRunner(githubToken, githubRepo, runnerName) {
  return new Promise((resolve) => {
    const options = {
      hostname: 'api.github.com',
      path: `/repos/${githubRepo}/actions/runners`,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'WebhookRouter/1.0'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode !== 200) {
          logger.error('Failed to list runners for', runnerName);
          return resolve(false);
        }
        const runners = JSON.parse(data).runners || [];
        const runner = runners.find(r => r.name === runnerName);
        if (!runner) {
          logger.info('Runner', runnerName, 'not found in GitHub');
          return resolve(true);
        }

        const deleteOpts = {
          hostname: 'api.github.com',
          path: `/repos/${githubRepo}/actions/runners/${runner.id}`,
          method: 'DELETE',
          headers: options.headers
        };
        const deleteReq = https.request(deleteOpts, (deleteRes) => {
          if (deleteRes.statusCode === 204) {
            logger.info('Deleted GitHub runner', runnerName, '(id=', runner.id, ')');
            resolve(true);
          } else {
            logger.error('Failed to delete GitHub runner', runnerName);
            resolve(false);
          }
        });
        deleteReq.on('error', () => resolve(false));
        deleteReq.end();
      });
    });
    req.on('error', () => resolve(false));
    req.end();
  });
}

async function terminateEcsTask(taskArn) {
  const cluster = process.env.ECS_CLUSTER;
  if (!cluster) {
    return false;
  }
  try {
    await getECSClient().send(new StopTaskCommand({
      cluster,
      task: taskArn,
      reason: 'Workflow completed'
    }));
    logger.info('Stopped ECS task:', taskArn);
    return true;
  } catch (err) {
    logger.error('Failed to stop ECS task', taskArn, ':', err.message);
    return false;
  }
}

async function terminateEc2Instance(instanceId) {
  try {
    await getEC2Client().send(new TerminateInstancesCommand({
      InstanceIds: [instanceId]
    }));
    logger.info('Terminated EC2 instance:', instanceId);
    return true;
  } catch (err) {
    logger.error('Failed to terminate EC2 instance', instanceId, ':', err.message);
    return false;
  }
}

async function terminateRunnersForWorkflow(runId) {
  const runners = await getWorkflowRunners(runId);
  if (runners.length === 0) {
    logger.info('No runners found for workflow run', runId);
    return { terminated: 0, failed: 0 };
  }

  const githubToken = await getGitHubToken();
  let terminated = 0;
  let failed = 0;

  for (const runner of runners) {
    let success = false;
    if (runner.runner_type.startsWith('ec2')) {
      success = await terminateEc2Instance(runner.resource_id);
    } else if (runner.runner_type.startsWith('fargate')) {
      success = await terminateEcsTask(runner.resource_id);
    }

    if (success) {
      terminated++;
      await deleteWorkflowRunner(runId, runner.runner_type);
      if (githubToken && runner.runner_name && runner.github_repo) {
        await deleteGitHubRunner(githubToken, runner.github_repo, runner.runner_name);
      }
    } else {
      failed++;
    }
  }

  const result = { terminated, failed };
  logger.info('Terminated runners for workflow', runId, ':', JSON.stringify(result));
  return result;
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

async function getApiKey(forceRefresh = false) {
  if (forceRefresh) {
    apiKeyCache.value = null;
  }
  if (apiKeyCache.value) {
    return apiKeyCache.value;
  }

  const parameterName = process.env.API_KEY_PARAMETER_NAME;
  if (!parameterName) {
    throw new Error('API_KEY_PARAMETER_NAME environment variable not set');
  }

  try {
    const response = await getSSMClient().send(new GetParameterCommand({
      Name: parameterName,
      WithDecryption: true
    }));
    const apiKey = response.Parameter?.Value;
    apiKeyCache.value = apiKey;
    return apiKey;
  } catch (err) {
    logger.error('Failed to retrieve API key:', err.message);
    throw new Error(`Cannot retrieve API key: ${err.message}`);
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

function makeHttpRequestWithRetry(endpoint, payload, headers = {}, maxRetries = 3) {
  return new Promise((resolve) => {
    const url = new URL(endpoint);
    let lastStatusCode = null;

    const attempt = (attemptNum) => {
      const options = {
        hostname: url.hostname,
        port: url.port || 443,
        path: url.pathname + url.search,
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...headers
        }
      };

      const req = https.request(options, (res) => {
        let data = '';
        res.on('data', chunk => { data += chunk; });
        res.on('end', () => {
          lastStatusCode = res.statusCode;
          if (res.statusCode >= 200 && res.statusCode < 300) {
            resolve([true, JSON.parse(data || '{}'), null, res.statusCode]);
          } else if (res.statusCode >= 400 && res.statusCode < 500) {
            resolve([false, null, `HTTP ${res.statusCode}`, res.statusCode]);
          } else if (attemptNum >= maxRetries) {
            resolve([false, null, `HTTP ${res.statusCode} after ${maxRetries + 1} attempts`, res.statusCode]);
          } else {
            setTimeout(() => attempt(attemptNum + 1), Math.pow(2, attemptNum) * 1000);
          }
        });
      });

      req.on('error', (err) => {
        if (attemptNum >= maxRetries) {
          resolve([false, null, `${err.message} after ${maxRetries + 1} attempts`, lastStatusCode]);
        } else {
          setTimeout(() => attempt(attemptNum + 1), Math.pow(2, attemptNum) * 1000);
        }
      });

      req.write(JSON.stringify(payload));
      req.end();
    };

    attempt(0);
  });
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

function buildRunnerEndpoint(endpointSuffix) {
  return `${process.env.API_BASE_URL}/v1/${endpointSuffix}`;
}

function handleRouteSuccess(jobId, runnerType, responseData) {
  logger.info('Successfully routed job', jobId, 'to', runnerType, 'runner');
  recordCircuitBreakerSuccess();
  return { success: true, runner_type: runnerType, response: responseData };
}

function handleRouteFailure(jobId, error, statusCode) {
  logger.error('Failed to route job', jobId, ':', error);
  if (shouldRecordCircuitBreakerFailure(statusCode)) {
    recordCircuitBreakerFailure();
  } else {
    logger.warn('Status', statusCode, 'for job', jobId, '- not counting as circuit breaker failure');
  }
  return { success: false, error };
}

async function routeRunnerRequest(jobId, jobLabels, githubRepo, runId = null) {
  if (!checkCircuitBreaker()) {
    logger.error('Circuit breaker is open, rejecting request for job', jobId);
    return { success: false, error: 'Service temporarily unavailable (circuit breaker open)' };
  }

  const [runnerType, endpointSuffix] = getRunnerTypeFromLabels(jobLabels);
  if (!runnerType || !endpointSuffix) {
    logger.error('No matching runner type for labels:', jobLabels);
    return { success: false, error: `No matching runner type for labels: ${JSON.stringify(jobLabels)}` };
  }

  let apiKey;
  try {
    apiKey = await getApiKey();
  } catch (err) {
    logger.error('Cannot route job', jobId, ':', err.message);
    return { success: false, error: err.message };
  }

  const endpoint = buildRunnerEndpoint(endpointSuffix);
  const payload = {
    job_id: jobId,
    job_labels: jobLabels,
    github_repo: githubRepo,
    run_id: runId,
    runner_type: runnerType
  };

  logger.info('Routing job', jobId, 'to', runnerType, 'runner:', endpoint, '(run_id=', runId, ')');

  const [success, responseData, error, statusCode] = await makeHttpRequestWithRetry(
    endpoint, payload, { 'x-api-key': apiKey }
  );

  if (success) {
    return handleRouteSuccess(jobId, runnerType, responseData);
  }
  return handleRouteFailure(jobId, error, statusCode);
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

async function handleSqsMessage(message) {
  try {
    const body = JSON.parse(message.body);
    const { job_id: jobId, job_labels: jobLabels, github_repo: githubRepo, run_id: runId } = body;

    logger.info(
      'Processing job from SQS: job_id=', jobId, ', labels=', JSON.stringify(jobLabels),
      ', repo=', githubRepo, ', run_id=', runId
    );

    const result = await routeRunnerRequest(jobId, jobLabels, githubRepo, runId);

    if (result.success) {
      logger.info('Successfully processed SQS message for job', jobId);
      return { success: true };
    }

    logger.error('Failed to process SQS message for job', jobId, ':', result.error);
    return { success: false, error: result.error };
  } catch (err) {
    logger.error('Failed to parse SQS message:', err.message);
    return { success: false, error: `Invalid message format: ${err.message}` };
  }
}

function handleHealthCheck() {
  const healthStatus = {
    status: 'healthy',
    circuit_breaker: circuitBreakerState.state,
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
    enqueueIgnored: enqueueIgnoredEvent
  };
  return new IngressHandler(deps);
}

exports.handler = async (event, _context) => {
  const startTime = Date.now();
  logger.info('Received event:', JSON.stringify(event));

  const records = event.Records || [];
  const isSqs = records.length > 0 && records[0].eventSource === 'aws:sqs';

  if (isSqs) {
    const eventSourceArn = records[0].eventSourceARN || '';

    let queueType;
    let handler;
    if (isWebhookIngressQueue(eventSourceArn)) {
      queueType = 'webhook_ingress';
      const ingressHandler = getIngressHandler();
      handler = (record) => ingressHandler.handle(record);
    } else {
      queueType = 'job';
      handler = handleSqsMessage;
    }

    logger.info('Processing SQS event from', queueType, 'queue');

    const results = [];
    for (const record of records) {
      const result = await handler(record);
      results.push(result);
    }

    if (!results.every(r => r.success)) {
      throw new Error(`One or more ${queueType} messages failed`);
    }
    return { statusCode: 200, body: JSON.stringify({ message: 'Processed' }) };
  }

  return handleApiGatewayEvent(event, startTime);
};
