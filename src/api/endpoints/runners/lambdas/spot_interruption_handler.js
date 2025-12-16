const https = require('https');
const {
  getGitHubToken,
  getECSClient
} = require('/opt/nodejs/runners-layer');
const { DescribeTasksCommand } = require('@aws-sdk/client-ecs');
const { DescribeInstancesCommand } = require('@aws-sdk/client-ec2');
const { EC2Client } = require('@aws-sdk/client-ec2');

const logger = {
  info: (...args) => console.log('[INFO]', ...args),
  warn: (...args) => console.warn('[WARN]', ...args),
  error: (...args) => console.error('[ERROR]', ...args)
};

function githubApiRequest(method, endpoint, token, body = null) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.github.com',
      path: endpoint,
      method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'SpotInterruptionHandler/1.0'
      }
    };

    if (body) {
      options.headers['Content-Type'] = 'application/json';
    }

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve({ status: res.statusCode, data: data ? JSON.parse(data) : {} });
        } else {
          reject(new Error(`GitHub API error ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', reject);
    if (body) {
      req.write(JSON.stringify(body));
    }
    req.end();
  });
}

async function getWorkflowRunStatus(githubToken, githubRepo, runId) {
  try {
    const result = await githubApiRequest('GET', `/repos/${githubRepo}/actions/runs/${runId}`, githubToken);
    return result.data.status || 'unknown';
  } catch (err) {
    logger.error('Failed to get workflow run status:', err.message);
    return 'unknown';
  }
}

async function cancelWorkflowRun(githubToken, githubRepo, runId) {
  try {
    const result = await githubApiRequest('POST', `/repos/${githubRepo}/actions/runs/${runId}/cancel`, githubToken, {});
    if (result.status === 202) {
      logger.info('Successfully cancelled workflow run', runId);
      return true;
    }
    logger.warn('Unexpected response status', result.status, 'for cancel');
  } catch (err) {
    logger.error('Failed to cancel workflow', runId, ':', err.message);
  }
  return false;
}

async function createCheckRunAnnotation(githubToken, githubRepo, headSha, title, summary) {
  const payload = {
    name: 'Spot Interruption Handler',
    head_sha: headSha,
    status: 'completed',
    conclusion: 'neutral',
    output: { title, summary }
  };
  try {
    const result = await githubApiRequest('POST', `/repos/${githubRepo}/check-runs`, githubToken, payload);
    if (result.status === 201) {
      logger.info('Successfully created check run annotation');
      return true;
    }
    logger.warn('Unexpected response status', result.status, 'for check run');
  } catch (err) {
    logger.error('Failed to create check run:', err.message);
  }
  return false;
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function waitForWorkflowCompletion(githubToken, githubRepo, runId, timeoutSeconds = 60) {
  const startTime = Date.now();
  while ((Date.now() - startTime) / 1000 < timeoutSeconds) {
    try {
      const result = await githubApiRequest('GET', `/repos/${githubRepo}/actions/runs/${runId}`, githubToken);
      if (result.data.status === 'completed') {
        logger.info('Workflow', runId, 'completed');
        return true;
      }
    } catch (err) {
      logger.warn('Error polling workflow status:', err.message);
    }
    await sleep(5000);
  }
  logger.warn('Timeout waiting for workflow', runId, 'to complete');
  return false;
}

async function getWorkflowInfoFromRun(githubToken, githubRepo, runId) {
  try {
    const result = await githubApiRequest('GET', `/repos/${githubRepo}/actions/runs/${runId}`, githubToken);
    return {
      workflowId: String(result.data.workflow_id || ''),
      headSha: result.data.head_sha || ''
    };
  } catch (err) {
    logger.error('Failed to get workflow info:', err.message);
    return { workflowId: '', headSha: '' };
  }
}

async function dispatchWorkflow(githubToken, githubRepo, workflowId, ref, reason) {
  const payload = {
    ref,
    inputs: { spot_recovery_reason: reason }
  };
  try {
    const result = await githubApiRequest(
      'POST',
      `/repos/${githubRepo}/actions/workflows/${workflowId}/dispatches`,
      githubToken,
      payload
    );
    if (result.status === 204) {
      logger.info('Successfully dispatched workflow', workflowId);
      return true;
    }
    logger.warn('Unexpected response status', result.status, 'for dispatch');
  } catch (err) {
    logger.error('Failed to dispatch workflow:', err.message);
  }
  return false;
}

async function recoverFromSpotInterruption(githubToken, githubRepo, runId, instanceId) {
  const { workflowId, headSha } = await getWorkflowInfoFromRun(githubToken, githubRepo, runId);
  if (!workflowId) {
    logger.error('Failed to get workflow info for run', runId);
    return { statusCode: 500, body: 'Failed to get workflow info' };
  }

  if (!await cancelWorkflowRun(githubToken, githubRepo, runId)) {
    logger.error('Failed to cancel workflow run', runId);
    return { statusCode: 500, body: 'Failed to cancel workflow' };
  }

  const reason = (
    `EC2 Spot Instance ${instanceId} received interruption warning. ` +
    `AWS is reclaiming spot capacity. Workflow cancelled and will be ` +
    `automatically re-triggered.`
  );
  await createCheckRunAnnotation(githubToken, githubRepo, headSha, 'Spot Instance Interruption', reason);

  await waitForWorkflowCompletion(githubToken, githubRepo, runId);

  const recoveryReason = `Auto-recovery from spot interruption of instance ${instanceId}`;
  if (await dispatchWorkflow(githubToken, githubRepo, workflowId, 'main', recoveryReason)) {
    logger.info('Successfully dispatched recovery workflow for', workflowId);
    return { statusCode: 200, body: 'Recovery workflow dispatched' };
  }

  logger.error('Failed to dispatch recovery workflow');
  return { statusCode: 500, body: 'Failed to dispatch recovery workflow' };
}

function isSpotInterruption(stopCode, stoppedReason) {
  return stopCode.includes('SpotInterruption') || stoppedReason.toLowerCase().includes('capacity');
}

async function triggerEcsRecovery(githubRepo, runId, taskArn) {
  const githubToken = await getGitHubToken();
  if (!githubToken) {
    logger.error('No GitHub token available');
    return { statusCode: 500, body: 'No GitHub token' };
  }
  const workflowStatus = await getWorkflowRunStatus(githubToken, githubRepo, runId);
  if (!['queued', 'in_progress', 'waiting'].includes(workflowStatus)) {
    logger.info('Workflow', runId, 'not active (status=', workflowStatus, '), skipping');
    return { statusCode: 200, body: `Workflow not active: ${workflowStatus}` };
  }
  logger.info('Initiating ECS spot recovery for run_id=', runId);
  return recoverFromEcsSpotInterruption(githubToken, githubRepo, runId, taskArn);
}

async function recoverFromEcsSpotInterruption(githubToken, githubRepo, runId, taskArn) {
  const { workflowId, headSha } = await getWorkflowInfoFromRun(githubToken, githubRepo, runId);
  if (!workflowId) {
    logger.error('Failed to get workflow info for run', runId);
    return { statusCode: 500, body: 'Failed to get workflow info' };
  }

  if (!await cancelWorkflowRun(githubToken, githubRepo, runId)) {
    logger.error('Failed to cancel workflow run', runId);
    return { statusCode: 500, body: 'Failed to cancel workflow' };
  }

  const taskId = taskArn.includes('/') ? taskArn.split('/').pop() : taskArn;
  const reason = (
    `ECS Fargate Spot task ${taskId} was interrupted. ` +
    `AWS reclaimed spot capacity. Workflow cancelled and will be ` +
    `automatically re-triggered.`
  );
  await createCheckRunAnnotation(githubToken, githubRepo, headSha, 'ECS Spot Interruption', reason);

  await waitForWorkflowCompletion(githubToken, githubRepo, runId);

  const recoveryReason = `Auto-recovery from ECS spot interruption of task ${taskId}`;
  if (await dispatchWorkflow(githubToken, githubRepo, workflowId, 'main', recoveryReason)) {
    logger.info('Successfully dispatched recovery workflow for', workflowId);
    return { statusCode: 200, body: 'Recovery workflow dispatched' };
  }

  logger.error('Failed to dispatch recovery workflow');
  return { statusCode: 500, body: 'Failed to dispatch recovery workflow' };
}

async function getEcsTaskTags(taskArn) {
  const tagDict = {};
  try {
    const cluster = process.env.ECS_CLUSTER || '';
    const response = await getECSClient().send(new DescribeTasksCommand({
      cluster,
      tasks: [taskArn],
      include: ['TAGS']
    }));
    const tasks = response.tasks || [];
    if (tasks.length > 0) {
      const tags = tasks[0].tags || [];
      for (const tag of tags) {
        tagDict[tag.key] = tag.value;
      }
    }
  } catch (err) {
    logger.error('Failed to get ECS task tags:', err.message);
  }
  return tagDict;
}

async function handleEcsTaskStopped(event) {
  const detail = event.detail || {};
  const stopCode = detail.stopCode || '';
  const stoppedReason = detail.stoppedReason || '';
  const taskArn = detail.taskArn || '';
  const tagDict = await getEcsTaskTags(taskArn);
  const runId = tagDict.RunId || '';
  const githubRepo = tagDict.GitHubRepo || '';

  logger.info(
    'ECS task stopped: arn=', taskArn, ', stopCode=', stopCode,
    ', reason=', stoppedReason, ', run_id=', runId
  );

  if (!runId) {
    logger.info('No run_id in task tags, skipping');
    return { statusCode: 200, body: 'No run_id' };
  }
  if (!isSpotInterruption(stopCode, stoppedReason)) {
    logger.info('Not a spot interruption, skipping recovery');
    return { statusCode: 200, body: 'Not a spot interruption' };
  }
  return triggerEcsRecovery(githubRepo, runId, taskArn);
}

async function getEc2InstanceTags(instanceId) {
  const tagDict = {};
  try {
    const ec2 = new EC2Client({});
    const response = await ec2.send(new DescribeInstancesCommand({
      InstanceIds: [instanceId]
    }));
    const tags = response.Reservations?.[0]?.Instances?.[0]?.Tags || [];
    for (const tag of tags) {
      tagDict[tag.Key] = tag.Value;
    }
  } catch (err) {
    logger.error('Failed to get instance tags:', err.message);
  }
  return tagDict;
}

async function handleEc2SpotInterruption(event) {
  const instanceId = event.detail?.['instance-id'] || '';
  logger.info('EC2 spot interruption warning for instance:', instanceId);

  const tagDict = await getEc2InstanceTags(instanceId);
  if (Object.keys(tagDict).length === 0) {
    return { statusCode: 500, body: 'Failed to get instance tags' };
  }

  const runId = tagDict.RunId || '';
  const githubRepo = tagDict.GitHubRepo || '';

  if (!runId) {
    logger.info('No run_id in instance tags, skipping');
    return { statusCode: 200, body: 'No run_id' };
  }

  const githubToken = await getGitHubToken();
  if (!githubToken) {
    logger.error('No GitHub token available');
    return { statusCode: 500, body: 'No GitHub token' };
  }

  const workflowStatus = await getWorkflowRunStatus(githubToken, githubRepo, runId);
  if (!['queued', 'in_progress', 'waiting'].includes(workflowStatus)) {
    logger.info('Workflow', runId, 'not active (status=', workflowStatus, '), skipping');
    return { statusCode: 200, body: `Workflow not active: ${workflowStatus}` };
  }

  logger.info('Initiating spot interruption recovery for run_id=', runId);
  return recoverFromSpotInterruption(githubToken, githubRepo, runId, instanceId);
}

exports.handler = async (event, _context) => {
  logger.info('Received event:', JSON.stringify(event));
  const source = event.source || '';
  const detailType = event['detail-type'] || '';

  if (source === 'aws.ecs' && detailType === 'ECS Task State Change') {
    const lastStatus = event.detail?.lastStatus || '';
    if (lastStatus === 'STOPPED') {
      return handleEcsTaskStopped(event);
    }
  } else if (source === 'aws.ec2' && detailType === 'EC2 Spot Instance Interruption Warning') {
    return handleEc2SpotInterruption(event);
  }

  logger.info('Ignoring event: source=', source, ', detail-type=', detailType);
  return { statusCode: 200, body: 'Event ignored' };
};
