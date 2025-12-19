const { ECSClient } = require('@aws-sdk/client-ecs');
const { EC2Client } = require('@aws-sdk/client-ec2');
const { CloudWatchClient } = require('@aws-sdk/client-cloudwatch');
const { SSMClient } = require('@aws-sdk/client-ssm');

const clients = {
  ecs: null,
  ec2: null,
  cloudwatch: null,
  ssm: null
};

function getECSClient() {
  if (!clients.ecs) {
    clients.ecs = new ECSClient({});
  }
  return clients.ecs;
}

function getEC2Client() {
  if (!clients.ec2) {
    clients.ec2 = new EC2Client({});
  }
  return clients.ec2;
}

function getCloudWatchClient() {
  if (!clients.cloudwatch) {
    clients.cloudwatch = new CloudWatchClient({});
  }
  return clients.cloudwatch;
}

function getSSMClient() {
  if (!clients.ssm) {
    clients.ssm = new SSMClient({});
  }
  return clients.ssm;
}

function clearClients() {
  for (const key of Object.keys(clients)) {
    clients[key] = null;
  }
}

module.exports = {
  getECSClient,
  getEC2Client,
  getCloudWatchClient,
  getSSMClient,
  clearClients
};
