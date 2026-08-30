import re
from pathlib import Path
from typing import Any, Dict, Optional

from repo_utils import REPO_ROOT as _REPO_ROOT, extract_brace_block

COMMON_MODULE_DIR = _REPO_ROOT / "lib" / "terraform" / "common"


def _parse_map_block(content: str, map_name: str) -> Dict[str, str]:
    pattern = rf'{map_name}\s*=\s*\{{'
    match = re.search(pattern, content)
    if not match:
        return {}

    block_content = extract_brace_block(content, match.end() - 1)
    values = {}
    entry_pattern = r'(\w+)\s*=\s*"([^"]+)"'
    for entry_match in re.finditer(entry_pattern, block_content):
        key, value = entry_match.groups()
        values[key] = value
    return values


def _parse_locals() -> Dict[str, str]:
    locals_path = COMMON_MODULE_DIR / "locals.tf"
    with open(locals_path, encoding="utf-8") as f:
        content = f.read()

    values = {}
    pattern = r'(\w+)\s*=\s*"([^"]+)"'
    for match in re.finditer(pattern, content):
        key, value = match.groups()
        values[key] = value
    return values


def parse_lambda_handler_names() -> Dict[str, str]:
    locals_path = COMMON_MODULE_DIR / "locals.tf"
    with open(locals_path, encoding="utf-8") as f:
        content = f.read()

    raw_values = _parse_map_block(content, "lambda_handler_names")

    locals_dict = _parse_locals()
    resource_prefix = locals_dict.get("resource_prefix", "")

    resolved = {}
    for key, value in raw_values.items():
        resolved[key] = value.replace("${local.resource_prefix}", resource_prefix)
    return resolved


def _parse_outputs() -> Dict[str, str]:
    outputs_path = COMMON_MODULE_DIR / "outputs.tf"
    with open(outputs_path, encoding="utf-8") as f:
        content = f.read()

    locals_dict = _parse_locals()
    values = {}

    literal_pattern = r'output\s+"([^"]+)"\s*\{\s*value\s*=\s*"([^"]+)"'
    for match in re.findall(literal_pattern, content):
        output_name, value = match
        values[output_name] = value

    local_pattern = r'output\s+"([^"]+)"\s*\{\s*value\s*=\s*local\.(\w+)'
    for match in re.findall(local_pattern, content):
        output_name, local_name = match
        if local_name in locals_dict:
            values[output_name] = locals_dict[local_name]

    return values


def get_shared_config() -> Dict[str, Any]:
    config: Dict[str, Any] = _parse_locals()
    config.update(_parse_outputs())
    config["lambda_handler_names"] = parse_lambda_handler_names()
    domain_name = config.get("domain_name", "")
    if domain_name:
        config["api_fqdn"] = f"api.{domain_name}"
    return config


TEST_AWS_REGION = _parse_locals().get("aws_region", "us-east-2")


def get_resource_prefix() -> str:
    return _parse_locals().get("resource_prefix", "TenULabs")


def _resolve_prefix_refs(value: str, prefix: str) -> str:
    value = value.replace("${module.common.resource_prefix}", prefix)
    value = value.replace("${local.resource_prefix}", prefix)
    return value


def _resolve_local_interpolations(value: str, local_values: Dict[str, str]) -> str:
    max_iterations = 10
    for _ in range(max_iterations):
        new_value = value
        for local_name, local_value in local_values.items():
            new_value = new_value.replace(f"${{local.{local_name}}}", local_value)
        if new_value == value:
            break
        value = new_value
    return value


