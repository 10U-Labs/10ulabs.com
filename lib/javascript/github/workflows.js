async function getWorkflowRun(octokit, owner, repo, runId) {
  const { data } = await octokit.actions.getWorkflowRun({
    owner,
    repo,
    run_id: runId
  });
  return data;
}

async function cancelWorkflowRun(octokit, owner, repo, runId) {
  await octokit.actions.cancelWorkflowRun({
    owner,
    repo,
    run_id: runId
  });
}

async function dispatchWorkflow(octokit, owner, repo, workflowId, ref, inputs) {
  await octokit.actions.createWorkflowDispatch({
    owner,
    repo,
    workflow_id: workflowId,
    ref,
    inputs
  });
}

async function getWorkflowRunInfo(octokit, owner, repo, runId) {
  const run = await getWorkflowRun(octokit, owner, repo, runId);
  return {
    workflowId: String(run.workflow_id),
    headSha: run.head_sha,
    status: run.status
  };
}

async function createCheckRunAnnotation(octokit, owner, repo, headSha, title, summary) {
  await octokit.checks.create({
    owner,
    repo,
    name: 'Spot Interruption Handler',
    head_sha: headSha,
    status: 'completed',
    conclusion: 'neutral',
    output: {
      title,
      summary
    }
  });
}

module.exports = {
  getWorkflowRun,
  cancelWorkflowRun,
  dispatchWorkflow,
  getWorkflowRunInfo,
  createCheckRunAnnotation
};
