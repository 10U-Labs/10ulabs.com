const https = require('https');
const { getECSClient } = require('/opt/nodejs/clients/ecs');
const { getEC2Client } = require('/opt/nodejs/clients/ec2');
const { getGitHubToken } = require('/opt/nodejs/common');
const {
  ListTasksCommand,
  DescribeTasksCommand,
  StopTaskCommand
} = require('@aws-sdk/client-ecs');
const {
  DescribeInstancesCommand,
  TerminateInstancesCommand
} = require('@aws-sdk/client-ec2');

const logger = {
  info: (...args) => console.log('[INFO]', ...args),
  error: (...args) => console.error('[ERROR]', ...args)
};

const ORPHAN_THRESHOLD_SECONDS = 300;
const ECS_MANAGED_BY_TAG = 'ecs-runner-api';
const WORKFLOW_RUNNER_TYPE_TAG = 'workflow-runner';

function githubApiRequest(method, endpoint, token) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.github.com',
      path: endpoint,
      method,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'StaleRunnerCleanup/1.0'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(data ? JSON.parse(data) : {});
        } else if (res.statusCode === 204) {
          resolve({});
        } else {
          reject(new Error(`GitHub API error ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

async function getAllGitHubRunners(githubToken, githubRepo) {
  const runners = [];
  let page = 1;
  let hasMore = true;

  try {
    while (hasMore) {
      const endpoint = `/repos/${githubRepo}/actions/runners?per_page=100&page=${page}`;
      const data = await githubApiRequest('GET', endpoint, githubToken);
      const pageRunners = data.runners || [];
      runners.push(...pageRunners);
      if (pageRunners.length < 100) {
        hasMore = false;
      } else {
        page++;
      }
    }
    return runners;
  } catch (err) {
    logger.error('Failed to list GitHub runners:', err.message);
    return null;
  }
}

async function deleteGitHubRunnerById(githubToken, githubRepo, runnerId, runnerName) {
  try {
    await githubApiRequest('DELETE', `/repos/${githubRepo}/actions/runners/${runnerId}`, githubToken);
    logger.info('Deleted GitHub runner:', runnerName);
    return true;
  } catch (err) {
    if (err.message.includes('204')) {
      return true;
    }
    logger.error('Failed to delete GitHub runner', runnerName, ':', err.message);
    return false;
  }
}

async function deleteGitHubRunner(githubToken, githubRepo, runnerName) {
  const runners = await getAllGitHubRunners(githubToken, githubRepo);
  if (runners === null) {
    return false;
  }
  const runner = runners.find(r => r.name === runnerName);
  if (!runner) {
    return true;
  }
  return deleteGitHubRunnerById(githubToken, githubRepo, runner.id, runnerName);
}

async function terminateEcsTask(taskArn) {
  const cluster = process.env.ECS_CLUSTER || '';
  if (!cluster) {
    return false;
  }
  try {
    await getECSClient().send(new StopTaskCommand({
      cluster,
      task: taskArn,
      reason: 'Stale runner cleanup'
    }));
    logger.info('Stopped ECS task:', taskArn);
    return true;
  } catch (err) {
    if (err.name === 'InvalidParameterException' || err.message.includes('TaskNotFound')) {
      logger.info('Task already stopped or not found:', taskArn);
      return true;
    }
    logger.error('Failed to stop ECS task:', err.message);
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
    if (err.Code === 'InvalidInstanceID.NotFound' || err.Code === 'InvalidInstanceID.Malformed') {
      logger.info('Instance already terminated or not found:', instanceId);
      return true;
    }
    logger.error('Failed to terminate EC2 instance:', err.message);
    return false;
  }
}

function isOrphanedEcsTask(task, currentTime) {
  const tags = {};
  for (const t of task.tags || []) {
    tags[t.key] = t.value;
  }
  if (tags.Type !== WORKFLOW_RUNNER_TYPE_TAG || tags.ManagedBy !== ECS_MANAGED_BY_TAG) {
    return null;
  }
  const startedAt = task.startedAt;
  if (!startedAt) {
    return null;
  }
  const ageSeconds = (currentTime - new Date(startedAt).getTime()) / 1000;
  if (ageSeconds < ORPHAN_THRESHOLD_SECONDS) {
    return null;
  }
  return {
    task_arn: task.taskArn,
    age_seconds: Math.floor(ageSeconds),
    runner_name: tags.Name || '',
    github_repo: tags.GitHubRepo || ''
  };
}

async function getOrphanedEcsTasks() {
  const tasks = [];
  const cluster = process.env.ECS_CLUSTER || '';
  if (!cluster) {
    return tasks;
  }

  try {
    const ecs = getECSClient();
    const taskArns = [];

    // List all running tasks
    let nextToken;
    do {
      const response = await ecs.send(new ListTasksCommand({
        cluster,
        desiredStatus: 'RUNNING',
        nextToken
      }));
      taskArns.push(...(response.taskArns || []));
      nextToken = response.nextToken;
    } while (nextToken);

    if (taskArns.length === 0) {
      return tasks;
    }

    const currentTime = Date.now();

    // Describe tasks in batches of 100
    for (let i = 0; i < taskArns.length; i += 100) {
      const batch = taskArns.slice(i, i + 100);
      const response = await ecs.send(new DescribeTasksCommand({
        cluster,
        tasks: batch,
        include: ['TAGS']
      }));
      for (const task of response.tasks || []) {
        const orphaned = isOrphanedEcsTask(task, currentTime);
        if (orphaned) {
          tasks.push(orphaned);
        }
      }
    }
  } catch (err) {
    logger.error('Failed to get orphaned ECS tasks:', err.message);
  }
  return tasks;
}

async function getOrphanedEc2Instances() {
  const instances = [];
  const ec2ManagedByTag = process.env.EC2_MANAGED_BY_TAG || '';
  if (!ec2ManagedByTag) {
    return instances;
  }

  try {
    const response = await getEC2Client().send(new DescribeInstancesCommand({
      Filters: [
        { Name: 'tag:Type', Values: [WORKFLOW_RUNNER_TYPE_TAG] },
        { Name: 'tag:ManagedBy', Values: [ec2ManagedByTag] },
        { Name: 'instance-state-name', Values: ['pending', 'running'] }
      ]
    }));

    const currentTime = Date.now();
    for (const reservation of response.Reservations || []) {
      for (const instance of reservation.Instances || []) {
        const launchTime = instance.LaunchTime;
        if (launchTime) {
          const ageSeconds = (currentTime - new Date(launchTime).getTime()) / 1000;
          if (ageSeconds >= ORPHAN_THRESHOLD_SECONDS) {
            const tags = {};
            for (const t of instance.Tags || []) {
              tags[t.Key] = t.Value;
            }
            instances.push({
              instance_id: instance.InstanceId,
              age_seconds: Math.floor(ageSeconds),
              runner_name: tags.Name || '',
              github_repo: tags.GitHubRepo || ''
            });
          }
        }
      }
    }
  } catch (err) {
    logger.error('Failed to get orphaned EC2 instances:', err.message);
  }
  return instances;
}

async function hasRunningEc2ByName(runnerName) {
  const ec2ManagedByTag = process.env.EC2_MANAGED_BY_TAG || '';
  if (!ec2ManagedByTag) {
    return false;
  }
  try {
    const response = await getEC2Client().send(new DescribeInstancesCommand({
      Filters: [
        { Name: 'tag:Name', Values: [runnerName] },
        { Name: 'tag:ManagedBy', Values: [ec2ManagedByTag] },
        { Name: 'instance-state-name', Values: ['pending', 'running'] }
      ]
    }));
    for (const reservation of response.Reservations || []) {
      if ((reservation.Instances || []).length > 0) {
        return true;
      }
    }
  } catch (err) {
    logger.error('Failed to check EC2 instance by name', runnerName, ':', err.message);
  }
  return false;
}

function extractRunIdFromRunnerName(runnerName) {
  if (runnerName.startsWith('fargate-runner-')) {
    return runnerName.replace('fargate-runner-', '');
  }
  if (runnerName.startsWith('ec2-runner-')) {
    return runnerName.replace('ec2-runner-', '');
  }
  return '';
}

async function getEcsTaskArns(cluster) {
  const taskArns = [];
  const ecs = getECSClient();

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
  return taskArns;
}

async function checkTasksForRunId(cluster, taskArns, runId) {
  const ecs = getECSClient();
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
      if (tags.RunId === runId) {
        return true;
      }
    }
  }
  return false;
}

async function hasRunningEcsTaskByName(runnerName) {
  const cluster = process.env.ECS_CLUSTER || '';
  const runId = extractRunIdFromRunnerName(runnerName);
  if (!cluster || !runId) {
    return false;
  }
  try {
    const taskArns = await getEcsTaskArns(cluster);
    return await checkTasksForRunId(cluster, taskArns, runId);
  } catch (err) {
    logger.error('Failed to check ECS task by name', runnerName, ':', err.message);
  }
  return false;
}

async function runnerHasInfrastructure(runnerName) {
  const hasEc2 = await hasRunningEc2ByName(runnerName);
  const hasEcs = !hasEc2 && await hasRunningEcsTaskByName(runnerName);
  return hasEc2 || hasEcs;
}

async function cleanupOrphanedGitHubRunners(githubToken) {
  const counts = { github_cleaned: 0, errors: 0 };
  const githubRepo = process.env.GITHUB_REPO || '';
  if (!githubRepo || !githubToken) {
    counts.errors = 1;
    return counts;
  }

  const runners = await getAllGitHubRunners(githubToken, githubRepo);
  if (runners === null) {
    counts.errors = 1;
    return counts;
  }

  for (const runner of runners) {
    const status = runner.status || '';
    const runnerName = runner.name || '';
    const runnerId = runner.id;

    if (status !== 'offline') {
      continue;
    }
    if (!runnerName || !runnerId) {
      continue;
    }

    const hasInfra = await runnerHasInfrastructure(runnerName);
    if (hasInfra) {
      logger.info('Offline runner', runnerName, 'has infrastructure, skipping');
      continue;
    }

    logger.info('Cleaning up orphaned GitHub runner:', runnerName, `(id=${runnerId})`);
    if (await deleteGitHubRunnerById(githubToken, githubRepo, runnerId, runnerName)) {
      counts.github_cleaned++;
    } else {
      counts.errors++;
    }
  }

  logger.info(
    'Orphaned GitHub runner cleanup complete: cleaned=',
    counts.github_cleaned, ', errors=', counts.errors
  );
  return counts;
}

async function cleanupOrphanedResources(githubToken) {
  const counts = { ecs_cleaned: 0, ec2_cleaned: 0, errors: 0 };
  const githubRepo = process.env.GITHUB_REPO || '';

  // Clean orphaned ECS tasks
  const orphanedTasks = await getOrphanedEcsTasks();
  for (const task of orphanedTasks) {
    logger.info('Cleaning orphaned ECS task:', task.task_arn, `(age=${task.age_seconds}s)`);
    if (await terminateEcsTask(task.task_arn)) {
      counts.ecs_cleaned++;
      const runnerName = task.runner_name;
      const taskRepo = task.github_repo || githubRepo;
      if (runnerName && taskRepo && githubToken) {
        await deleteGitHubRunner(githubToken, taskRepo, runnerName);
      }
    } else {
      counts.errors++;
    }
  }

  // Clean orphaned EC2 instances
  const orphanedInstances = await getOrphanedEc2Instances();
  for (const instance of orphanedInstances) {
    logger.info('Cleaning orphaned EC2 instance:', instance.instance_id, `(age=${instance.age_seconds}s)`);
    if (await terminateEc2Instance(instance.instance_id)) {
      counts.ec2_cleaned++;
      const runnerName = instance.runner_name;
      const instanceRepo = instance.github_repo || githubRepo;
      if (runnerName && instanceRepo && githubToken) {
        await deleteGitHubRunner(githubToken, instanceRepo, runnerName);
      }
    } else {
      counts.errors++;
    }
  }

  logger.info(
    'Orphaned resource cleanup complete: ecs=', counts.ecs_cleaned,
    ', ec2=', counts.ec2_cleaned, ', errors=', counts.errors
  );
  return counts;
}

exports.handler = async (_event, _context) => {
  logger.info('Starting orphaned runner cleanup');
  const githubToken = await getGitHubToken();
  const orphanResult = await cleanupOrphanedResources(githubToken);
  const githubResult = await cleanupOrphanedGitHubRunners(githubToken);

  const result = {
    orphaned_ecs_cleaned: orphanResult.ecs_cleaned,
    orphaned_ec2_cleaned: orphanResult.ec2_cleaned,
    orphaned_github_cleaned: githubResult.github_cleaned,
    errors: orphanResult.errors + githubResult.errors
  };

  logger.info('Orphan cleanup complete:', JSON.stringify(result));
  return {
    statusCode: 200,
    body: JSON.stringify(result)
  };
};
