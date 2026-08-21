"""Contract tests for workflow_dependencies.json.

These tests verify that the workflow dependency graph aligns with the actual
workflow files in .github/workflows/. Per docs/tenets/tests/PRE_DEPLOYMENT_INTEGRATION_TESTS.md,
Layer 1 contract tests validate cross-file compatibility without making AWS calls.
"""

import json
import os
import re
from pathlib import Path

import pytest
import yaml

from repo_utils import REPO_ROOT


GRAPH_PATH = REPO_ROOT / "etc" / "workflow_dependencies.json"
WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
TERRAFORM_ROOT = REPO_ROOT / "src"

# Nodes whose paths have been narrowed off the whole of lib/python. Add a key
# here as its list is cut down to the packages it actually builds from.
NARROWED_NODES = {"api_endpoint_v1_runners_ec2_images_post"}
WHOLE_TREE_GLOBS = ("lib/python/**", "test/lib/python/**")

# State keys owned by another repository's Terraform. This controller only
# orders workflows in this repository, so a read of one of these implies no
# edge. Anything not listed here must resolve to a node in the graph.
EXTERNAL_STATE_KEYS = {"wan-synthesizer/common/routing/terraform.tfstate"}

# Orderings that exist for a reason Terraform does not express, and the reason.
# Every other entry in a node's depends_on has to correspond to a
# terraform_remote_state read under that node's own src paths.
ORDERINGS_WITHOUT_STATE_READS = {
    ("www_home", "www_common"):
        "www_home.yml reads 'terraform -chdir=src/www/common output -raw "
        "bucket_name' and syncs its built site into that bucket",
    ("www_rack_designer", "www_common"):
        "www_rack_designer.yml reads 'terraform -chdir=src/www/common output "
        "-raw bucket_name' and syncs its built site into that bucket",
    ("www_simulations_soc", "www_common"):
        "www_simulations_soc.yml reads 'terraform -chdir=src/www/common output "
        "-raw bucket_name' and syncs its built site into that bucket",
}

REMOTE_STATE_BLOCK = re.compile(r'data\s+"terraform_remote_state"\s+"[^"]+"\s*\{')
STATE_KEY = re.compile(r'key\s*=\s*"([^"]+)"')
DEFAULTS_ATTRIBUTE = re.compile(r"^\s*defaults\s*=", re.MULTILINE)


