const https = require('https');
const { getGitHubToken, invokeAgent, handleRecommendation, processSqsRecords } = require('/opt/nodejs/agents-layer');

const logger = {
  info: (...args) => console.log('[INFO]', ...args),
  warn: (...args) => console.warn('[WARN]', ...args),
  error: (...args) => console.error('[ERROR]', ...args)
};

const GITHUB_ORG = process.env.GITHUB_ORG || '10U-Labs-LLC';
const GITHUB_REPO = process.env.GITHUB_REPO || '10ulabs.com';

function githubApiRequest(endpoint, token) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: 'api.github.com',
      path: endpoint,
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': 'AgentScanner/1.0'
      }
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => { data += chunk; });
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(JSON.parse(data));
        } else {
          reject(new Error(`GitHub API error ${res.statusCode}: ${data}`));
        }
      });
    });

    req.on('error', reject);
    req.end();
  });
}

async function getUnresolvedFailures(token) {
  const endpoint = `/repos/${GITHUB_ORG}/${GITHUB_REPO}/actions/runs?status=failure&per_page=50`;
  const response = await githubApiRequest(endpoint, token);

  const unresolved = [];
  for (const run of response.workflow_runs || []) {
    const workflowId = run.workflow_id;
    const headBranch = run.head_branch;

    const checkEndpoint = `/repos/${GITHUB_ORG}/${GITHUB_REPO}/actions/workflows/${workflowId}/runs?branch=${headBranch}&status=success&per_page=1`;
    try {
      const successResponse = await githubApiRequest(checkEndpoint, token);
      const successRuns = successResponse.workflow_runs || [];

      if (successRuns.length > 0) {
        const latestSuccess = successRuns[0];
        if (latestSuccess.created_at > run.created_at) {
          continue;
        }
      }

      const workflowName = (run.name || '').toLowerCase();
      if (workflowName.includes('agent')) {
        continue;
      }

      unresolved.push(run);
    } catch {
      continue;
    }
  }

  return unresolved;
}

function buildAgentPayloadFromRun(run, githubToken) {
  return {
    github_token: githubToken,
    owner: GITHUB_ORG,
    repo: GITHUB_REPO,
    run_id: run.id,
    workflow_name: run.name,
    workflow_path: run.path || '',
    head_sha: run.head_sha,
    head_branch: run.head_branch
  };
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function processUnresolvedFailure(run, githubToken) {
  const runId = run.id;
  logger.info('Processing unresolved failure:', run.name, '(run', runId, ')');

  const initialDelay = Math.random() * 30000;
  logger.info(`Initial delay of ${(initialDelay / 1000).toFixed(1)}s before processing run ${runId}`);
  await sleep(initialDelay);

  const maxAttempts = 7;
  for (let attempt = 0; attempt < maxAttempts; attempt++) {
    try {
      const agentPayload = buildAgentPayloadFromRun(run, githubToken);
      let result = await invokeAgent('troubleshooter_of_workflows', agentPayload);
      result = await handleRecommendation(result, githubToken);

      return { run_id: runId, status: 'processed', result };
    } catch (err) {
      if (attempt < maxAttempts - 1) {
        const backoff = Math.pow(2, 4 + attempt) * 1000;
        logger.warn(
          `Attempt ${attempt + 1}/${maxAttempts} failed for run ${runId}, retrying in ${backoff / 1000}s:`,
          err.message
        );
        await sleep(backoff);
      } else {
        logger.error(`All ${maxAttempts} retries exhausted for run ${runId}:`, err.message);
        return { run_id: runId, status: 'error', error: err.message };
      }
    }
  }

  return { run_id: runId, status: 'error', error: 'Unknown error' };
}

async function runScan(githubToken, testMode = false) {
  logger.info('Running scheduled scan for unresolved workflow failures');

  if (testMode) {
    logger.info('Test mode enabled, skipping actual scan');
    return { mode: 'scheduled', processed: 0, test_mode: true };
  }

  const unresolved = await getUnresolvedFailures(githubToken);
  logger.info('Found', unresolved.length, 'unresolved failures');

  const results = [];
  for (const run of unresolved) {
    const result = await processUnresolvedFailure(run, githubToken);
    results.push(result);
  }

  return { mode: 'scheduled', processed: results.length, results };
}

async function processRecord(body, githubToken) {
  const testMode = body.test_mode || false;
  return runScan(githubToken, testMode);
}

exports.handler = async (event, _context) => {
  const githubToken = await getGitHubToken();
  return processSqsRecords(event, githubToken, processRecord);
};
