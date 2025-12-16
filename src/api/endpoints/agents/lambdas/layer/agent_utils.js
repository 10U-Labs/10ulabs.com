const { BedrockAgentRuntimeClient, InvokeAgentCommand } = require('@aws-sdk/client-bedrock-agent-runtime');

const logger = {
  info: (...args) => console.log('[INFO]', ...args),
  error: (...args) => console.error('[ERROR]', ...args),
  warn: (...args) => console.warn('[WARN]', ...args)
};

async function invokeAgent(agentType, payload) {
  const client = new BedrockAgentRuntimeClient({
    region: process.env.AWS_REGION_NAME || 'us-east-2'
  });

  const agentArn = process.env.AGENT_RUNTIME_ARN;
  if (!agentArn) {
    throw new Error('AGENT_RUNTIME_ARN environment variable not set');
  }

  payload.agent_type = agentType;

  const command = new InvokeAgentCommand({
    agentRuntimeArn: agentArn,
    payload: JSON.stringify(payload),
    contentType: 'application/json'
  });

  const response = await client.send(command);

  const content = [];
  if (response.response) {
    for await (const chunk of response.response) {
      if (chunk.chunk?.bytes) {
        content.push(new TextDecoder().decode(chunk.chunk.bytes));
      }
    }
  }

  return content.length > 0 ? JSON.parse(content.join('')) : {};
}

async function handleRecommendation(result, githubToken) {
  const recommendation = result.recommendation;

  if (recommendation === 'create_agent') {
    let createRequest = result.create_agent_request || {};
    if (typeof createRequest === 'string') {
      createRequest = { request: createRequest };
    }

    createRequest.github_token = githubToken;
    logger.info('Routing to creator_of_agents:', (createRequest.request || '').slice(0, 100));

    const creatorResult = await invokeAgent('creator_of_agents', createRequest);
    return {
      original_result: result,
      creator_result: creatorResult,
      routed_to: 'creator_of_agents'
    };
  }

  return result;
}

async function processSqsRecords(event, githubToken, processor) {
  logger.info('Received SQS event with', (event.Records || []).length, 'records');

  const results = [];
  const failedMessageIds = [];

  for (const record of event.Records || []) {
    const messageId = record.messageId || 'unknown';
    try {
      const body = JSON.parse(record.body || '{}');
      const result = await processor(body, githubToken);
      results.push({ messageId, ...result });
    } catch (err) {
      logger.error('Error processing message', messageId, ':', err.message);
      console.error(err.stack);
      failedMessageIds.push(messageId);
      results.push({ messageId, status: 'error', error: err.message });
    }
  }

  const response = {
    statusCode: 200,
    body: JSON.stringify({ processed: results.length, results })
  };

  if (failedMessageIds.length > 0) {
    response.batchItemFailures = failedMessageIds.map(id => ({ itemIdentifier: id }));
  }

  return response;
}

module.exports = { invokeAgent, handleRecommendation, processSqsRecords };
