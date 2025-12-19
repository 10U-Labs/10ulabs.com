const https = require('https');
const { getSSMClient } = require('/opt/nodejs/clients/ssm');
const { getEC2Client } = require('/opt/nodejs/clients/ec2');
const { GetParameterCommand } = require('@aws-sdk/client-ssm');
const { SNSClient, PublishCommand } = require('@aws-sdk/client-sns');

let snsClient = null;
function getSNSClient() {
  if (!snsClient) {
    snsClient = new SNSClient({});
  }
  return snsClient;
}
const { DescribeSubnetsCommand, DescribeSecurityGroupsCommand } = require('@aws-sdk/client-ec2');

const logger = {
  info: (...args) => console.log('[INFO]', ...args),
  warn: (...args) => console.warn('[WARN]', ...args),
  error: (...args) => console.error('[ERROR]', ...args)
};

async function isResourceInManagedVpc(resourceId, resourceType) {
  const managedVpcId = process.env.MANAGED_VPC_ID || '';
  if (!managedVpcId) {
    return true;
  }

  const ec2 = getEC2Client();
  try {
    if (resourceType === 'AWS::EC2::VPC') {
      return resourceId === managedVpcId;
    }

    if (resourceType === 'AWS::EC2::Subnet') {
      const response = await ec2.send(new DescribeSubnetsCommand({
        SubnetIds: [resourceId]
      }));
      const subnets = response.Subnets || [];
      return subnets.length > 0 && subnets[0].VpcId === managedVpcId;
    }

    if (resourceType === 'AWS::EC2::SecurityGroup') {
      const response = await ec2.send(new DescribeSecurityGroupsCommand({
        GroupIds: [resourceId]
      }));
      const groups = response.SecurityGroups || [];
      if (groups.length > 0) {
        const group = groups[0];
        const isDefault = group.GroupName === 'default';
        const isInVpc = group.VpcId === managedVpcId;
        return isInVpc && !isDefault;
      }
      return false;
    }
  } catch (err) {
    logger.warn('Failed to check resource VPC:', err.message);
    return false;
  }

  return true;
}

async function getGitHubToken() {
  const parameterName = process.env.GITHUB_TOKEN_PARAMETER_NAME;
  if (!parameterName) {
    logger.error('GITHUB_TOKEN_PARAMETER_NAME not set');
    return '';
  }
  try {
    const response = await getSSMClient().send(new GetParameterCommand({
      Name: parameterName,
      WithDecryption: true
    }));
    return response.Parameter?.Value || '';
  } catch (err) {
    logger.error('Failed to retrieve GitHub token:', err.message);
    return '';
  }
}

function triggerApiWorkflow(githubToken) {
  return new Promise((resolve) => {
    const githubRepo = process.env.GITHUB_REPO;
    const workflowFile = 'api_backend.yml';
    const payload = {
      ref: 'main',
      inputs: { github_hosted: 'true' }
    };

    const options = {
      hostname: 'api.github.com',
      path: `/repos/${githubRepo}/actions/workflows/${workflowFile}/dispatches`,
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${githubToken}`,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'Content-Type': 'application/json',
        'User-Agent': 'DriftRecovery/1.0'
      }
    };

    const req = https.request(options, (res) => {
      if (res.statusCode === 204) {
        resolve({ success: true, message: 'Workflow triggered' });
      } else {
        resolve({ success: false, error: `Unexpected status: ${res.statusCode}` });
      }
    });

    req.on('error', (err) => {
      logger.error('Failed to trigger workflow:', err.message);
      resolve({ success: false, error: err.message });
    });

    req.write(JSON.stringify(payload));
    req.end();
  });
}

async function sendNotification(subject, message) {
  const snsTopicArn = process.env.SNS_TOPIC_ARN;
  if (!snsTopicArn) {
    logger.warn('SNS_TOPIC_ARN not configured, skipping notification');
    return;
  }
  try {
    await getSNSClient().send(new PublishCommand({
      TopicArn: snsTopicArn,
      Subject: subject,
      Message: message
    }));
    logger.info('Notification sent:', subject);
  } catch (err) {
    logger.error('Failed to send notification:', err.message);
  }
}

function extractEventFromSqs(event) {
  const records = event.Records || [];
  if (records.length > 0) {
    const body = records[0].body || '{}';
    return JSON.parse(body);
  }
  return event;
}

function formatDriftDetails(triggerEvent) {
  const ruleName = triggerEvent.configRuleName || 'Unknown';
  const resourceType = triggerEvent.resourceType || 'Unknown';
  const resourceId = triggerEvent.resourceId || 'Unknown';
  const awsRegion = triggerEvent.awsRegion || 'Unknown';

  return {
    rule_name: ruleName,
    resource_type: resourceType,
    resource_id: resourceId,
    aws_region: awsRegion,
    summary: `${resourceType} (${resourceId}) in ${awsRegion}`
  };
}

exports.handler = async (event, _context) => {
  logger.info('Received SQS event:', JSON.stringify(event));
  const triggerEvent = extractEventFromSqs(event);
  const drift = formatDriftDetails(triggerEvent);
  logger.info('Drift detected:', drift.summary);

  const isInManagedVpc = await isResourceInManagedVpc(drift.resource_id, drift.resource_type);
  if (!isInManagedVpc) {
    logger.info('Resource', drift.resource_id, 'is not in managed VPC, skipping');
    return { statusCode: 200, body: 'Resource not in managed VPC, skipping' };
  }

  const githubRepo = process.env.GITHUB_REPO || '';
  const githubToken = await getGitHubToken();

  if (!githubToken) {
    const errorMsg = 'Failed to retrieve GitHub token';
    logger.error(errorMsg);
    await sendNotification(
      `Drift Recovery FAILED: ${drift.rule_name}`,
      `Infrastructure drift was detected.\n\n` +
      `Resource: ${drift.summary}\n` +
      `Rule: ${drift.rule_name}\n\n` +
      `FAILED to trigger recovery workflow: ${errorMsg}\n\n` +
      `MANUAL INTERVENTION REQUIRED`
    );
    return { statusCode: 500, body: errorMsg };
  }

  const result = await triggerApiWorkflow(githubToken);

  if (result.success) {
    logger.info('Successfully triggered api_backend.yml workflow for drift recovery');
    await sendNotification(
      `Drift Recovery Triggered: ${drift.rule_name}`,
      `Infrastructure drift was detected.\n\n` +
      `Resource: ${drift.summary}\n` +
      `Rule: ${drift.rule_name}\n\n` +
      `Automatically triggered api_backend.yml workflow ` +
      `to recover infrastructure.\n\n` +
      `Monitor the workflow at: https://github.com/${githubRepo}/actions`
    );
    return { statusCode: 200, body: 'Recovery workflow triggered' };
  }

  logger.error('Failed to trigger workflow:', result.error);
  await sendNotification(
    `Drift Recovery FAILED: ${drift.rule_name}`,
    `Infrastructure drift was detected.\n\n` +
    `Resource: ${drift.summary}\n` +
    `Rule: ${drift.rule_name}\n\n` +
    `FAILED to trigger recovery workflow: ${result.error}\n\n` +
    `MANUAL INTERVENTION REQUIRED`
  );
  return { statusCode: 500, body: 'Failed to trigger recovery' };
};
