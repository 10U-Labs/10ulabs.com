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
LIB_PYTHON_ROOT = REPO_ROOT / "lib" / "python"

# Nodes still allowed to deploy on any edit anywhere under lib/python. Narrow
# a node to the packages it builds from rather than adding a key here; the
# list is meant to stay empty.
WHOLE_TREE_GLOB_NODES: set = set()
WHOLE_TREE_GLOBS = ("lib/python/**", "test/lib/python/**")

# State keys owned by another repository's Terraform. This controller only
# orders workflows in this repository, so a read of one of these implies no
# edge. Anything not listed here must resolve to a node in the graph.
EXTERNAL_STATE_KEYS = {"wan-synthesizer/common/routing/terraform.tfstate"}

# Orderings that exist for a reason Terraform does not express, and the reason.
# Every other entry in a node's depends_on has to correspond to a
# terraform_remote_state read under that node's own src paths.
ORDERINGS_WITHOUT_STATE_READS: dict = {}

REMOTE_STATE_BLOCK = re.compile(r'data\s+"terraform_remote_state"\s+"[^"]+"\s*\{')
STATE_KEY = re.compile(r'key\s*=\s*"([^"]+)"')
DEFAULTS_ATTRIBUTE = re.compile(r"^\s*defaults\s*=", re.MULTILINE)
WORKING_DIRECTORY = re.compile(r"^\s*cd\s+(\S+)", re.MULTILINE)
DOCKERFILE_PATH = re.compile(r"^\s*\w+=(\S+/Dockerfile)$", re.MULTILINE)
NPM_PREFIX = re.compile(r"--prefix\s+(src/\S+)")
S3_SYNC = re.compile(r"aws s3 sync\s+(src/\S+)")
CHANGED_FILE_EVENT = re.compile(r"github\.event\.(?:before|commits)")
INVALIDATION_INPUT = "github.event.inputs.invalidate_cloudfront"
PUSH_EVENT = "github.event_name == 'push'"
STEP_OUTPUT = re.compile(r"steps\.([A-Za-z0-9_-]+)\.outputs\.")
TEST_ASSIGNMENT = re.compile(r"^\s*(\w+)=(test/[\w./-]+)\s*$", re.MULTILINE)
TEST_ARGUMENT = re.compile(r"(?<![=\w])test/[\w./-]+")

# The controller itself, which is started by every push and names no paths.
CONTROLLER = "workflowctl"


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
    """List the Python files a path glob matches.

    The literal part only says where to start looking: 'src/.../runners/*.tf'
    reaches no Python at all, and 'src/.../runners/ec2/**' reaches the images
    node nested inside it. Matching the whole glob is what tells them apart.
    """
    root = REPO_ROOT / Path(path_glob.split("*")[0])
    if not root.is_dir():
        return []
    return sorted(
        path for path in root.rglob("*.py")
        if _matches_glob(path_glob, _repo_relative(path))
    )


def _node_imports(paths: list, package: str) -> bool:
    """Say whether a node's own source imports a lib/python package."""
    forms = (f"import {package}\n", f"from {package} import", f"from {package}.")
    for path_glob in [p for p in paths if p.startswith("src/")]:
        for source in _python_files_under(path_glob):
            content = source.read_text(encoding="utf-8")
            if any(form in content for form in forms):
                return True
    return False


def _lib_python_packages() -> list:
    """List the package names under lib/python."""
    return sorted(
        path.name for path in LIB_PYTHON_ROOT.iterdir()
        if path.is_dir() and not path.name.startswith("_")
    )


