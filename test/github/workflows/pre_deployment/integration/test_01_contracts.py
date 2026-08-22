"""Contract tests for the workflow files in .github/workflows/.

GitHub starts every workflow in this repository from its own push trigger, so a
workflow's 'on: push: paths:' list is the only record of which files belong to
it. These tests read that list back against the source the workflow actually
deploys, builds and runs, and check that nothing in the tree can start a run
other than a push. Per docs/tenets/tests/PRE_DEPLOYMENT_INTEGRATION_TESTS.md,
Layer 1 contract tests validate cross-file compatibility without making AWS
calls.
"""

import re
from pathlib import Path

import yaml

from repo_utils import REPO_ROOT


WORKFLOWS_DIR = REPO_ROOT / ".github" / "workflows"
GREPPED_NAME = re.compile(r"grep '(\w+)'")
LIB_PYTHON_ROOT = REPO_ROOT / "lib" / "python"

# The directory the deleted controller lived in. A workflow naming it is a
# workflow starting another one again.
CONTROLLER_SOURCE = "src/workflowctl/"

# Globs that deploy a workflow on any edit anywhere under a whole tree. A
# workflow names the packages it builds from instead.
WHOLE_TREE_GLOBS = ("lib/python/**", "test/lib/python/**")

# State keys owned by another repository's Terraform. Nothing here applies
# them, so a read of one of these asks for no workflow of ours. Anything not
# listed here has to be a stack a workflow in this repository deploys.
EXTERNAL_STATE_KEYS = {"wan-synthesizer/common/routing/terraform.tfstate"}


REMOTE_STATE_BLOCK = re.compile(r'data\s+"terraform_remote_state"\s+"[^"]+"\s*\{')
STATE_KEY = re.compile(r'key\s*=\s*"([^"]+)"')
WORKING_DIRECTORY = re.compile(r"^\s*cd\s+(\S+)", re.MULTILINE)
DOCKERFILE_PATH = re.compile(r"^\s*\w+=(\S+/Dockerfile)$", re.MULTILINE)
NPM_PREFIX = re.compile(r"--prefix\s+(src/\S+)")
S3_SYNC = re.compile(r"aws s3 sync\s+(src/\S+)")
TERRAFORM_MODULE = re.compile(r"cd (lib/terraform/[\w-]+)")
CHANGED_FILE_EVENT = re.compile(r"github\.event\.(?:before|commits)")
INVALIDATION_INPUT = "github.event.inputs.invalidate_cloudfront"
PUSH_EVENT = "github.event_name == 'push'"
STEP_OUTPUT = re.compile(r"steps\.([A-Za-z0-9_-]+)\.outputs\.")
TEST_ASSIGNMENT = re.compile(r"^\s*(\w+)=(test/[\w./-]+)\s*$", re.MULTILINE)
TEST_ARGUMENT = re.compile(r"(?<![=\w])test/[\w./-]+")
LOCAL_ACTION = "./.github/actions/"


def _declared_packages(paths: list, prefix: str) -> list:
    """List the package names a paths list declares as '<prefix><name>/**'.

    A workflow that declares the whole of a directory names no package, so the
    bare '<prefix>**' is not a package name and is left out.
    """
    depth = len(prefix.rstrip("/").split("/"))
    return [
        path.split("/")[depth] for path in paths
        if path.startswith(prefix) and len(path.split("/")) > depth + 1
    ]


def _python_files_under(path_glob: str) -> list:
    """List the Python files a path glob matches.

    The literal part only says where to start looking: 'src/.../webhooks/*.tf'
    reaches no Python at all, and 'src/api/endpoints/github_workflows/**'
    reaches every stack nested inside it. Matching the whole glob is what tells
    them apart.
    """
    root = REPO_ROOT / Path(path_glob.split("*")[0])
    if not root.is_dir():
        return []
    return sorted(
        path for path in root.rglob("*.py")
        if _matches_glob(path_glob, _repo_relative(path))
    )


