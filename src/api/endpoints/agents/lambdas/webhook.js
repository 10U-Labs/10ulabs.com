const { getGitHubToken, invokeAgent, handleRecommendation, processSqsRecords } = require('/opt/nodejs/agents-layer');

const logger = {
  info: (...args) => console.log('[INFO]', ...args)
};

function parseWebhookPayload(body) {
  if (body === null || body === undefined || body === '') {
    return {};
  }
  if (typeof body === 'string') {
    return JSON.parse(body);
  }
  return body || {};
}

function shouldSkipEvent(payload) {
  const action = payload.action;
  const workflowRun = payload.workflow_run || {};

  if (action !== 'completed') {
    return { skip: true, reason: 'Ignoring non-completed event' };
  }

  const conclusion = workflowRun.conclusion;
  if (conclusion !== 'failure') {
    return { skip: true, reason: `Ignoring ${conclusion} workflow` };
  }

  const workflowName = workflowRun.name || '';
  if (workflowName.toLowerCase().includes('agent')) {
    return { skip: true, reason: 'Ignoring agent workflow' };
  }

  return { skip: false, reason: '' };
}

function buildAgentPayload(payload, githubToken) {
  const workflowRun = payload.workflow_run || {};
  const repo = payload.repository || {};

  return {
    github_token: githubToken,
    owner: (repo.owner || {}).login,
    repo: repo.name,
    run_id: workflowRun.id,
    workflow_name: workflowRun.name,
    workflow_path: workflowRun.path || '',
    head_sha: workflowRun.head_sha,
    head_branch: workflowRun.head_branch
  };
}

async function processWebhookEvent(payload, githubToken) {
  const { skip, reason } = shouldSkipEvent(payload);

  if (skip) {
    return { status: 'skipped', reason };
  }

  const workflowRun = payload.workflow_run || {};
  const repo = payload.repository || {};
  logger.info(
    'Processing failed workflow:',
    workflowRun.name,
    '(run', workflowRun.id, ') in',
    `${(repo.owner || {}).login}/${repo.name}`
  );

  const agentPayload = buildAgentPayload(payload, githubToken);
  let result = await invokeAgent('troubleshooter_of_workflows', agentPayload);
  result = await handleRecommendation(result, githubToken);

  logger.info('Agent result:', JSON.stringify(result, null, 2));

  return { status: 'processed', result };
}

async function processRecord(body, githubToken) {
  const payload = parseWebhookPayload(body.body || body);
  return processWebhookEvent(payload, githubToken);
}

exports.handler = async (event, _context) => {
  const githubToken = await getGitHubToken();
  return processSqsRecords(event, githubToken, processRecord);
};