def _undeclared_imports(paths: list) -> list:
    """List the lib/python packages a paths list imports without naming.

    A package imported but not named is a package whose edits never reach the
    thing built from it, whether the paths came from the graph or from a
    workflow's own push trigger.
    """
    declared = set(_declared_packages(paths, "lib/python/"))
    return [
        package for package in _lib_python_packages()
        if package not in declared and _node_imports(paths, package)
    ]


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
        node = _owning_node(graph, _repo_relative(backend))
        if key is not None and node:
            owners[key.group(1)] = node
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
        if not node:
            continue
        for match in REMOTE_STATE_BLOCK.finditer(text):
            body = _block_body(text, match.end() - 1)
            key = STATE_KEY.search(body)
            if key is None or (hard_only and DEFAULTS_ATTRIBUTE.search(body)):
                continue
            reads.setdefault(node, set()).add(key.group(1))
    return reads


def _terraform_directory(name: str) -> str:
    """Name the directory a workflow runs 'terraform apply' in, if it does."""
    text = (WORKFLOWS_DIR / f"{name}.yml").read_text(encoding="utf-8")
    if "terraform apply" not in text:
        return ""
    return WORKING_DIRECTORY.findall(text[:text.index("terraform apply")])[-1]


def _dockerfile_directory(name: str) -> str:
    """Name the directory holding the Dockerfile a workflow builds, if it builds one."""
    text = (WORKFLOWS_DIR / f"{name}.yml").read_text(encoding="utf-8")
    found = DOCKERFILE_PATH.search(text)
    return str(Path(found.group(1)).parent) if found else ""


def _npm_directory(name: str) -> str:
    """Name the npm project a workflow builds, if it builds one.

    A site with no Terraform of its own is still built from a directory, and
    'npm --prefix' is where the workflow says which one.
    """
    text = (WORKFLOWS_DIR / f"{name}.yml").read_text(encoding="utf-8")
    found = NPM_PREFIX.search(text)
    return found.group(1) if found else ""


def _synced_directories(name: str) -> list:
    """List the directories a workflow copies into S3, if it copies any.

    A site is published by an 'aws s3 sync' of one directory, which is either
    the checked-in source or a build output sitting inside it.
    """
    text = (WORKFLOWS_DIR / f"{name}.yml").read_text(encoding="utf-8")
    return sorted({found.rstrip("/") for found in S3_SYNC.findall(text)})


def _applied_stacks() -> dict:
    """Map each workflow that runs 'terraform apply' to the state key it writes.

    The directory the apply runs in is the Terraform root module, and its
    backend.tf names the state object the lock is taken against.
    """
    stacks = {}
    for workflow in sorted(WORKFLOWS_DIR.glob("*.yml")):
        directory = _terraform_directory(workflow.stem)
        if not directory:
            continue
        backend = REPO_ROOT / directory / "backend.tf"
        key = STATE_KEY.search(backend.read_text(encoding="utf-8"))
        if key is not None:
            stacks[workflow.stem] = key.group(1)
    return stacks


def _glob_matches(glob: str, path: str) -> bool:
    """Say whether a GitHub path filter matches a repository path.

    A single star stops at a directory separator and a double star crosses
    them, which is what separates a stack's own files from a neighbour's.
    """
    pattern = re.escape(glob).replace(r"\*\*", "\x00").replace(r"\*", "[^/]*")
    return re.fullmatch(pattern.replace("\x00", ".*"), path) is not None


def _test_directories(name: str) -> list:
    """List the test directories a workflow hands to pytest.

    A step names them through a shell variable set in the same block, so the
    assignment is substituted back in before the arguments are read out.
    """
    source = (WORKFLOWS_DIR / f"{name}.yml").read_text(encoding="utf-8")
    found: set = set()
    for job in (yaml.safe_load(source).get("jobs") or {}).values():
        for step in job.get("steps") or []:
            block = step.get("run")
            if not isinstance(block, str):
                continue
            for variable, value in TEST_ASSIGNMENT.findall(block):
                block = block.replace(f"${{{variable}}}", value)
                block = block.replace(f"${variable}", value)
            found |= {argument.rstrip("/") for argument in TEST_ARGUMENT.findall(block)}
    return sorted(found)


