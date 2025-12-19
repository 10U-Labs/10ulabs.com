const { SSMClient } = require('@aws-sdk/client-ssm');

let ssmClient = null;

function getSSMClient() {
  if (!ssmClient) {
    ssmClient = new SSMClient({});
  }
  return ssmClient;
}

function clearClient() {
  ssmClient = null;
}

module.exports = {
  getSSMClient,
  clearClient
};
