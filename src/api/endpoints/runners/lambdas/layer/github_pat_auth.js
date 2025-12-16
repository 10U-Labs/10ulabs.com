const { SSMClient, GetParameterCommand } = require('@aws-sdk/client-ssm');

let tokenCache = { value: null };
let ssmClient = null;

function getSSMClient() {
  if (!ssmClient) {
    ssmClient = new SSMClient({});
  }
  return ssmClient;
}

async function getGitHubToken() {
  if (tokenCache.value) {
    return tokenCache.value;
  }

  const parameterName = process.env.GITHUB_TOKEN_SECRET_NAME;
  if (!parameterName) {
    return '';
  }

  try {
    const response = await getSSMClient().send(new GetParameterCommand({
      Name: parameterName,
      WithDecryption: true
    }));
    const token = response.Parameter?.Value || '';
    tokenCache.value = token;
    return token;
  } catch (err) {
    console.error('[ERROR] Failed to retrieve GitHub token:', err.message);
    return '';
  }
}

function clearTokenCache() {
  tokenCache.value = null;
}

module.exports = { getGitHubToken, clearTokenCache, getSSMClient };