def _push_triggered_workflows() -> dict:
    """Map each workflow GitHub starts from a push to the paths it matches on."""
    triggered = {}
    for workflow in sorted(WORKFLOWS_DIR.glob("*.yml")):
        # 'on' is YAML 1.1 true, so safe_load gives the trigger block that key.
        document = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        paths = (document.get(True) or document.get("on") or {})
        if isinstance(paths, dict) and isinstance(paths.get("push"), dict):
            listed = paths["push"].get("paths")
            if listed:
                triggered[workflow.stem] = listed
    return triggered


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

    def test_no_node_keeps_a_whole_tree_glob(self, dependency_graph: dict) -> None:
        """Verify no node deploys on any edit anywhere under lib/python."""
        violations = [
            f"{key}: declares '{glob}', which deploys it on any edit under it"
            for key, config in sorted(dependency_graph.items())
            if key not in WHOLE_TREE_GLOB_NODES
            for glob in WHOLE_TREE_GLOBS
            if glob in config.get("paths", [])
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

    def test_imported_packages_are_declared_by_the_node(
        self, dependency_graph: dict
    ) -> None:
        """Verify each lib/python package a node's source imports is in its paths."""
        undeclared = [
            f"{key}: its source imports lib/python/{package} but its paths do "
            f"not name it, so a change there never reaches it"
            for key, config in sorted(dependency_graph.items())
            for package in _undeclared_imports(config.get("paths", []))
        ]

        assert not undeclared, (
            "Packages imported but not declared:\n  " + "\n  ".join(undeclared)
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
        deployed = set(_applied_stacks().values()) | EXTERNAL_STATE_KEYS
        unrecorded = []

        for key, state_keys in sorted(_state_reads(dependency_graph, True).items()):
            declared = set(dependency_graph.get(key, {}).get("depends_on", []))
            for state_key in sorted(state_keys):
                owner = owners.get(state_key)
                if owner is None and state_key not in deployed:
                    unrecorded.append(
                        f"{key}: reads '{state_key}', which nothing here writes"
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


class TestApplyingWorkflowsAreNotCancelled:
    """Tests that a deploy is never killed part-way through terraform apply."""

    def test_no_applying_workflow_cancels_itself(self) -> None:
        """Verify a workflow running terraform apply is not cancelled by a newer run.

        Terraform holds a lock object beside the state for the length of an
        apply. A run killed mid-apply need not reach the release, which strands
        the lock and can leave the state no longer describing the account.
        """
        cancelled = []

        for name in _applied_stacks():
            path = WORKFLOWS_DIR / f"{name}.yml"
            concurrency = yaml.safe_load(
                path.read_text(encoding="utf-8")
            ).get("concurrency", {})
            if concurrency.get("cancel-in-progress"):
                cancelled.append(
                    f"{name}: runs terraform apply and declares "
                    "cancel-in-progress: true"
                )

        assert not cancelled, (
            "Deploys that can be killed mid-apply:\n  " + "\n  ".join(cancelled)
        )

    def test_applying_workflows_serialise_on_the_stack(self) -> None:
        """Verify a deploy's concurrency group is the state key it applies.

        The lock protects a state object, so two runs of one stack have to
        queue and two runs of different stacks have to not.
        """
        misgrouped = []

        for name, state_key in _applied_stacks().items():
            path = WORKFLOWS_DIR / f"{name}.yml"
            group = yaml.safe_load(
                path.read_text(encoding="utf-8")
            ).get("concurrency", {}).get("group")
            if group != state_key:
                misgrouped.append(
                    f"{name}: applies '{state_key}' but queues on '{group}'"
                )

        assert not misgrouped, (
            "Deploys not serialised on their stack:\n  " + "\n  ".join(misgrouped)
        )


class TestPushTriggeredWorkflows:
    """Tests the workflows GitHub starts from a push rather than the controller."""

    def test_a_push_triggered_workflow_matches_its_own_source(self) -> None:
        """Verify a push-triggered workflow runs when its own file or stack changes.

        A workflow the controller no longer dispatches is started by nothing
        else, so a paths list that misses its own source silently stops
        deploying it.
        """
        unmatched = []

        for name, paths in _push_triggered_workflows().items():
            if f".github/workflows/{name}.yml" not in paths:
                unmatched.append(f"{name}: its paths do not name its own workflow file")
            built = (_terraform_directory(name), _dockerfile_directory(name),
                     _npm_directory(name))
            for directory in [entry for entry in built if entry]:
                if not any(glob.startswith(directory) for glob in paths):
                    unmatched.append(f"{name}: its paths do not cover '{directory}'")

        assert not unmatched, (
            "Push triggers that miss their own source:\n  " + "\n  ".join(unmatched)
        )

    def test_a_push_triggered_workflow_names_the_files_it_publishes(self) -> None:
        """Verify such a workflow's paths reach the files it copies into S3.

        A site with no Terraform and no build step is published straight from
        the tree, so its paths list is the only thing tying the workflow to the
        pages it serves. One it misses is a page whose edits never reach the
        bucket.
        """
        unreached = [
            f"{name}: syncs {directory} into S3, which its paths do not reach"
            for name, paths in sorted(_push_triggered_workflows().items())
            for directory in _synced_directories(name)
            if not any(f"{directory}/".startswith(glob.split("*")[0]) for glob in paths)
        ]

        assert not unreached, (
            "Push triggers that miss the files they publish:\n  " + "\n  ".join(unreached)
        )

    def test_a_push_triggered_workflow_reads_only_stacks_deployed_here(self) -> None:
        """Verify every state such a workflow's Terraform reads is applied by a workflow.

        Nothing orders these runs any more, so a read of a stack no workflow
        here deploys is a dependency on something that may never exist.
        """
        undeployed = []
        deployed = set(_applied_stacks().values()) | EXTERNAL_STATE_KEYS

        for name in _push_triggered_workflows():
            directory = _terraform_directory(name)
            if not directory:
                continue
            for source in sorted((REPO_ROOT / directory).glob("*.tf")):
                text = source.read_text(encoding="utf-8")
                for match in REMOTE_STATE_BLOCK.finditer(text):
                    key = STATE_KEY.search(_block_body(text, match.end() - 1))
                    if key is not None and key.group(1) not in deployed:
                        undeployed.append(
                            f"{name}: reads '{key.group(1)}', which no workflow applies"
                        )

        assert not undeployed, (
            "Reads of stacks nothing deploys:\n  " + "\n  ".join(undeployed)
        )

    def test_a_push_triggered_workflow_is_not_also_a_graph_node(
        self, dependency_graph: dict
    ) -> None:
        """Verify no workflow is both started by a push and dispatched as a descendant.

        A workflow named in both places runs twice for one commit: GitHub
        starts it on its paths, and the controller starts it again as soon as
        a parent reports, with the two runs racing on the same state lock.
        """
        doubled = sorted(set(dependency_graph) & set(_push_triggered_workflows()))

        assert not doubled, (
            "Workflows started twice for one push:\n  " + "\n  ".join(doubled)
        )

    def test_a_push_triggered_workflow_reaches_no_other_stack(self) -> None:
        """Verify such a workflow's paths match no Terraform root but its own.

        Nothing orders these runs any more, so a glob that reaches a
        neighbouring stack starts two applies against two state files for one
        commit, each holding its own lock and neither aware of the other.
        """
        roots = {name: _terraform_directory(name) for name in _applied_stacks()}
        crossed = [
            f"{name}: its paths name '{glob}', which reaches {root}/backend.tf"
            for name, paths in sorted(_push_triggered_workflows().items())
            for root in sorted(set(roots.values()))
            if root and root != roots.get(name, _terraform_directory(name))
            for glob in paths
            if _glob_matches(glob, f"{root}/backend.tf")
        ]

        assert not crossed, (
            "Push triggers that reach another stack:\n  " + "\n  ".join(crossed)
        )

    def test_a_push_triggered_workflow_reaches_no_other_build(self) -> None:
        """Verify such a workflow's paths match no Docker build but its own.

        The image a workflow builds sits in a directory of its own below the
        stack that runs on it, so a glob reaching into it deploys a stack again
        for every edit to a Dockerfile that stack does not build.
        """
        builds = {name: _dockerfile_directory(name) for name in _push_triggered_workflows()}
        reached = [
            f"{name}: its paths name '{glob}', which reaches {build}/Dockerfile"
            for name, paths in sorted(_push_triggered_workflows().items())
            for build in sorted(entry for entry in set(builds.values()) if entry)
            if build != builds[name]
            for glob in paths
            if _glob_matches(glob, f"{build}/Dockerfile")
        ]

        assert not reached, (
            "Push triggers that reach another build:\n  " + "\n  ".join(reached)
        )

    def test_a_push_triggered_workflow_owns_the_source_it_names(self) -> None:
        """Verify no file under src/ is named by two push triggers.

        A source file belongs to one deploy. Where a second trigger reaches it,
        one edit runs two deploys, and the one that did not want the edit is
        applying a stack for no reason.
        """
        triggers = _push_triggered_workflows()
        shared = []

        for entry in sorted((REPO_ROOT / "src").rglob("*")):
            if not entry.is_file():
                continue
            path = _repo_relative(entry)
            owners = [
                name for name, paths in sorted(triggers.items())
                if any(_glob_matches(glob, path) for glob in paths)
            ]
            if len(owners) > 1:
                shared.append(f"{path}: named by {', '.join(owners)}")

        assert not shared, (
            "Source files more than one push trigger reaches:\n  " + "\n  ".join(shared)
        )

    def test_a_push_triggered_workflow_does_not_rederive_the_changed_files(self) -> None:
        """Verify no such workflow works out for itself what the push changed.

        The trigger already matched the push against this workflow's paths, so
        a step that diffs github.event.before is answering the same question
        from a worse place. A dispatch carries no such commit, and the fallback
        compares a whole push against its own tip, which loses every commit
        below it.
        """
        rederived = [
            f"{name}: a step reads {reference}"
            for name in sorted(set(_push_triggered_workflows()) - {CONTROLLER})
            for reference in sorted(set(CHANGED_FILE_EVENT.findall(
                (WORKFLOWS_DIR / f"{name}.yml").read_text(encoding="utf-8")
            )))
        ]

        assert not rederived, (
            "Push triggers recomputed inside the run:\n  " + "\n  ".join(rederived)
        )

    def test_a_push_triggered_workflow_clears_its_cache_on_every_push(self) -> None:
        """Verify a run started by a push is a run that clears the CDN cache.

        The push already matched this workflow's paths, so the deploy it starts
        is a deploy of the files the cache is holding. A condition that leaves
        the push out clears the cache only when somebody presses the button,
        and visitors keep being served the copies the deploy replaced.
        """
        stale = []

        for name in sorted(_push_triggered_workflows()):
            document = yaml.safe_load(
                (WORKFLOWS_DIR / f"{name}.yml").read_text(encoding="utf-8")
            )
            for job, definition in sorted((document.get("jobs") or {}).items()):
                for step in definition.get("steps") or []:
                    condition = step.get("if") or ""
                    if INVALIDATION_INPUT in condition and PUSH_EVENT not in condition:
                        stale.append(
                            f"{name}: job '{job}' step "
                            f"'{step.get('name', step.get('id'))}' asks for the "
                            "input and not for the push"
                        )

        assert not stale, (
            "Invalidations a push does not reach:\n  " + "\n  ".join(stale)
        )

    def test_a_push_triggered_workflow_names_the_tests_it_runs(self) -> None:
        """Verify every test file such a workflow runs is named in its paths.

        The graph node used to tie a workflow to the tests it runs. With the
        node gone the paths list is the only record of which tests belong to
        it, and one it misses is a test whose edits never run it.
        """
        unnamed = []

        for name, paths in sorted(_push_triggered_workflows().items()):
            for directory in _test_directories(name):
                below = (REPO_ROOT / directory).rglob("*")
                for test in sorted(entry for entry in below if entry.is_file()):
                    path = _repo_relative(test)
                    if not any(_glob_matches(glob, path) for glob in paths):
                        unnamed.append(f"{name}: runs {path}, which its paths do not name")

        assert not unnamed, (
            "Push triggers that miss a test they run:\n  " + "\n  ".join(unnamed)
        )

    def test_a_push_triggered_workflow_names_no_whole_tree_glob(self) -> None:
        """Verify such a workflow does not rebuild on any edit under lib/python.

        Once a node leaves the graph its trigger is the only record of how
        narrow it is, so the paths list is the only place left that can widen.
        """
        widened = [
            f"{name}: its paths name '{glob}', so any edit under it rebuilds this"
            for name, paths in sorted(_push_triggered_workflows().items())
            for glob in WHOLE_TREE_GLOBS
            if glob in paths
        ]

        assert not widened, (
            "Push triggers wider than the source they build from:\n  "
            + "\n  ".join(widened)
        )

    def test_a_push_triggered_workflow_names_every_package_it_imports(self) -> None:
        """Verify each lib/python package such a workflow imports is in its paths.

        Narrowing the paths list is what makes this reachable: a package left
        out is one whose edits never rebuild the thing that imports it.
        """
        missing = [
            f"{name}: its source imports lib/python/{package} but its paths do "
            f"not name it, so a change there never reaches it"
            for name, paths in sorted(_push_triggered_workflows().items())
            for package in _undeclared_imports(paths)
        ]

        assert not missing, (
            "Push triggers that miss a package they import:\n  " + "\n  ".join(missing)
        )


class TestStepConditionsNameLiveSteps:
    """Tests that a gated step reads an output some step beside it produces."""

    def test_a_condition_names_only_step_outputs_that_exist(self) -> None:
        """Verify no step is gated on the output of a step that is not there.

        GitHub hands an absent step output the empty string rather than an
        error, so a condition left behind when its step is deleted is false in
        every run and the step it guards quietly stops happening.
        """
        dangling = []

        for workflow in sorted(WORKFLOWS_DIR.glob("*.yml")):
            document = yaml.safe_load(workflow.read_text(encoding="utf-8"))
            for job, definition in sorted((document.get("jobs") or {}).items()):
                present = {
                    step["id"] for step in definition.get("steps") or []
                    if step.get("id")
                }
                named = set(STEP_OUTPUT.findall(yaml.safe_dump(definition)))
                dangling += [
                    f"{workflow.name}: job '{job}' reads steps.{missing}.outputs "
                    "and no step in that job carries the id"
                    for missing in sorted(named - present)
                ]

        assert not dangling, (
            "Conditions on steps that are gone:\n  " + "\n  ".join(dangling)
        )


class TestEveryWorkflowCanBeStarted:
    """Tests that something in the repository is able to start each workflow."""

    def test_no_workflow_is_left_with_nothing_to_start_it(
        self, dependency_graph: dict, workflow_files: set
    ) -> None:
        """Verify each workflow is either a graph node or triggered by a push.

        The controller starts a workflow only when the graph names it, so a
        file in neither place is deployed only when somebody presses the
        button and its steps go unread until they are pressed.
        """
        started = set(dependency_graph) | set(_push_triggered_workflows())
        stranded = sorted(workflow_files - started - {CONTROLLER})

        assert not stranded, (
            "Workflows nothing starts:\n  " + "\n  ".join(stranded)
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
