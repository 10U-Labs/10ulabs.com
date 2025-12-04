def test_is_code_file_returns_true_for_py(code_quality_checker):
    py_file_is_code = code_quality_checker.is_code_file('main.py')
    assert py_file_is_code


def test_is_code_file_returns_true_for_ts(code_quality_checker):
    ts_file_is_code = code_quality_checker.is_code_file('index.ts')
    assert ts_file_is_code


def test_is_code_file_returns_true_for_tsx(code_quality_checker):
    tsx_file_is_code = code_quality_checker.is_code_file('App.tsx')
    assert tsx_file_is_code


def test_is_code_file_returns_true_for_js(code_quality_checker):
    js_file_is_code = code_quality_checker.is_code_file('index.js')
    assert js_file_is_code


def test_is_code_file_returns_true_for_jsx(code_quality_checker):
    jsx_file_is_code = code_quality_checker.is_code_file('App.jsx')
    assert jsx_file_is_code


def test_is_code_file_returns_false_for_md(code_quality_checker):
    md_file_is_not_code = not code_quality_checker.is_code_file('README.md')
    assert md_file_is_not_code


def test_is_code_file_returns_false_for_yaml(code_quality_checker):
    yaml_file_is_not_code = not code_quality_checker.is_code_file('config.yaml')
    assert yaml_file_is_not_code


def test_check_python_detects_multiple_returns(code_quality_checker):
    content = '''
def foo(x):
    if x > 0:
        return 1
    return 0
'''
    violations = code_quality_checker.check_python(content)
    multiple_returns_is_detected = len(violations) > 0
    assert multiple_returns_is_detected


def test_check_python_allows_single_return(code_quality_checker):
    content = '''
def foo(x):
    result = 0
    if x > 0:
        result = 1
    return result
'''
    violations = code_quality_checker.check_python(content)
    single_return_is_allowed = len(violations) == 0
    assert single_return_is_allowed


def test_check_python_detects_break_statement(code_quality_checker):
    content = '''
def foo(items):
    for item in items:
        if item == 'stop':
            break
    return items
'''
    violations = code_quality_checker.check_python(content)
    break_statement_is_detected = len(violations) > 0
    assert break_statement_is_detected


def test_check_python_detects_continue_statement(code_quality_checker):
    content = '''
def foo(items):
    result = []
    for item in items:
        if item == 'skip':
            continue
        result.append(item)
    return result
'''
    violations = code_quality_checker.check_python(content)
    continue_statement_is_detected = len(violations) > 0
    assert continue_statement_is_detected


def test_check_python_allows_function_without_break_continue(code_quality_checker):
    content = '''
def foo(items):
    result = [item for item in items if item != 'skip']
    return result
'''
    violations = code_quality_checker.check_python(content)
    function_without_break_continue_is_allowed = len(violations) == 0
    assert function_without_break_continue_is_allowed


def test_check_javascript_typescript_detects_break(code_quality_checker):
    content = '''
function foo(items) {
  for (const item of items) {
    if (item === 'stop') {
      break;
    }
  }
}
'''
    violations = code_quality_checker.check_javascript_typescript(content)
    js_break_is_detected = len(violations) > 0
    assert js_break_is_detected


def test_check_javascript_typescript_detects_continue(code_quality_checker):
    content = '''
function foo(items) {
  for (const item of items) {
    if (item === 'skip') {
      continue;
    }
    console.log(item);
  }
}
'''
    violations = code_quality_checker.check_javascript_typescript(content)
    js_continue_is_detected = len(violations) > 0
    assert js_continue_is_detected


def test_check_javascript_typescript_allows_code_without_break_continue(code_quality_checker):
    content = '''
function foo(items) {
  const result = items.filter(item => item !== 'skip');
  return result;
}
'''
    violations = code_quality_checker.check_javascript_typescript(content)
    js_code_without_break_continue_is_allowed = len(violations) == 0
    assert js_code_without_break_continue_is_allowed


def test_check_content_skips_non_code_files(code_quality_checker):
    content = 'break; continue;'
    violations = code_quality_checker.check_content(content, 'README.md')
    non_code_file_is_skipped = len(violations) == 0
    assert non_code_file_is_skipped


def test_check_content_processes_python_file(code_quality_checker):
    content = '''
def foo(x):
    if x > 0:
        return 1
    return 0
'''
    violations = code_quality_checker.check_content(content, 'main.py')
    python_file_is_processed = len(violations) > 0
    assert python_file_is_processed


def test_check_content_processes_typescript_file(code_quality_checker):
    content = '''
function foo() {
  for (let i = 0; i < 10; i++) {
    break;
  }
}
'''
    violations = code_quality_checker.check_content(content, 'index.ts')
    typescript_file_is_processed = len(violations) > 0
    assert typescript_file_is_processed