@pytest.fixture(scope="module")
def dependency_graph() -> dict:
    """Load the workflow dependency graph."""
    with open(GRAPH_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def workflow_files() -> set:
    """Get set of workflow file stems (without .yml extension)."""
    return {
        f.stem for f in WORKFLOWS_DIR.glob("*.yml")
        if not f.stem.startswith(".")
    }


def _declared_packages(paths: list, prefix: str) -> list:
    """List the package names a node declares as '<prefix><name>/**'.

    A node that declares the whole of a directory names no package, so the
    bare '<prefix>**' is not a package name and is left out.
    """
    depth = len(prefix.rstrip("/").split("/"))
    return [
        path.split("/")[depth] for path in paths
        if path.startswith(prefix) and len(path.split("/")) > depth + 1
    ]


def _python_files_under(path_glob: str) -> list:
    """List the Python files under the literal part of a path glob."""
    root = REPO_ROOT / Path(path_glob.split("*")[0])
    return sorted(root.rglob("*.py")) if root.is_dir() else []


def _node_imports(paths: list, package: str) -> bool:
    """Say whether a node's own source imports a lib/python package."""
    forms = (f"import {package}\n", f"from {package} import", f"from {package}.")
    for path_glob in [p for p in paths if p.startswith("src/")]:
        for source in _python_files_under(path_glob):
            content = source.read_text(encoding="utf-8")
            if any(form in content for form in forms):
                return True
    return False


def _matches_glob(glob: str, path: str) -> bool:
    """Say whether a repository-relative path is matched by a graph path glob.

    '**' spans directories and '*' stops at one, which is how GitHub reads the
    same globs in a workflow's paths filter.
    """
    pattern = re.escape(glob).replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
    return re.fullmatch(pattern, path) is not None


def _owning_node(graph: dict, path: str) -> str:
    """Name the node a file under src/ belongs to.

    Node paths nest — 'src/api/endpoints/runners/ec2/**' contains the images
    node — so the owner is the one whose matching glob is most specific.
    """
    owner, longest = "", -1
    for key, config in graph.items():
        for glob in config.get("paths", []):
            if not glob.startswith("src/") or not _matches_glob(glob, path):
                continue
            literal = len(glob.split("*")[0])
            if literal > longest:
                owner, longest = key, literal
    return owner


def _block_body(text: str, brace: int) -> str:
    """Return the body of the HCL block whose opening brace is at an index."""
    depth = 0
    for index in range(brace, len(text)):
        if text[index] == "{":
            depth += 1
        elif text[index] == "}":
            depth -= 1
            if depth == 0:
                return text[brace + 1:index]
    return text[brace:]


def _repo_relative(path: Path) -> str:
    """Return a path relative to the repository root, with forward slashes."""
    return path.relative_to(REPO_ROOT).as_posix()


def _state_key_owners(graph: dict) -> dict:
    """Map each Terraform state key to the node whose backend declares it."""
    owners: dict = {}
    for backend in sorted(TERRAFORM_ROOT.rglob("backend.tf")):
        key = STATE_KEY.search(backend.read_text(encoding="utf-8"))
        if key is not None:
            owners[key.group(1)] = _owning_node(graph, _repo_relative(backend))
    return owners


def _state_reads(graph: dict, hard_only: bool) -> dict:
    """Map each node to the state keys its own Terraform reads.

    A read carrying a 'defaults' block applies before the stack it reads has
    ever been applied, so it asks for no ordering and is left out when
    hard_only is set.
    """
    reads: dict = {}
    for source in sorted(TERRAFORM_ROOT.rglob("*.tf")):
        text = source.read_text(encoding="utf-8")
        node = _owning_node(graph, _repo_relative(source))
        for match in REMOTE_STATE_BLOCK.finditer(text):
            body = _block_body(text, match.end() - 1)
            key = STATE_KEY.search(body)
            if key is None or (hard_only and DEFAULTS_ATTRIBUTE.search(body)):
                continue
            reads.setdefault(node, set()).add(key.group(1))
    return reads


class TestGraphKeysMatchWorkflowFiles:
    """Tests that graph keys correspond to actual workflow files."""

    def test_all_graph_keys_have_workflow_files(
        self, dependency_graph: dict, workflow_files: set
    ) -> None:
        """Verify each graph key has a corresponding workflow file."""
        graph_keys = set(dependency_graph.keys())
        missing = graph_keys - workflow_files

        assert not missing, (
            f"Graph keys without workflow files: {sorted(missing)}. "
            f"Either create .github/workflows/<key>.yml or remove from graph."
        )


class TestGraphPathsMatchWorkflowFiles:
    """Tests that graph paths include the correct workflow file references."""

    def test_first_path_is_workflow_file(self, dependency_graph: dict) -> None:
        """Verify first path in each workflow entry is its own .yml file."""
        violations = []

        for key, config in dependency_graph.items():
            paths = config.get("paths", [])
            if not paths:
                violations.append(f"{key}: no paths defined")
                continue

            expected_first = f".github/workflows/{key}.yml"
            actual_first = paths[0]

            if actual_first != expected_first:
                violations.append(
                    f"{key}: first path is '{actual_first}', "
                    f"expected '{expected_first}'"
                )

        assert not violations, (
            "Workflow path violations:\n  " + "\n  ".join(violations)
        )


class TestGraphPathsAreNoWiderThanDependencies:
    """Tests that a node's paths name what it is built from, and no more."""

    def test_narrowed_nodes_keep_no_whole_tree_globs(
        self, dependency_graph: dict
    ) -> None:
        """Verify narrowed nodes name packages instead of a whole directory."""
        violations = [
            f"{key}: declares '{glob}', which dispatches it on any edit under it"
            for key in sorted(NARROWED_NODES)
            for glob in WHOLE_TREE_GLOBS
            if glob in dependency_graph.get(key, {}).get("paths", [])
        ]

        assert not violations, (
            "Paths wider than the node's dependencies:\n  " + "\n  ".join(violations)
        )

    def test_declared_packages_are_imported_by_node_source(
        self, dependency_graph: dict
    ) -> None:
        """Verify each lib/python package a node declares is imported by its source."""
        unimported = []

        for key, config in dependency_graph.items():
            paths = config.get("paths", [])
            for package in _declared_packages(paths, "lib/python/"):
                if not _node_imports(paths, package):
                    unimported.append(
                        f"{key}: declares lib/python/{package}/** but no Python "
                        f"under its own src paths imports it"
                    )

        assert not unimported, (
            "Packages declared but not imported:\n  " + "\n  ".join(unimported)
        )

    def test_declared_test_packages_are_run_by_the_workflow(
        self, dependency_graph: dict
    ) -> None:
        """Verify each test/lib/python package a node declares is named in its workflow."""
        unrun = []

        for key, config in dependency_graph.items():
            workflow_file = WORKFLOWS_DIR / f"{key}.yml"
            if not workflow_file.exists():
                continue  # Covered by other test

            content = workflow_file.read_text(encoding="utf-8")
            for package in _declared_packages(config.get("paths", []), "test/lib/python/"):
                if f"test/lib/python/{package}" not in content:
                    unrun.append(
                        f"{key}: declares test/lib/python/{package}/** but "
                        f"{key}.yml runs no test under it"
                    )

        assert not unrun, (
            "Test directories declared but never run:\n  " + "\n  ".join(unrun)
        )


class TestGraphDependenciesExist:
    """Tests that all dependencies reference valid graph keys."""

    def test_all_dependencies_are_valid_keys(self, dependency_graph: dict) -> None:
        """Verify all depends_on values reference existing graph keys."""
        graph_keys = set(dependency_graph.keys())
        invalid_deps = []

        for key, config in dependency_graph.items():
            for dep in config.get("depends_on", []):
                if dep not in graph_keys:
                    invalid_deps.append(f"{key} depends on unknown '{dep}'")

        assert not invalid_deps, (
            "Invalid dependencies:\n  " + "\n  ".join(invalid_deps)
        )


class TestGraphDependenciesMatchTerraformReads:
    """Tests that depends_on records what Terraform reads, and nothing else."""

    def test_every_state_a_node_reads_is_a_dependency(
        self, dependency_graph: dict
    ) -> None:
        """Verify each stack a node reads state from is one of its dependencies."""
        owners = _state_key_owners(dependency_graph)
        unrecorded = []

        for key, state_keys in sorted(_state_reads(dependency_graph, True).items()):
            declared = set(dependency_graph.get(key, {}).get("depends_on", []))
            for state_key in sorted(state_keys):
                owner = owners.get(state_key)
                if owner is None and state_key not in EXTERNAL_STATE_KEYS:
                    unrecorded.append(
                        f"{key}: reads '{state_key}', which no node in the graph owns"
                    )
                elif owner not in (None, key) and owner not in declared:
                    unrecorded.append(
                        f"{key}: reads {owner}'s state but does not depend on it"
                    )

        assert not unrecorded, (
            "State read without a dependency:\n  " + "\n  ".join(unrecorded)
        )

    def test_every_dependency_is_a_state_a_node_reads(
        self, dependency_graph: dict
    ) -> None:
        """Verify each entry in depends_on corresponds to a read or a stated reason."""
        owners = _state_key_owners(dependency_graph)
        reads = _state_reads(dependency_graph, False)
        invented = []

        for key, config in sorted(dependency_graph.items()):
            read_nodes = {owners.get(state) for state in reads.get(key, set())}
            for dep in config.get("depends_on", []):
                if dep in read_nodes or (key, dep) in ORDERINGS_WITHOUT_STATE_READS:
                    continue
                invented.append(
                    f"{key}: depends on {dep} but reads no state of it. Drop the "
                    "edge, or give the reason in ORDERINGS_WITHOUT_STATE_READS"
                )

        assert not invented, (
            "Dependencies describing no relationship:\n  " + "\n  ".join(invented)
        )


class TestGraphNamesMatchWorkflowNames:
    """Tests that graph names match actual workflow name: fields."""

    def test_graph_names_match_workflow_yaml_names(
        self, dependency_graph: dict
    ) -> None:
        """Verify graph 'name' values match workflow file 'name:' fields."""
        mismatches = []

        for key, config in dependency_graph.items():
            graph_name = config.get("name")
            if not graph_name:
                continue

            workflow_file = WORKFLOWS_DIR / f"{key}.yml"
            if not workflow_file.exists():
                continue  # Covered by other test

            with open(workflow_file, encoding="utf-8") as f:
                try:
                    workflow_yaml = yaml.safe_load(f)
                except yaml.YAMLError:
                    mismatches.append(f"{key}: could not parse YAML")
                    continue

            yaml_name = workflow_yaml.get("name")
            if yaml_name != graph_name:
                mismatches.append(
                    f"{key}: graph name '{graph_name}' != "
                    f"workflow name '{yaml_name}'"
                )

        assert not mismatches, (
            "Name mismatches between graph and workflow files:\n  " +
            "\n  ".join(mismatches)
        )


class TestNoCyclicDependencies:
    """Tests that the dependency graph has no cycles."""

    def test_graph_has_no_cycles(self, dependency_graph: dict) -> None:
        """Verify the dependency graph is acyclic."""
        # Use DFS to detect cycles
        visited: set = set()
        rec_stack: set = set()
        cycles: list = []

        def has_cycle(node: str, path: list) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for dep in dependency_graph.get(node, {}).get("depends_on", []):
                if dep not in dependency_graph:
                    continue  # Invalid dep, covered by other test

                if dep not in visited:
                    if has_cycle(dep, path + [dep]):
                        return True
                elif dep in rec_stack:
                    cycle_start = path.index(dep) if dep in path else 0
                    cycles.append(" -> ".join(path[cycle_start:] + [dep]))
                    return True

            rec_stack.remove(node)
            return False

        for key in dependency_graph:
            if key not in visited:
                has_cycle(key, [key])

        assert not cycles, (
            "Cyclic dependencies detected:\n  " + "\n  ".join(cycles)
        )
