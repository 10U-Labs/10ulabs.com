async function listRunners(octokit, owner, repo) {
  return octokit.paginate(octokit.actions.listSelfHostedRunnersForRepo, {
    owner,
    repo,
    per_page: 100
  });
}

async function deleteRunner(octokit, owner, repo, runnerId) {
  await octokit.actions.deleteSelfHostedRunnerFromRepo({
    owner,
    repo,
    runner_id: runnerId
  });
}

async function deleteRunnerByName(octokit, owner, repo, name) {
  const runners = await listRunners(octokit, owner, repo);
  const runner = runners.find(r => r.name === name);
  if (runner) {
    await deleteRunner(octokit, owner, repo, runner.id);
  }
}

module.exports = { listRunners, deleteRunner, deleteRunnerByName };
