const { getGitHubToken, invokeAgent, handleRecommendation, processSqsRecords } = require('/opt/nodejs/agents-layer');

const logger = {
  info: (...args) => console.log('[INFO]', ...args)
};

async function processInvocation(payload, githubToken) {
  const agentType = payload.agent_type;

  if (!agentType) {
    return { status: 'error', error: 'agent_type is required for direct invocation' };
  }

  if (!payload.github_token) {
    payload.github_token = githubToken;
  }

  logger.info('Direct invocation of agent:', agentType);
  let result = await invokeAgent(agentType, payload);
  result = await handleRecommendation(result, githubToken);

  return { status: 'processed', agent_type: agentType, result };
}

async function processRecord(body, githubToken) {
  let payload = body.body || body;
  if (typeof payload === 'string') {
    payload = JSON.parse(payload);
  }
  return processInvocation(payload, githubToken);
}

exports.handler = async (event, _context) => {
  const githubToken = await getGitHubToken();
  return processSqsRecords(event, githubToken, processRecord);
};
