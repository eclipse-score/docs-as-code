# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
import subprocess
import pytest
import os
import re
import logging


from pathlib import Path
from rich import print
from rich.table import Table
from collections import defaultdict
from pytest import TempPathFactory
from dataclasses import dataclass, field

from src.extensions.score_source_code_linker.generate_source_code_links_json import (
    find_git_root,
)
from src.extensions.score_source_code_linker import get_github_base_url

"""
This script's main usecase is to test consumers of Docs-As-Code with the new changes made in PR's. 
This enables us to find new issues and problems we introduce with changes that we otherwise would only know much later.
There are several things to note.

- The `print` function has been overwritten by the 'rich' package to allow for richer text output.
- The script itself takes quiet a bit of time, roughly 5+ min for a full run.
- If you need more output, enable it via `-v` or `-vv`  
- Start the script via the following command:
    - bazel run //src:ide_support
    - .venv/bin/python -m pytest -s src/tests   (If you need more verbosity add `-v` or `-vv`)
"""

# Max width of the printout
len_max = 80


LOGGER = logging.getLogger(__name__)
LOGGER.setLevel("DEBUG")


@dataclass
class ConsumerRepo:
    name: str
    git_url: str
    commands: list[str]
    test_commands: list[str]


@dataclass
class BuildOutput:
    returncode: int
    stdout: str
    stderr: str
    warnings: dict[str, list[str]] = field(default_factory=dict)


@dataclass
class Result:
    repo: str
    cmd: str
    local_or_git: str
    passed: bool
    reason: str


REPOS_TO_TEST: list[ConsumerRepo] = [
    ConsumerRepo(
        name="process_description",
        git_url="git@github.com:eclipse-score/process_description.git",
        commands=["bazel run //process:incremental_latest"],
        test_commands=[],
    ),
    ConsumerRepo(
        name="score",
        git_url="git@github.com:eclipse-score/score.git",
        commands=[
            "bazel run //docs:incremental_latest",
            "bazel run //docs:ide_support",
            "bazel run //docs:incremental_release",
            "bazel build //docs:docs_release",
            "bazel build //docs:docs_latest",
        ],
        test_commands=[],
    ),
    ConsumerRepo(
        name="module_template",
        git_url="git@github.com:eclipse-score/module_template.git",
        commands=[
            "bazel run //docs:ide_support",
            "bazel run //docs:incremental",
            "bazel build //docs:docs",
        ],
        test_commands=[
            "bazel test //tests/...",
        ],
    ),
]


@pytest.fixture(scope="session")
def sphinx_base_dir(tmp_path_factory: TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("testing_dir")


def get_current_git_commit(curr_path: Path):
    """
    Get the current git commit hash (HEAD).
    """
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        capture_output=True,
        text=True,
        check=True,
        cwd=curr_path,
    )
    return result.stdout.strip()


def get_remote_main_commit(curr_path: Path) -> str:
    """
    Get the commit hash of the remote main branch, to find possible metamodel changes
    """
    _ = subprocess.run(
        ["git", "fetch", "origin", "main"],
        capture_output=True,
        text=True,
        check=True,
        cwd=curr_path,
    )

    result = subprocess.run(
        ["git", "rev-parse", "origin/main"],
        capture_output=True,
        text=True,
        check=True,
        cwd=curr_path,
    )
    LOGGER.debug(f"Grabbed remote origin/main with commit: {result.stdout.strip()}")
    return result.stdout.strip()


