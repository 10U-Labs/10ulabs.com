"""Unit tests for diagnostics endpoint variables.tf configuration."""


def test_variables_file_exists(diagnostics_src_dir):
    """Verify variables.tf file exists."""
    assert (diagnostics_src_dir / "variables.tf").exists()


def test_variables_has_diagnostics_handler_function_name(diagnostics_src_dir):
    """Verify diagnostics_handler_function_name variable is defined."""
    content = (diagnostics_src_dir / "variables.tf").read_text()
    assert 'variable "diagnostics_handler_function_name"' in content


def test_variables_diagnostics_handler_function_name_type(diagnostics_src_dir):
    """Verify diagnostics_handler_function_name is type string."""
    content = (diagnostics_src_dir / "variables.tf").read_text()
    assert "type = string" in content


def test_variables_has_diagnostics_handler_log_group_name(diagnostics_src_dir):
    """Verify diagnostics_handler_log_group_name variable is defined."""
    content = (diagnostics_src_dir / "variables.tf").read_text()
    assert 'variable "diagnostics_handler_log_group_name"' in content


def test_variables_contains_exactly_two_variables(diagnostics_src_dir):
    """Verify variables.tf contains exactly two variables."""
    content = (diagnostics_src_dir / "variables.tf").read_text()
    variable_count = content.count('variable "')
    assert variable_count == 2, f"Expected 2 variables, found {variable_count}"
