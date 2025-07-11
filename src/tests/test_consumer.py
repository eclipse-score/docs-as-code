import json
from collections.abc import Callable
from pathlib import Path

import subprocess
from sys import stderr
from warnings import warn
from github import BadUserAgentException
import pytest
import os
import re
import logging


from collections import defaultdict
from pytest import TempPathFactory
from typing import Optional
from sphinx.testing.util import SphinxTestApp
from sphinx_needs.data import SphinxNeedsData
from dataclasses import dataclass, field

from src.extensions.score_source_code_linker.generate_source_code_links_json import (
    find_git_root,
)

# Do not need the sphinx logger => Normal python logger instead.
LOGGER = logging.getLogger(__name__)
LOGGER.setLevel("DEBUG")


@dataclass
class ConsumerRepo:
    name: str
    git_url: str
    commands: list[str]
    test_commands: list[str]


@dataclass
class BuildResult:
    returncode: int
    stdout: str
    stderr: str
    warnings: dict[str, list[str]] = field(default_factory=dict)
    LocalOverrideResult: bool = False
    GitOverrideResult: bool = False




REPOS_TO_TEST: list[ConsumerRepo] = [
    # ConsumerRepo(
    #         name="process_description",
    #         git_url= "git@github.com:eclipse-score/process_description.git",
    #         commands=["bazel run //process:incremental_latest"],
    #         LocalOverrideResult=False,
    #         GitOverrideResult=False,
    #         test_commands= []
    # ),
    ConsumerRepo(
        name="score",
        git_url="git@github.com:eclipse-score/score.git",
        commands=[
            # "bazel run //docs:incremental_latest",
            "bazel run //docs:incremental_release",
            # "bazel run //docs:ide_support",
            # "bazel build //docs:docs_release",
            # "bazel build //docs:docs_latest",
        ],
        test_commands=[],
    ),
    # ConsumerRepo(
    #     name="module_template",
    #     git_url="git@github.com:eclipse-score/module_template.git",
    #     commands=[
    #         "bazel run //docs:ide_support",
    #         "bazel run //docs:incremental",
    #         "bazel build //docs:docs",
    #     ],
    #     test_commands=[
    #         "bazel test //tests/...",
    #     ],
    # )
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
    Check if there are any changes in the metamodel.
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


def replace_bazel_dep_with_local_override(module_content):
    """ """

    # Pattern to match the bazel_dep line
    pattern = rf'bazel_dep\(name = "score_docs_as_code", version = "[^"]+"\)'

    # Replacement with local_path_override
    replacement = f"""bazel_dep(name = "score_docs_as_code", version = "0.4.2")
local_path_override(
    module_name = "score_docs_as_code",
    path = "../docs_as_code"
)"""

    # Replace the pattern
    modified_content = re.sub(pattern, replacement, module_content)

    return modified_content


def replace_bazel_dep_with_git_override(module_content, git_hash):
    """ """
    import re

    # Pattern to match the bazel_dep line
    pattern = rf'bazel_dep\(name = "score_docs_as_code", version = "[^"]+"\)'

    # Replacement with local_path_override
    replacement = f'''bazel_dep(name = "score_docs_as_code", version = "0.4.2")
git_override(
    module_name = "score_docs_as_code",
    repsoitory = 
    commit = "{git_hash}"
)'''

    # Replace the pattern
    modified_content = re.sub(pattern, replacement, module_content)

    return modified_content


def parse_bazel_output(BR: BuildResult) -> BuildResult:
    # HINT: All errors from sphinx / bazel commands are put into the stderr for some reason.
    err_lines = BR.stderr.splitlines()
    split_warnings = [x for x in err_lines if "WARNING: " in x]
    warning_dict: dict[str, list[str]] = defaultdict(list)
     
    for raw_warning in split_warnings:
        logger = "[NO SPECIFIC LOGGER]"
        file_and_warning = raw_warning
        if raw_warning.endswith("]"):
            tmp_split_warning = raw_warning.split() 
            logger = tmp_split_warning[-1] # [score_metamodel]
            file_and_warning = raw_warning.replace(logger, "").rstrip()

        warning_dict[logger].append(file_and_warning)
    BR.warnings = warning_dict
    print(BR.warnings)
    # "[score_metamodel]": [warning1, warning2, warning3, ...], "[NO SPECIFIC LOGGER]": [warning1, warning2,...]
    return BR

def aggregate_results(BR: BuildResult) ->str:
    result = ""
    warning_loggers = list(BR.warnings.keys())
    result += f"Warning Loggers Total: {len(warning_loggers)}\n"
    for logger in warning_loggers:  
        result += f"========={logger}========\n"
        warnings = BR.warnings[logger]
        result += f"Warnings Found: {len(warnings)}\n"
        result += "\n".join(x for x in warnings)
    return result

def print_build_result(BR: BuildResult, metamodel_changed: bool):
    metamodel_warnings = BR.warnings.get('[score_metamodel]', [])
    warning_loggers = [x for x in BR.warnings.keys() if x != "[NO SPECIFIC LOGGER]"]
    LOGGER.info("=============================================")
    LOGGER.info("=========BAZEL CONSUMER TEST RESULTS=========")
    LOGGER.info("=============================================")
    results = aggregate_results(BR)
    if metamodel_changed:
        LOGGER.info("============METAMODEL HAS CHANGED=============")
        LOGGER.info("=[SCORE_METAMODEL] WARNINGS DISPLAYED AS INFO=")
        LOGGER.info("\n".join(x for x in metamodel_warnings))
        LOGGER.info("========[SCORE_METAMODEL] WARNINGS END========")
    LOGGER.info(results)
    pass 

def test_and_clone_repos(sphinx_base_dir):
    # Clone
    # This might not be the best idea
    os.chdir(sphinx_base_dir)
    curr_path = Path(__file__).parent
    git_root = find_git_root(curr_path)
    docs_as_code_dest = sphinx_base_dir / "docs_as_code"
    docs_as_code_dest.symlink_to(git_root)
    current_hash = get_current_git_commit(curr_path)
    remote_main_commit = get_remote_main_commit(curr_path)
    metamodel_changed = check_for_metamodel_change(curr_path, remote_main_commit)

    for repo in REPOS_TO_TEST:
        # CLoning the repo
        subprocess.run(["git", "clone", repo.git_url], check=True, capture_output=True)
        os.chdir(repo.name)
        with open("MODULE.bazel", "r") as f:
            module_orig = f.read()
        module_local_override = replace_bazel_dep_with_local_override(module_orig)
        module_git_override = replace_bazel_dep_with_git_override(
            module_orig, current_hash
        )
        with open("MODULE.bazel", "w") as f:
            f.write(module_local_override)
        # TEST all commands
        for cmd in repo.commands:
            out = subprocess.run(
                cmd.split(), capture_output=True, check=True, text=True
            )
            out_both = str(out.stdout) + "\n\n" + str(out.stderr)

            BR = BuildResult(
                returncode=out.returncode,
                stdout=str(out.stdout),
                stderr=str(out.stderr),
            )
            BR_parsed = parse_bazel_output(BR)
            print_build_result(BR_parsed, metamodel_changed)

            # print(out)
            # assert out.returncode == 0
            # assert "Build completed successfully" in str(out.stderr)
            # assert "feat_req__feo__activity_shutdown: parent need `stkh_req__app_architectures__support_data` does not fulfill condition `safety == QM`. [score_metamodel]" in str(out_both)
            assert False
        for test_cmd in repo.test_commands:
            pass
            #print("TESTING WITH LOCAL OVERRIDE")
            #out = subprocess.run(
            #    test_cmd.split(), capture_output=True, check=True, text=True
            #)
            #assert out.returncode == 0
        with open("MODULE.bazel", "w") as f:
            f.write(module_git_override)
        for cmd in repo.commands:
            print("TESTING WITH GIt OVERRIDE")
            out = subprocess.run(
                cmd.split(), capture_output=True, check=True, text=True
            )
            # print(out)
            # assert out.returncode == 0
            BR = BuildResult(
                returncode=out.returncode, stdout=str(out.stdout), stderr=str(out.stderr)
             )
            parse_bazel_output(BR)
            assert "Build completed successfully" in str(out.stderr)
        os.chdir(Path.cwd().parent)
        # Now need to adapt the MODULE.bazel file.
