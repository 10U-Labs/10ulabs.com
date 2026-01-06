"""Unit tests for health endpoint variables.tf configuration."""


def test_variables_file_exists(health_src_dir):
    """Verify variables.tf file exists."""
    assert (health_src_dir / "variables.tf").exists()


def test_variables_health_handler_function_name_exists(health_src_dir):
    """Verify health_handler_function_name variable is defined."""
    content = (health_src_dir / "variables.tf").read_text()
    assert 'variable "health_handler_function_name"' in content


def test_variables_health_handler_function_name_type_string(health_src_dir):
    """Verify health_handler_function_name is type string."""
    content = (health_src_dir / "variables.tf").read_text()
    assert "type = string" in content


def test_variables_health_handler_log_group_name_exists(health_src_dir):
    """Verify health_handler_log_group_name variable is defined."""
    content = (health_src_dir / "variables.tf").read_text()
    assert 'variable "health_handler_log_group_name"' in content


def test_variables_has_two_variables(health_src_dir):
    """Verify variables.tf contains exactly two variables."""
    content = (health_src_dir / "variables.tf").read_text()
    variable_count = content.count('variable "')
    assert variable_count == 2, f"Expected 2 variables, found {variable_count}"
