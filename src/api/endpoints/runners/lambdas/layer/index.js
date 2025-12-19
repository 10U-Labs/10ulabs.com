const { getGitHubToken, clearTokenCache } = require('./github_pat_auth');
const {
  getECSClient,
  getEC2Client,
  getCloudWatchClient,
  getSSMClient,
  clearClients
} = require('./aws_clients');
const {
  parseLabels,
  validateLabels,
  getInstanceType,
  getEcsConfig,
  getTaskArchitecture,
  isSpot,
  getRunnerIdNumber,
  LabelParseError,
  LabelValidationError
} = require('./runner_labels');
const {
  getMessageAttribute,
  isWebhookIngressQueue,
  IngressHandler
} = require('./webhook_ingress');

module.exports = {
  // GitHub PAT auth
  getGitHubToken,
  clearTokenCache,

  // AWS clients
  getECSClient,
  getEC2Client,
  getCloudWatchClient,
  getSSMClient,
  clearClients,

  // Runner labels
  parseLabels,
  validateLabels,
  getInstanceType,
  getEcsConfig,
  getTaskArchitecture,
  isSpot,
  getRunnerIdNumber,
  LabelParseError,
  LabelValidationError,

  // Webhook ingress
  getMessageAttribute,
  isWebhookIngressQueue,
  IngressHandler
};
