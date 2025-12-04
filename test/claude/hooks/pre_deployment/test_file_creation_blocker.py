def test_blocked_filenames_contains_eslintrc(file_creation_blocker):
    eslintrc_is_blocked = '.eslintrc' in file_creation_blocker.BLOCKED_FILENAMES
    assert eslintrc_is_blocked


def test_blocked_filenames_contains_eslintrc_json(file_creation_blocker):
    eslintrc_json_is_blocked = '.eslintrc.json' in file_creation_blocker.BLOCKED_FILENAMES
    assert eslintrc_json_is_blocked


def test_blocked_filenames_contains_eslint_config_js(file_creation_blocker):
    eslint_config_js_is_blocked = 'eslint.config.js' in file_creation_blocker.BLOCKED_FILENAMES
    assert eslint_config_js_is_blocked


def test_blocked_filenames_contains_pylintrc(file_creation_blocker):
    pylintrc_is_blocked = '.pylintrc' in file_creation_blocker.BLOCKED_FILENAMES
    assert pylintrc_is_blocked


def test_blocked_filenames_contains_flake8(file_creation_blocker):
    flake8_is_blocked = '.flake8' in file_creation_blocker.BLOCKED_FILENAMES
    assert flake8_is_blocked


def test_blocked_filenames_contains_prettierrc(file_creation_blocker):
    prettierrc_is_blocked = '.prettierrc' in file_creation_blocker.BLOCKED_FILENAMES
    assert prettierrc_is_blocked


def test_blocked_filenames_contains_prettierrc_json(file_creation_blocker):
    prettierrc_json_is_blocked = '.prettierrc.json' in file_creation_blocker.BLOCKED_FILENAMES
    assert prettierrc_json_is_blocked


def test_blocked_filenames_contains_stylelintrc(file_creation_blocker):
    stylelintrc_is_blocked = '.stylelintrc' in file_creation_blocker.BLOCKED_FILENAMES
    assert stylelintrc_is_blocked


def test_blocked_filenames_contains_hadolint_yaml(file_creation_blocker):
    hadolint_yaml_is_blocked = '.hadolint.yaml' in file_creation_blocker.BLOCKED_FILENAMES
    assert hadolint_yaml_is_blocked


def test_blocked_filenames_contains_tflint_hcl(file_creation_blocker):
    tflint_hcl_is_blocked = '.tflint.hcl' in file_creation_blocker.BLOCKED_FILENAMES
    assert tflint_hcl_is_blocked


def test_blocked_filenames_contains_rubocop_yml(file_creation_blocker):
    rubocop_yml_is_blocked = '.rubocop.yml' in file_creation_blocker.BLOCKED_FILENAMES
    assert rubocop_yml_is_blocked


def test_blocked_filenames_contains_mypy_ini(file_creation_blocker):
    mypy_ini_is_blocked = 'mypy.ini' in file_creation_blocker.BLOCKED_FILENAMES
    assert mypy_ini_is_blocked


def test_blocked_filenames_contains_ruff_toml(file_creation_blocker):
    ruff_toml_is_blocked = 'ruff.toml' in file_creation_blocker.BLOCKED_FILENAMES
    assert ruff_toml_is_blocked


def test_blocked_filenames_contains_shellcheckrc(file_creation_blocker):
    shellcheckrc_is_blocked = '.shellcheckrc' in file_creation_blocker.BLOCKED_FILENAMES
    assert shellcheckrc_is_blocked


def test_blocked_filenames_contains_yamllint(file_creation_blocker):
    yamllint_is_blocked = '.yamllint' in file_creation_blocker.BLOCKED_FILENAMES
    assert yamllint_is_blocked


def test_blocked_filenames_contains_markdownlint_json(file_creation_blocker):
    markdownlint_json_is_blocked = '.markdownlint.json' in file_creation_blocker.BLOCKED_FILENAMES
    assert markdownlint_json_is_blocked


def test_regular_python_file_is_not_blocked(file_creation_blocker):
    regular_python_file_is_allowed = 'main.py' not in file_creation_blocker.BLOCKED_FILENAMES
    assert regular_python_file_is_allowed


def test_regular_js_file_is_not_blocked(file_creation_blocker):
    regular_js_file_is_allowed = 'index.js' not in file_creation_blocker.BLOCKED_FILENAMES
    assert regular_js_file_is_allowed


def test_readme_file_is_not_blocked(file_creation_blocker):
    readme_file_is_allowed = 'README.md' not in file_creation_blocker.BLOCKED_FILENAMES
    assert readme_file_is_allowed


def test_package_json_is_not_blocked(file_creation_blocker):
    package_json_is_allowed = 'package.json' not in file_creation_blocker.BLOCKED_FILENAMES
    assert package_json_is_allowed