def _node_imports(paths: list, package: str) -> bool:
    """Say whether the source a paths list names imports a lib/python package."""
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
    thing built from it.
    """
    declared = set(_declared_packages(paths, "lib/python/"))
    return [
        package for package in _lib_python_packages()
        if package not in declared and _node_imports(paths, package)
    ]


def _matches_glob(glob: str, path: str) -> bool:
    """Say whether a repository-relative path is matched by a path filter.

    '**' spans directories and '*' stops at one, which is how GitHub reads the
    same globs in a workflow's paths filter.
    """
    pattern = re.escape(glob).replace(r"\*\*", ".*").replace(r"\*", "[^/]*")
    return re.fullmatch(pattern, path) is not None


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


def _checked_modules(name: str) -> list:
    """List the shared Terraform modules a workflow formats and lints.

    A module under lib/terraform is deployed by no workflow of its own, so
    the runs that change directory into it are the only ones that check it.
    """
    text = (WORKFLOWS_DIR / f"{name}.yml").read_text(encoding="utf-8")
    return sorted(set(TERRAFORM_MODULE.findall(text)))


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


def _loaded_conftests(directory: str) -> list:
    """List the conftest.py files pytest loads for one test directory.

    pytest reads a conftest from every directory between --confcutdir and the
    one it is handed, so the fixtures a suite is written against usually sit
    several levels above the suite itself.
    """
    parts = Path(directory).parts
    candidates = [Path(*parts[:depth]) for depth in range(1, len(parts) + 1)]
    return [
        _repo_relative(REPO_ROOT / candidate / "conftest.py")
        for candidate in candidates
        if (REPO_ROOT / candidate / "conftest.py").exists()
    ]


def _local_actions(name: str) -> list:
    """List the composite actions under .github/actions a workflow runs.

    A step reaches a local action by its directory rather than its file, so
    'uses: ./.github/actions/verify-oidc-vars' is the action.yml inside it.
    """
    source = (WORKFLOWS_DIR / f"{name}.yml").read_text(encoding="utf-8")
    used = set()
    for job in (yaml.safe_load(source).get("jobs") or {}).values():
        for step in job.get("steps") or []:
            reference = step.get("uses")
            if isinstance(reference, str) and reference.startswith(LOCAL_ACTION):
                used.add(f"{reference[2:]}/action.yml")
    return sorted(used)


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
    """Tests the workflows GitHub starts from a push, which is all of them."""

    def test_a_push_triggered_workflow_matches_its_own_source(self) -> None:
        """Verify a push-triggered workflow runs when its own file or stack changes.

        Nothing but the push starts a workflow now, so a paths list that
        misses its own source silently stops deploying it.
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

    def test_a_push_triggered_workflow_names_the_modules_it_checks(self) -> None:
        """Verify a shared module such a workflow checks is named in its paths.

        A module under lib/terraform belongs to no stack, so the workflow that
        formats and lints it is the only place its files are read at all. The
        paths list is the record of that, and a module left out of it is one
        whose edits are checked by nothing until something else in the same
        workflow happens to change.
        """
        unchecked = []

        for name, paths in sorted(_push_triggered_workflows().items()):
            covered = {glob.split("*")[0].rstrip("/") for glob in paths}
            for module in _checked_modules(name):
                if module not in covered:
                    unchecked.append(
                        f"{name}: formats {module} but its paths do not name it"
                    )

        assert not unchecked, (
            "Push triggers that miss a module they check:\n  " + "\n  ".join(unchecked)
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
            if _matches_glob(glob, f"{root}/backend.tf")
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
            if _matches_glob(glob, f"{build}/Dockerfile")
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
                if any(_matches_glob(glob, path) for glob in paths)
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
            for name in sorted(_push_triggered_workflows())
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

        The paths list is the only record of which tests belong to a
        workflow, and one it misses is a test whose edits never run it.
        """
        unnamed = []

        for name, paths in sorted(_push_triggered_workflows().items()):
            for directory in _test_directories(name):
                below = (REPO_ROOT / directory).rglob("*")
                for test in sorted(entry for entry in below if entry.is_file()):
                    path = _repo_relative(test)
                    if not any(_matches_glob(glob, path) for glob in paths):
                        unnamed.append(f"{name}: runs {path}, which its paths do not name")

        assert not unnamed, (
            "Push triggers that miss a test they run:\n  " + "\n  ".join(unnamed)
        )

    def test_a_push_triggered_workflow_names_the_conftests_it_loads(self) -> None:
        """Verify every conftest.py such a workflow's tests load is in its paths.

        A suite's fixtures live in the conftest files above it, not only in the
        directory the workflow hands to pytest. A paths list that names the
        directory and not those files never re-runs the suite when the fixtures
        change, so a fixture edit that breaks or quietly weakens a dozen
        endpoints' tests starts nothing, and surfaces on whichever unrelated
        push happens to touch that workflow next.
        """
        unnamed = [
            f"{name}: loads {conftest}, which its paths do not name"
            for name, paths in sorted(_push_triggered_workflows().items())
            for directory in _test_directories(name)
            for conftest in _loaded_conftests(directory)
            if not any(_matches_glob(glob, conftest) for glob in paths)
        ]

        assert not unnamed, (
            "Push triggers that miss a conftest they load:\n  " + "\n  ".join(unnamed)
        )

    def test_a_push_triggered_workflow_names_the_actions_it_uses(self) -> None:
        """Verify every composite action such a workflow runs is in its paths.

        The actions under .github/actions are shared source: one of them is
        what every deploy runs to check the OIDC role is configured before it
        authenticates. A paths list that does not name the action it runs never
        re-runs on an edit to it, so a mistake there lands green and then
        breaks whichever unrelated push next starts a deploy.
        """
        missed = [
            f"{workflow}: uses {action}, which its paths do not name"
            for workflow, paths in sorted(_push_triggered_workflows().items())
            for action in _local_actions(workflow)
            if not any(_matches_glob(glob, action) for glob in paths)
        ]

        assert not missed, (
            "Push triggers that miss an action they use:\n  " + "\n  ".join(missed)
        )

    def test_a_push_triggered_workflow_names_no_whole_tree_glob(self) -> None:
        """Verify such a workflow does not rebuild on any edit under lib/python.

        A workflow's trigger is the only record of how narrow it is, so the
        paths list is the only place left that can widen.
        A workflow that applies no Terraform rebuilds nothing, so the cost this
        measures does not exist for it: scripts.yml deploys nothing and lints
        and tests both trees whole, which is why they are what it names.
        """
        deploys = set(_applied_stacks())
        widened = [
            f"{name}: its paths name '{glob}', so any edit under it rebuilds this"
            for name, paths in sorted(_push_triggered_workflows().items())
            if name in deploys
            for glob in WHOLE_TREE_GLOBS
            if glob in paths
        ]

        assert not widened, (
            "Push triggers wider than the source they build from:\n  "
            + "\n  ".join(widened)
        )

    def test_a_push_triggered_workflow_imports_every_package_it_names(self) -> None:
        """Verify each lib/python package such a workflow names is one it imports.

        A package named by a workflow whose source does not import it rebuilds
        and redeploys that stack for every edit to code it never runs, and puts
        an unrelated deploy in the way of the one the edit was for.
        """
        unimported = [
            f"{name}: names lib/python/{package}/** but no Python under its own "
            "src paths imports it"
            for name, paths in sorted(_push_triggered_workflows().items())
            for package in _declared_packages(paths, "lib/python/")
            if not _node_imports(paths, package)
        ]

        assert not unimported, (
            "Packages named but not imported:\n  " + "\n  ".join(unimported)
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


class TestWorkflowsReadOnlyLiteralLocals:
    """Tests that a workflow reading locals.tf takes a value written there."""

    def test_a_scraped_local_is_a_quoted_literal(self) -> None:
        """Verify each local a workflow cuts out of locals.tf is a string.

        A workflow that needs a shared setting greps its line out of locals.tf
        and cuts the value from between the quotes, which hands back the whole
        line when the setting is a Terraform expression rather than a literal.
        The step then carries a fragment of HCL where a value belongs, and
        every command built from it fails on a run that reached AWS.
        """
        locals_text = (
            REPO_ROOT / "lib" / "terraform" / "common" / "locals.tf"
        ).read_text(encoding="utf-8")
        assigned = dict(re.findall(r"^  (\w+)\s*=\s*(\S)", locals_text, re.M))
        expressions = {
            name for name, first in assigned.items() if first != '"'
        }
        scraped = []

        for workflow in sorted(WORKFLOWS_DIR.glob("*.yml")):
            document = yaml.safe_load(workflow.read_text(encoding="utf-8"))
            for job, definition in sorted((document.get("jobs") or {}).items()):
                for step in definition.get("steps") or []:
                    script = step.get("run") or ""
                    if "locals.tf" not in script:
                        continue
                    scraped += [
                        f"{workflow.name}: job '{job}' cuts '{name}' out of "
                        "locals.tf, where it is an expression and not a string"
                        for name in sorted(set(GREPPED_NAME.findall(script)))
                        if name in expressions
                    ]

        assert not scraped, (
            "Locals read as strings that are not:\n  " + "\n  ".join(scraped)
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


class TestBootstrapCanBeAppliedIntoAnEmptyAccount:
    """Tests that the one workflow a cold account needs can still be pressed."""

    def test_bootstrap_keeps_its_workflow_dispatch_trigger(self) -> None:
        """Verify bootstrap can be started by hand as well as by a push.

        Bootstrap creates the bucket every other stack keeps its state in and
        the role every other run assumes, so in an account where none of that
        exists yet a push can start nothing at all and the first deploy has to
        be pressed. A conversion that dropped this trigger would look correct
        until the next fresh account, which is the worst moment to find out.
        """
        document = yaml.safe_load(
            (WORKFLOWS_DIR / "bootstrap.yml").read_text(encoding="utf-8")
        )
        triggers = document.get(True) or document.get("on") or {}

        assert "workflow_dispatch" in triggers, (
            "bootstrap.yml can only be started by a push, so an account with no "
            "state bucket and no OIDC role has no way to deploy it"
        )


class TestEveryWorkflowIsStartedByItsOwnPaths:
    """Tests that GitHub starts every workflow, now nothing else can."""

    def test_every_workflow_declares_a_push_trigger_with_paths(self) -> None:
        """Verify each workflow runs on a push to main that matches its paths.

        A controller used to start the workflows that named no paths of their
        own, and there is no controller any more. A workflow left without this
        trigger deploys only when somebody presses the button, so its steps go
        unread and the code it deploys stays whatever was there last.
        """
        unstarted = []

        for workflow in sorted(WORKFLOWS_DIR.glob("*.yml")):
            document = yaml.safe_load(workflow.read_text(encoding="utf-8"))
            triggers = document.get(True) or document.get("on") or {}
            push = triggers.get("push")
            if not isinstance(push, dict):
                unstarted.append(f"{workflow.name}: declares no push trigger")
            elif push.get("branches") != ["main"]:
                unstarted.append(
                    f"{workflow.name}: its push trigger names "
                    f"{push.get('branches')} rather than main"
                )
            elif not push.get("paths"):
                unstarted.append(f"{workflow.name}: its push trigger names no paths")

        assert not unstarted, (
            "Workflows a push does not start:\n  " + "\n  ".join(unstarted)
        )


class TestNoWorkflowRunsTheController:
    """Tests that the deleted controller does not come back a step at a time."""

    def test_no_workflow_names_the_controller_source(self) -> None:
        """Verify no workflow file still shells out to src/workflowctl.

        The controller worked out which workflows a push should start and
        dispatched them, which GitHub now does from the paths filters. One
        copied step is all it would take to have a workflow starting another
        again, and two runs of one stack racing on a single state lock.
        """
        revived = [
            f"{workflow.name}: a step names {CONTROLLER_SOURCE}"
            for workflow in sorted(WORKFLOWS_DIR.glob("*.yml"))
            if CONTROLLER_SOURCE in workflow.read_text(encoding="utf-8")
        ]

        assert not revived, (
            "Workflows running the deleted controller:\n  " + "\n  ".join(revived)
        )


class TestNoWorkflowCanStartOrCancelAnother:
    """Tests that no run holds the token permission a dispatch needs."""

    def test_no_workflow_requests_permission_to_write_actions(self) -> None:
        """Verify no workflow asks for actions: write.

        A run needs that permission to start or cancel another run, and the
        controller was the only thing here that did. A run able to cancel
        another can kill a deploy part-way through terraform apply, which
        strands the state lock, so this is where a request for it is noticed.
        """
        requested = []

        for workflow in sorted(WORKFLOWS_DIR.glob("*.yml")):
            document = yaml.safe_load(workflow.read_text(encoding="utf-8"))
            declared = [("the file", document.get("permissions"))]
            declared += [
                (f"job '{job}'", definition.get("permissions"))
                for job, definition in sorted((document.get("jobs") or {}).items())
            ]
            requested += [
                f"{workflow.name}: {where} asks for actions: write"
                for where, permissions in declared
                if isinstance(permissions, dict)
                and permissions.get("actions") == "write"
            ]

        assert not requested, (
            "Workflows able to start or cancel another:\n  " + "\n  ".join(requested)
        )
