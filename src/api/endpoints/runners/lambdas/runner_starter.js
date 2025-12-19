const https = require('https');
const { getSSMClient } = require('/opt/nodejs/clients/ssm');
const { getCloudWatchClient } = require('/opt/nodejs/clients/cloudwatch');
const {
  parseLabels,
  validateLabels,
  LabelParseError,
  LabelValidationError
} = require('/opt/nodejs/common');
const { GetParameterCommand } = require('@aws-sdk/client-ssm');
const { PutMetricDataCommand } = require('@aws-sdk/client-cloudwatch');

const logger = {
  info: (...args) => console.log('[INFO]', ...args),
  warn: (...args) => console.warn('[WARN]', ...args),
  error: (...args) => console.error('[ERROR]', ...args)
};

const apiKeyCache = { value: null };

const circuitBreakerState = {
  failures: 0,
  lastFailureTime: 0,
  state: 'closed'
};

async function publishMetric(metricName, value, unit = 'None') {
  try {
    await getCloudWatchClient().send(new PutMetricDataCommand({
      Namespace: 'RunnerStarter',
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

exports.handler = async (event, _context) => {
  const startTime = Date.now();
  logger.info('Received event:', JSON.stringify(event));

  const records = event.Records || [];
  if (records.length === 0) {
    logger.warn('No records in event');
    return { statusCode: 200, body: JSON.stringify({ message: 'No records to process' }) };
  }

  logger.info('Processing', records.length, 'job(s) from SQS');

  const results = [];
  for (const record of records) {
    const result = await handleSqsMessage(record);
    results.push(result);
  }

  const elapsed = Date.now() - startTime;
  await publishMetric('ProcessingTime', elapsed, 'Milliseconds');

  if (!results.every(r => r.success)) {
    throw new Error('One or more job messages failed');
  }

  return { statusCode: 200, body: JSON.stringify({ message: 'Processed', count: records.length }) };
};

// Exported for testing
module.exports = {
  handler: exports.handler,
  getApiKey,
  checkCircuitBreaker,
  recordCircuitBreakerSuccess,
  recordCircuitBreakerFailure,
  routeRunnerRequest,
  handleSqsMessage,
  getRunnerTypeFromLabels,
  makeHttpRequestWithRetry
};
