const { ECSClient } = require('@aws-sdk/client-ecs');
const { EC2Client } = require('@aws-sdk/client-ec2');
const { SQSClient } = require('@aws-sdk/client-sqs');
const { DynamoDBClient } = require('@aws-sdk/client-dynamodb');
const { CloudWatchClient } = require('@aws-sdk/client-cloudwatch');
const { SNSClient } = require('@aws-sdk/client-sns');
const { SSMClient } = require('@aws-sdk/client-ssm');
const { S3Client } = require('@aws-sdk/client-s3');

const clients = {
  ecs: null,
  ec2: null,
  sqs: null,
  dynamodb: null,
  cloudwatch: null,
  sns: null,
  ssm: null,
  s3: null
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

function getSQSClient() {
  if (!clients.sqs) {
    clients.sqs = new SQSClient({});
  }
  return clients.sqs;
}

function getDynamoDBClient() {
  if (!clients.dynamodb) {
    clients.dynamodb = new DynamoDBClient({});
  }
  return clients.dynamodb;
}

function getCloudWatchClient() {
  if (!clients.cloudwatch) {
    clients.cloudwatch = new CloudWatchClient({});
  }
  return clients.cloudwatch;
}

function getSNSClient() {
  if (!clients.sns) {
    clients.sns = new SNSClient({});
  }
  return clients.sns;
}

function getSSMClient() {
  if (!clients.ssm) {
    clients.ssm = new SSMClient({});
  }
  return clients.ssm;
}

function getS3Client() {
  if (!clients.s3) {
    clients.s3 = new S3Client({});
  }
  return clients.s3;
}

function clearClients() {
  for (const key of Object.keys(clients)) {
    clients[key] = null;
  }
}

module.exports = {
  getECSClient,
  getEC2Client,
  getSQSClient,
  getDynamoDBClient,
  getCloudWatchClient,
  getSNSClient,
  getSSMClient,
  getS3Client,
  clearClients
};
