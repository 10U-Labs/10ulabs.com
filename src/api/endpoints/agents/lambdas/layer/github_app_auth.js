const { SSMClient, GetParameterCommand } = require('@aws-sdk/client-ssm');
const jwt = require('jsonwebtoken');
const https = require('https');

// Cache for installation token (valid for ~1 hour)
let tokenCache = { token: null, expiresAt: 0 };

// Default SSM parameter paths
const DEFAULT_SSM_APP_ID = '/github/app/id';
const DEFAULT_SSM_INSTALLATION_ID = '/github/app/installation_id';
const DEFAULT_SSM_PRIVATE_KEY = '/github/app/private_key';

async function getSSMParameter(name) {
  const ssm = new SSMClient({ region: process.env.AWS_REGION_NAME || 'us-east-2' });
  const response = await ssm.send(new GetParameterCommand({
    Name: name,
    WithDecryption: true
  }));
  return response.Parameter.Value;
}

function generateJWT(appId, privateKey) {
  const now = Math.floor(Date.now() / 1000);
  const payload = {
    iat: now - 60,  // Issued 60 seconds ago to account for clock drift
    exp: now + 600, // Expires in 10 minutes
    iss: appId
  };
  return jwt.sign(payload, privateKey, { algorithm: 'RS256' });
}

function getInstallationTokenFromGitHub(appJwt, installationId) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.github.com',
      path: `/app/installations/${installationId}/access_tokens`,
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${appJwt}`,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': '10ULabsBot/1.0'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          const json = JSON.parse(data);
          resolve(json.token);
        } else {
          reject(new Error(`GitHub API error ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

async function getGitHubToken() {
  const now = Date.now() / 1000;

  // Return cached token if still valid (with 5 min buffer)
  if (tokenCache.token && tokenCache.expiresAt > now + 300) {
    return tokenCache.token;
  }

  // Get GitHub App credentials from SSM
  const appId = await getSSMParameter(
    process.env.SSM_GITHUB_APP_ID || DEFAULT_SSM_APP_ID
  );
  const installationId = await getSSMParameter(
    process.env.SSM_GITHUB_APP_INSTALL_ID || DEFAULT_SSM_INSTALLATION_ID
  );
  const privateKey = await getSSMParameter(
    process.env.SSM_GITHUB_APP_PRIVATE_KEY || DEFAULT_SSM_PRIVATE_KEY
  );

  // Generate JWT and get installation token
  const appJwt = generateJWT(appId, privateKey);
  const token = await getInstallationTokenFromGitHub(appJwt, installationId);

  // Cache for 55 minutes (tokens are valid for 1 hour)
  tokenCache.token = token;
  tokenCache.expiresAt = now + 3300;

  return token;
}

module.exports = { getGitHubToken };
