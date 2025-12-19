const { getGitHubToken, clearTokenCache } = require('./github_pat_auth');
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
