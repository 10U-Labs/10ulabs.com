const { EC2Client } = require('@aws-sdk/client-ec2');

let ec2Client = null;

function getEC2Client() {
  if (!ec2Client) {
    ec2Client = new EC2Client({});
  }
  return ec2Client;
}

function clearClient() {
  ec2Client = null;
}

module.exports = {
  getEC2Client,
  clearClient
};
