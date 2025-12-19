const { CloudWatchClient } = require('@aws-sdk/client-cloudwatch');

let cloudWatchClient = null;

function getCloudWatchClient() {
  if (!cloudWatchClient) {
    cloudWatchClient = new CloudWatchClient({});
  }
  return cloudWatchClient;
}

function clearClient() {
  cloudWatchClient = null;
}

module.exports = {
  getCloudWatchClient,
  clearClient
};
