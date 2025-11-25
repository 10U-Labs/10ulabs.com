def test_backend_tf_file_exists(bootstrap_dir):
    assert (bootstrap_dir / "backend.tf").exists()


def test_providers_tf_file_exists(bootstrap_dir):
    assert (bootstrap_dir / "providers.tf").exists()


def test_variables_tf_file_exists(bootstrap_dir):
    assert (bootstrap_dir / "variables.tf").exists()


def test_outputs_tf_file_exists(bootstrap_dir):
    assert (bootstrap_dir / "outputs.tf").exists()


def test_state_tf_file_exists(bootstrap_dir):
    assert (bootstrap_dir / "state.tf").exists()


def test_cloudtrail_tf_file_exists(bootstrap_dir):
    assert (bootstrap_dir / "cloudtrail.tf").exists()


def test_oidc_tf_file_exists(bootstrap_dir):
    assert (bootstrap_dir / "oidc.tf").exists()


def test_domain_tf_file_exists(bootstrap_dir):
    assert (bootstrap_dir / "domain.tf").exists()


def test_gmail_tf_file_exists(bootstrap_dir):
    assert (bootstrap_dir / "gmail.tf").exists()


def test_cloudtrail_module_exists(bootstrap_dir):
    assert (bootstrap_dir / "modules" / "cloudtrail" / "main.tf").exists()


def test_github_oidc_module_exists(bootstrap_dir):
    assert (bootstrap_dir / "modules" / "github-oidc" / "main.tf").exists()


def test_domain_module_exists(bootstrap_dir):
    assert (bootstrap_dir / "modules" / "domain" / "main.tf").exists()


def test_central_logs_tf_file_exists(bootstrap_dir):
    assert (bootstrap_dir / "central_logs.tf").exists()


def test_shared_tf_file_exists(bootstrap_dir):
    assert (bootstrap_dir / "shared.tf").exists()


def test_locals_tf_file_exists(bootstrap_dir):
    assert (bootstrap_dir / "locals.tf").exists()


def test_github_pat_tf_file_exists(bootstrap_dir):
    assert (bootstrap_dir / "github_pat.tf").exists()


def test_central_logs_module_exists(bootstrap_dir):
    assert (bootstrap_dir / "modules" / "central_logs" / "main.tf").exists()
