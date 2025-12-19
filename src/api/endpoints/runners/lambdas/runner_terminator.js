const { getECSClient } = require('/opt/nodejs/clients/ecs');
const { getEC2Client } = require('/opt/nodejs/clients/ec2');
const { getCloudWatchClient } = require('/opt/nodejs/clients/cloudwatch');
const {
  ListTasksCommand,
  DescribeTasksCommand,
  StopTaskCommand
} = require('@aws-sdk/client-ecs');
const {
  DescribeInstancesCommand,
  TerminateInstancesCommand
} = require('@aws-sdk/client-ec2');
const { PutMetricDataCommand } = require('@aws-sdk/client-cloudwatch');

const logger = {
  info: (...args) => console.log('[INFO]', ...args),
  warn: (...args) => console.warn('[WARN]', ...args),
  error: (...args) => console.error('[ERROR]', ...args)
};

const WORKFLOW_RUNNER_TYPE_TAG = 'workflow-runner';

async function publishMetric(metricName, value, unit = 'None') {
  try {
    await getCloudWatchClient().send(new PutMetricDataCommand({
      Namespace: 'RunnerTerminator',
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

async function findEcsTaskByRunId(runId) {
  const cluster = process.env.ECS_CLUSTER;
  if (!cluster || !runId) {
    return null;
  }

  try {
    const ecs = getECSClient();
    const taskArns = [];

    // List all running/pending tasks
    for (const status of ['RUNNING', 'PENDING']) {
      let nextToken;
      do {
        const response = await ecs.send(new ListTasksCommand({
          cluster,
          desiredStatus: status,
          nextToken
        }));
        taskArns.push(...(response.taskArns || []));
        nextToken = response.nextToken;
      } while (nextToken);
    }

    if (taskArns.length === 0) {
      return null;
    }

    // Describe tasks in batches of 100 to find the one with matching RunId
    for (let i = 0; i < taskArns.length; i += 100) {
      const batch = taskArns.slice(i, i + 100);
      const response = await ecs.send(new DescribeTasksCommand({
        cluster,
        tasks: batch,
        include: ['TAGS']
      }));

      for (const task of response.tasks || []) {
        const tags = {};
        for (const t of task.tags || []) {
          tags[t.key] = t.value;
        }
        if (tags.RunId === String(runId)) {
          return {
            taskArn: task.taskArn,
            runnerName: tags.Name || null,
            tags
          };
        }
      }
    }
  } catch (err) {
    logger.error('Failed to find ECS task by RunId', runId, ':', err.message);
  }

  return null;
}

async function findEc2InstanceByRunId(runId) {
  const ec2ManagedByTag = process.env.EC2_MANAGED_BY_TAG;
  if (!ec2ManagedByTag || !runId) {
    return null;
  }

  try {
    const response = await getEC2Client().send(new DescribeInstancesCommand({
      Filters: [
        { Name: 'tag:RunId', Values: [String(runId)] },
        { Name: 'tag:Type', Values: [WORKFLOW_RUNNER_TYPE_TAG] },
        { Name: 'tag:ManagedBy', Values: [ec2ManagedByTag] },
        { Name: 'instance-state-name', Values: ['pending', 'running'] }
      ]
    }));

    for (const reservation of response.Reservations || []) {
      for (const instance of reservation.Instances || []) {
        const tags = {};
        for (const t of instance.Tags || []) {
          tags[t.Key] = t.Value;
        }
        return {
          instanceId: instance.InstanceId,
          runnerName: tags.Name || null,
          tags
        };
      }
    }
  } catch (err) {
    logger.error('Failed to find EC2 instance by RunId', runId, ':', err.message);
  }

  return null;
}

async function stopEcsTask(taskArn, reason) {
  const cluster = process.env.ECS_CLUSTER;
  if (!cluster) {
    logger.error('ECS_CLUSTER not configured');
    return false;
  }

  try {
    await getECSClient().send(new StopTaskCommand({
      cluster,
      task: taskArn,
      reason
    }));
    logger.info('Stopped ECS task:', taskArn, '(reason:', reason, ')');
    await publishMetric('EcsTasksStopped', 1, 'Count');
    return true;
  } catch (err) {
    if (err.name === 'InvalidParameterException' || err.message.includes('TaskNotFound')) {
      logger.info('Task already stopped or not found:', taskArn);
      return true;
    }
    logger.error('Failed to stop ECS task:', err.message);
    await publishMetric('EcsStopErrors', 1, 'Count');
    return false;
  }
}

async function terminateEc2Instance(instanceId, reason) {
  try {
    await getEC2Client().send(new TerminateInstancesCommand({
      InstanceIds: [instanceId]
    }));
    logger.info('Terminated EC2 instance:', instanceId, '(reason:', reason, ')');
    await publishMetric('Ec2InstancesTerminated', 1, 'Count');
    return true;
  } catch (err) {
    if (err.Code === 'InvalidInstanceID.NotFound' || err.Code === 'InvalidInstanceID.Malformed') {
      logger.info('Instance already terminated or not found:', instanceId);
      return true;
    }
    logger.error('Failed to terminate EC2 instance:', err.message);
    await publishMetric('Ec2TerminateErrors', 1, 'Count');
    return false;
  }
}

async function terminateRunnerByRunId(runId, action, jobId) {
  const reason = `Workflow ${action} (job_id=${jobId})`;

  // Try to find and stop ECS task first
  const ecsTask = await findEcsTaskByRunId(runId);
  if (ecsTask) {
    logger.info('Found ECS task for RunId', runId, ':', ecsTask.taskArn);
    const success = await stopEcsTask(ecsTask.taskArn, reason);
    return { success, type: 'ecs', resourceId: ecsTask.taskArn, runnerName: ecsTask.runnerName };
  }

  // Try to find and terminate EC2 instance
  const ec2Instance = await findEc2InstanceByRunId(runId);
  if (ec2Instance) {
    logger.info('Found EC2 instance for RunId', runId, ':', ec2Instance.instanceId);
    const success = await terminateEc2Instance(ec2Instance.instanceId, reason);
    return { success, type: 'ec2', resourceId: ec2Instance.instanceId, runnerName: ec2Instance.runnerName };
  }

  logger.info('No running ECS task or EC2 instance found for RunId', runId);
  await publishMetric('RunnerNotFound', 1, 'Count');
  return { success: true, type: 'none', resourceId: null, runnerName: null };
}

async function handleCancellationMessage(message) {
  try {
    const body = JSON.parse(message.body);
    const { action, job_id: jobId, run_id: runId, runner_name: runnerName } = body;

    logger.info(
      'Processing cancellation: action=', action, ', job_id=', jobId,
      ', run_id=', runId, ', runner_name=', runnerName
    );

    if (!runId) {
      logger.warn('No run_id in cancellation message, cannot find runner');
      return { success: true, skipped: true, reason: 'no_run_id' };
    }

    const result = await terminateRunnerByRunId(runId, action, jobId);

    if (result.success) {
      logger.info(
        'Successfully processed cancellation for job', jobId,
        ':', result.type, result.resourceId || '(no resource found)'
      );
      return { success: true, ...result };
    }

    logger.error('Failed to process cancellation for job', jobId);
    return { success: false, error: 'Failed to terminate runner' };
  } catch (err) {
    logger.error('Failed to parse cancellation message:', err.message);
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

  logger.info('Processing', records.length, 'cancellation(s) from SQS');

  const results = [];
  for (const record of records) {
    const result = await handleCancellationMessage(record);
    results.push(result);
  }

  const elapsed = Date.now() - startTime;
  await publishMetric('ProcessingTime', elapsed, 'Milliseconds');

  const successCount = results.filter(r => r.success).length;
  const failCount = results.filter(r => !r.success).length;

  logger.info('Processed', successCount, 'cancellations successfully,', failCount, 'failed');

  if (failCount > 0) {
    throw new Error(`${failCount} cancellation(s) failed`);
  }

  return {
    statusCode: 200,
    body: JSON.stringify({
      message: 'Processed',
      count: records.length,
      success: successCount,
      failed: failCount
    })
  };
};

// Exported for testing
module.exports = {
  handler: exports.handler,
  findEcsTaskByRunId,
  findEc2InstanceByRunId,
  stopEcsTask,
  terminateEc2Instance,
  terminateRunnerByRunId,
  handleCancellationMessage
};
