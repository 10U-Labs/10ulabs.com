const { ECSClient } = require('@aws-sdk/client-ecs');

let ecsClient = null;

function getECSClient() {
  if (!ecsClient) {
    ecsClient = new ECSClient({});
  }
  return ecsClient;
}

function clearClient() {
  ecsClient = null;
}

module.exports = {
  getECSClient,
  clearClient
};