def check_for_metamodel_change(curr_path: Path, remote_base_commit: str):
    """
    Check if there are any changes in the metamodel.yaml file.
    """
    try:
        # Get list of changed files
        result = subprocess.run(
            ["git", "diff", "--name-only", remote_base_commit, "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=curr_path,
        )

        changed_files = result.stdout.strip().split("\n")

        # Check if any changed files are in metamodel paths
        for file_path in changed_files:
            if "metamodel.yaml" in file_path:
                LOGGER.debug(
                    "Metamodel.yaml has changed. Ignoring 'score_metamodel' errors."
                )
                return True

        LOGGER.debug("Metamodel.yaml has NOT changed. Parsing all errors")
        return False

    except Exception as e:
        # Wondering if this is a good idea.
        # Or better to fail here?
        LOGGER.debug(f"Failed git diff. Error: {e}")
        return False


def replace_bazel_dep_with_local_override(module_content: str) -> str:
    """ """

    # Pattern to match the bazel_dep line
    pattern = rf'bazel_dep\(name = "score_docs_as_code", version = "[^"]+"\)'

    # Replacement with local_path_override
    replacement = f"""bazel_dep(name = "score_docs_as_code", version = "0.4.2")
local_path_override(
    module_name = "score_docs_as_code",
    path = "../docs_as_code"
)"""

    modified_content = re.sub(pattern, replacement, module_content)

    return modified_content


def replace_bazel_dep_with_git_override(
    module_content: str, git_hash: str, gh_url: str
) -> str:
    pattern = rf'bazel_dep\(name = "score_docs_as_code", version = "[^"]+"\)'

    replacement = f'''bazel_dep(name = "score_docs_as_code", version = "0.4.2")
git_override(
    module_name = "score_docs_as_code",
    remote = "{gh_url}",
    commit = "{git_hash}"
)'''

    modified_content = re.sub(pattern, replacement, module_content)

    return modified_content


def parse_bazel_output(BR: BuildOutput) -> BuildOutput:
    # HINT: All errors from sphinx / bazel commands are put into the stderr for some reason.
    err_lines = BR.stderr.splitlines()
    split_warnings = [x for x in err_lines if "WARNING: " in x]
    warning_dict: dict[str, list[str]] = defaultdict(list)

    for raw_warning in split_warnings:
        logger = "[NO SPECIFIC LOGGER]"
        file_and_warning = raw_warning
        # If this is the case we have a specific logger => therefore parsing it
        if raw_warning.endswith("]"):
            tmp_split_warning = raw_warning.split()
            logger = tmp_split_warning[-1].upper()  # [score_metamodel]
            file_and_warning = raw_warning.replace(logger, "").rstrip()
        warning_dict[logger].append(file_and_warning)
    BR.warnings = warning_dict
    return BR


def print_overview_logs(BR: BuildOutput, metamodel_changed: bool):
    warning_loggers = list(BR.warnings.keys())
    len_left_test_result = len_max - len("TEST RESULTS")
    print(
        f"[blue]{'=' * int(len_left_test_result / 2)}TEST RESULTS{'=' * int(len_left_test_result / 2)}[/blue]"
    )
    print(f"[navy_blue]{'=' * len_max}[/navy_blue]")
    warning_total_loggers_msg = f"Warning Loggers Total: {len(warning_loggers)}"
    len_left_loggers = len_max - len(warning_total_loggers_msg)
    print(
        f"[blue]{'=' * int(len_left_loggers / 2)}{warning_total_loggers_msg}{'=' * int(len_left_loggers / 2)}[/blue]"
    )
    warning_loggers = list(BR.warnings.keys())
    warning_total_msg = f"Logger Warnings Accumulated"
    len_left_loggers_total = len_max - len(warning_total_msg)
    print(
        f"[blue]{'=' * int(len_left_loggers_total / 2)}{warning_total_msg}{'=' * int(len_left_loggers_total / 2)}[/blue]"
    )
    for logger in warning_loggers:
        if len(BR.warnings[logger]) == 0:
            continue
        color = "orange1" if logger == "[NO SPECIFIC LOGGER]" else "red"
        warning_logger_msg = f"{logger} has {len(BR.warnings[logger])} warnings"
        if metamodel_changed and logger == "[SCORE_METAMODEL]":
            warning_logger_msg += "|| IGNORED DUE TO METAMODEL CHANGE"
            color = "orange1"
        len_left_logger = len_max - len(warning_logger_msg)
        print(
            f"[{color}]{'=' * int(len_left_logger / 2)}{warning_logger_msg}{'=' * int(len_left_logger / 2)}[/{color}]"
        )
    print(f"[blue]{'=' * len_max}[/blue]")


def verbose_printout(BR: BuildOutput):
    """Prints warnings for each logger when '-v' or higher is specified."""
    warning_loggers = list(BR.warnings.keys())
    for logger in warning_loggers:
        len_left_logger = len_max - len(logger)
        print(
            f"[cornflower_blue]{'=' * int(len_left_logger / 2)}{logger}{'=' * int(len_left_logger / 2)}[/cornflower_blue]"
        )
        warnings = BR.warnings[logger]
        len_left_warnings = len_max - len(f"Warnings Found: {len(warnings)}\n")
        color = "red"
        if logger == "[NO SPECIFIC LOGGER]":
            color = "orange1"
        print(
            f"[{color}]{'=' * int(len_left_warnings / 2)}{f'Warnings Found: {len(warnings)}'}{'=' * int(len_left_warnings / 2)}[/{color}]"
        )
        print("\n".join(f"[{color}]{x}[/{color}]" for x in warnings))


def print_running_cmd(repo: str, cmd: str, local_or_git: str):
    """Prints a 'Title Card' for the current command"""
    len_left_cmd = len_max - len(cmd)
    len_left_repo = len_max - len(repo)
    len_left_local = len_max - len(local_or_git)
    print(f"\n[cyan]{'=' * len_max}[/cyan]")
    print(
        f"[cornflower_blue]{'=' * int(len_left_repo / 2)}{repo}{'=' * int(len_left_repo / 2)}[/cornflower_blue]"
    )
    print(
        f"[cornflower_blue]{'=' * int(len_left_local / 2)}{local_or_git}{'=' * int(len_left_local / 2)}[/cornflower_blue]"
    )
    print(
        f"[cornflower_blue]{'=' * int(len_left_cmd / 2)}{cmd}{'=' * int(len_left_cmd / 2)}[/cornflower_blue]"
    )
    print(f"[cyan]{'=' * len_max}[/cyan]")


def analyze_build_success(BR: BuildOutput, metamodel_changed: bool) -> tuple[bool, str]:
    """
    Analyze if the build should be considered successful based on your rules.

    Rules:
    - '[NO SPECIFIC LOGGER]' warnings are always ignored
    - '[SCORE_METAMODEL]' warnings are ignored only if metamodel_changed is True
    """

    # Unsure if this is good, as sometimes the returncode is 1 but it should still go through?
    # Logging for feedback here
    if BR.returncode != 0:
        return False, f"Build failed with return code {BR.returncode}"

    # Check for critical/non ignored warnings
    critical_warnings = []

    for logger, warnings in BR.warnings.items():
        if logger == "[NO SPECIFIC LOGGER]":
            # Always ignore these
            continue
        elif logger == "[SCORE_METAMODEL]":
            # Only ignore if metamodel changed
            if not metamodel_changed:
                critical_warnings.extend(warnings)
        else:
            # Any other logger is critical/not ignored
            critical_warnings.extend(warnings)

    if critical_warnings:
        return False, f"Found {len(critical_warnings)} critical warnings"

    return True, "Build successful - no critical warnings"


def print_final_result(
    BR: BuildOutput, metamodel_changed: bool, repo_name: str, cmd: str, pytestconfig
):
    """
    Print your existing detailed output plus a clear success/failure summary
    """
    print_overview_logs(BR, metamodel_changed)
    if pytestconfig.get_verbosity() >= 1:
        # Verbosity Level 1 (-v)
        verbose_printout(BR)
    if pytestconfig.get_verbosity() >= 2:
        # Verbosity Level 2 (-vv)
        print("==== STDOUT ====:\n\n", BR.stdout)
        print("==== STDERR ====:\n\n", BR.stderr)

    is_success, reason = analyze_build_success(BR, metamodel_changed)

    status = "OK PASSED" if is_success else "XX FAILED"
    color = "green" if is_success else "red"

    # Printing a small 'report' for each cmd.
    result_msg = f"{repo_name} - {cmd}: {status}"
    len_left = len_max - len(result_msg)
    print(
        f"[{color}]{'=' * int(len_left / 2)}{result_msg}{'=' * int(len_left / 2)}[/{color}]"
    )
    print(f"[{color}]Reason: {reason}[/{color}]")
    print(f"[{color}]{'=' * len_max}[/{color}]")

    return is_success, reason


def print_result_table(results: list[Result]):
    """Printing an 'overview' table to show all results."""
    table = Table(title="Docs-As-Code Consumer Test Result")
    table.add_column("Repository")
    table.add_column("CMD")
    table.add_column("LOCAL OR GIT")
    table.add_column("PASSED")
    table.add_column("REASON")
    for result in results:
        style = "green" if result.passed else "red"
        table.add_row(
            result.repo,
            result.cmd,
            result.local_or_git,
            str(result.passed),
            result.reason,
            style=style,
        )
    print(table)


# Updated version of your test loop
def test_and_clone_repos_updated(sphinx_base_dir, pytestconfig):
    # Setting up the Test Environment

    # This might be hacky, but currently the best way I could solve the issue of going to the right place.
    os.chdir(sphinx_base_dir)
    curr_path = Path(__file__).parent
    # Finding git_root is needed to enable local overrides.
    git_root = find_git_root(curr_path)

    # I think we need git_root, otherwise the rest makes not much sense.
    if git_root is None:
        assert False, "Git root was none"

    # Getting GH_URL & current hash to enable git override
    gh_url = get_github_base_url(git_root)
    current_hash = get_current_git_commit(curr_path)

    # Symlink local docs-as-code => sphinx tmp
    docs_as_code_dest = sphinx_base_dir / "docs_as_code"
    docs_as_code_dest.symlink_to(git_root)

    # Calculating / Checking if the metamodel.yaml has changed, to determin if [score_metamodel] errors should be disablede
    remote_main_commit = get_remote_main_commit(curr_path)
    metamodel_changed = check_for_metamodel_change(curr_path, remote_main_commit)

    overall_success = True

    # We capture the results for each command run.
    results: list[Result] = []

    for repo in REPOS_TO_TEST:
        # Cloning the repo to the temporary directories
        subprocess.run(["git", "clone", repo.git_url], check=True, capture_output=True)
        os.chdir(repo.name)
        # Reading the original MODULE.bazel to enable manipulation later
        with open("MODULE.bazel", "r") as f:
            module_orig = f.read()
        # Preparing local & git overrides for later use
        module_local_override = replace_bazel_dep_with_local_override(module_orig)
        module_git_override = replace_bazel_dep_with_git_override(
            module_orig, current_hash, gh_url
        )
        with open("MODULE.bazel", "w") as f:
            f.write(module_local_override)
        for cmd in repo.commands:
            # Running through all 'cmds' specified with the local override
            print_running_cmd(repo.name, cmd, "LOCAL OVERRIDE")

            out = subprocess.run(cmd.split(), capture_output=True, text=True)

            BR = BuildOutput(
                returncode=out.returncode,
                stdout=str(out.stdout),
                stderr=str(out.stderr),
            )
            BR_parsed = parse_bazel_output(BR)

            is_success, reason = print_final_result(
                BR_parsed, metamodel_changed, repo.name, cmd, pytestconfig
            )

            results.append(
                Result(
                    repo=repo.name,
                    cmd=cmd,
                    local_or_git="local",
                    passed=is_success,
                    reason=reason,
                )
            )

            if not is_success:
                overall_success = False

        for test_cmd in repo.test_commands:
            # Running through all 'test cmds' specified with the local override
            print_running_cmd(repo.name, test_cmd, "LOCAL OVERRIDE")
            out = subprocess.run(test_cmd.split(), capture_output=True, text=True)

            BR = BuildOutput(
                returncode=out.returncode,
                stdout=str(out.stdout),
                stderr=str(out.stderr),
            )
            BR_parsed = parse_bazel_output(BR)

            is_success, reason = print_final_result(
                BR_parsed, metamodel_changed, repo.name, test_cmd, pytestconfig
            )

            results.append(
                Result(
                    repo=repo.name,
                    cmd=test_cmd,
                    local_or_git="local",
                    passed=is_success,
                    reason=reason,
                )
            )

            if not is_success:
                overall_success = False

        with open("MODULE.bazel", "w") as f:
            f.write(module_git_override)
        for cmd in repo.commands:
            # Running through all 'cmds' specified with the git override
            print_running_cmd(repo.name, cmd, "GIT OVERRIDE")

            out = subprocess.run(cmd.split(), capture_output=True, text=True)

            BR = BuildOutput(
                returncode=out.returncode,
                stdout=str(out.stdout),
                stderr=str(out.stderr),
            )
            BR_parsed = parse_bazel_output(BR)

            is_success, reason = print_final_result(
                BR_parsed, metamodel_changed, repo.name, cmd, pytestconfig
            )

            results.append(
                Result(
                    repo=repo.name,
                    cmd=cmd,
                    local_or_git="git",
                    passed=is_success,
                    reason=reason,
                )
            )

            if not is_success:
                overall_success = False

        for test_cmd in repo.test_commands:
            # Running through all 'test cmds' specified with the git override
            print_running_cmd(repo.name, test_cmd, "GIT OVERRIDE")
            out = subprocess.run(test_cmd.split(), capture_output=True, text=True)

            BR = BuildOutput(
                returncode=out.returncode,
                stdout=str(out.stdout),
                stderr=str(out.stderr),
            )
            BR_parsed = parse_bazel_output(BR)

            is_success, reason = print_final_result(
                BR_parsed, metamodel_changed, repo.name, test_cmd, pytestconfig
            )
            results.append(
                Result(
                    repo=repo.name,
                    cmd=test_cmd,
                    local_or_git="git",
                    passed=is_success,
                    reason=reason,
                )
            )

            if not is_success:
                overall_success = False

        # NOTE: We have to change directories back to the parent, otherwise the cloning & override will not be correct
        os.chdir(Path.cwd().parent)

    # Printing a 'overview' table as a result
    print_result_table(results)
    assert overall_success, (
        "Consumer Tests failed, see table for which commands specifically. Enable verbosity for warning/error printouts"
    )