def get_tfvars_values(tf_dir: Path) -> Dict[str, Any]:
    tfvars_file = tf_dir / "terraform.tfvars"
    if not tfvars_file.exists():
        return {}

    values: Dict[str, Any] = {}
    with open(tfvars_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                match = re.match(r'(\w+)\s*=\s*"([^"]+)"', line)
                if match:
                    values[match.group(1)] = match.group(2)
                    continue
                list_match = re.match(r'(\w+)\s*=\s*\[([^\]]*)\]', line)
                if list_match:
                    key = list_match.group(1)
                    list_content = list_match.group(2)
                    items = re.findall(r'"([^"]+)"', list_content)
                    values[key] = items
    return values


def _resolve_all_refs(value: str, prefix: str, handler_names: Dict[str, str]) -> str:
    value = _resolve_prefix_refs(value, prefix)
    for handler_key, handler_value in handler_names.items():
        value = value.replace(
            f"${{module.common.lambda_handler_names.{handler_key}}}",
            handler_value
        )
    return value


def get_endpoint_local_values(tf_dir: Path) -> Dict[str, str]:
    locals_file = tf_dir / "locals.tf"
    if not locals_file.exists():
        return {}
    with open(locals_file, encoding="utf-8") as f:
        content = f.read()
    locals_dict = {}
    prefix = get_resource_prefix()
    handler_names = parse_lambda_handler_names()

    for match in re.finditer(r'(\w+)\s*=\s*"([^"]*)"', content):
        locals_dict[match.group(1)] = _resolve_all_refs(match.group(2), prefix, handler_names)

    for match in re.finditer(r'(\w+)\s*=\s*module\.common\.lambda_handler_names\.(\w+)', content):
        local_name, handler_key = match.groups()
        if handler_key in handler_names:
            locals_dict[local_name] = handler_names[handler_key]

    return locals_dict


def _load_tf_file_context(tf_file: Path) -> tuple | None:
    if not tf_file.exists():
        return None
    with open(tf_file, encoding="utf-8") as f:
        content = f.read()
    return (
        content,
        get_resource_prefix(),
        get_endpoint_local_values(tf_file.parent),
        get_tfvars_values(tf_file.parent),
    )


def _resolve_lambda_function_name(
    block: str, prefix: str, locals_map: Dict, tfvars: Dict, handlers: Dict
) -> Optional[str]:
    match = re.search(r'^\s*function_name\s*=\s*"([^"]+)"', block, re.MULTILINE)
    if match:
        return _resolve_prefix_refs(match.group(1), prefix)

    match = re.search(r'^\s*function_name\s*=\s*local\.(\w+)', block, re.MULTILINE)
    if match and match.group(1) in locals_map:
        return locals_map[match.group(1)]

    match = re.search(r'^\s*function_name\s*=\s*var\.(\w+)', block, re.MULTILINE)
    if match and match.group(1) in tfvars:
        return tfvars[match.group(1)]

    match = re.search(
        r'^\s*function_name\s*=\s*module\.common\.lambda_handler_names\.(\w+)',
        block, re.MULTILINE
    )
    if match and match.group(1) in handlers:
        return handlers[match.group(1)]

    return None


def extract_lambda_function_names(tf_file: Path, use_handler_names: bool = False) -> list:
    ctx = _load_tf_file_context(tf_file)
    if ctx is None:
        return []
    content, prefix, local_values, tfvars_values = ctx
    handler_names = parse_lambda_handler_names() if use_handler_names else {}
    functions = []

    for match in re.finditer(r'resource\s+"aws_lambda_function"\s+"([^"]+)"\s*\{', content):
        block_content = extract_brace_block(content, match.end() - 1)
        func_name = _resolve_lambda_function_name(
            block_content, prefix, local_values, tfvars_values, handler_names
        )
        if func_name:
            functions.append((match.group(1), func_name))

    return functions


def packaged_lambda_sources(tf_file: Path) -> list:
    pattern = r'(?:source_file\s*=|content\s*=\s*file\()\s*"\$\{path\.module\}/([^"]+)"'
    content = tf_file.read_text(encoding="utf-8")
    return [
        packaged
        for packaged in re.findall(pattern, content)
        if packaged.endswith(".py") and ".." not in Path(packaged).parts
    ]


def packaged_lambda_archives(tf_file: Path) -> list:
    pattern = r'output_path\s*=\s*"\$\{path\.module\}/([^"]+)"'
    content = tf_file.read_text(encoding="utf-8")
    return re.findall(pattern, content)
