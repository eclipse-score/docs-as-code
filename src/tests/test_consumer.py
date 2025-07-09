import json
from collections.abc import Callable
from pathlib import Path

import subprocess
import pytest
import os
import re
from pytest import TempPathFactory
from typing import Optional
from sphinx.testing.util import SphinxTestApp
from sphinx_needs.data import SphinxNeedsData
from dataclasses import dataclass

@dataclass
class ConsumerRepo():
    name: str
    git_url: str
    commands: list[str] 
    test_commands: list[str]
    LocalOverrideResult: bool
    GitOverrideResult: bool


REPOS_TO_TEST: list[ConsumerRepo] = [
    # ConsumerRepo(
    #         name="process_description",
    #         git_url= "git@github.com:eclipse-score/process_description.git",
    #         commands=["bazel run //process:incremental_latest"],
    #         LocalOverrideResult=False,
    #         GitOverrideResult=False,
    #         test_commands= []
    # ),
    # ConsumerRepo(
    #         name="score",
    #         git_url= "git@github.com:eclipse-score/score.git",
    #         commands=[
    #             "bazel run //docs:incremental_latest",
    #             "bazel run //docs:incremental_release",
    #             "bazel run //docs:ide_support",
    #             "bazel build //docs:docs_release",
    #             "bazel build //docs:docs_latest",
    #         ],
    #         LocalOverrideResult=False,
    #         GitOverrideResult=False,
    #         test_commands= []
    # ),
    ConsumerRepo(
            name="module_template",
            git_url= "git@github.com:eclipse-score/module_template.git",
            commands=[
                "bazel run //docs:ide_support",
                # "bazel run //docs:incremental",
                # "bazel build //docs:docs",
            ],
            LocalOverrideResult=False,
            GitOverrideResult=False,
            test_commands= [
            "bazel test //tests/...",
        ]
    )
]


@pytest.fixture(scope="session")
def sphinx_base_dir(tmp_path_factory: TempPathFactory) -> Path:
    return tmp_path_factory.mktemp("testing_dir")


def get_current_git_commit(curr_path):
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




def replace_bazel_dep_with_local_override(module_content):
    """
    """
    
    # Pattern to match the bazel_dep line
    pattern = rf'bazel_dep\(name = "score_docs_as_code", version = "0.4.1"\)'
    
    # Replacement with local_path_override
    replacement = f'''bazel_dep(name = "score_docs_as_code", version = "0.4.1")
local_path_override(
    module_name = "score_docs_as_code",
    path = "../docs_as_code"
)'''
    
    # Replace the pattern
    modified_content = re.sub(pattern, replacement, module_content)
    
    return modified_content

def replace_bazel_dep_with_git_override(module_content, git_hash):
    """
    """
    import re
    
    # Pattern to match the bazel_dep line
    pattern = rf'bazel_dep\(name = "score_docs_as_code", version = "0.4.1"\)'
    
    # Replacement with local_path_override
    replacement = f'''bazel_dep(name = "score_docs_as_code", version = "0.4.1")
git_override(
    module_name = "score_docs_as_code",
    repsoitory = 
    commit = "{git_hash}"
)'''
    
    # Replace the pattern
    modified_content = re.sub(pattern, replacement, module_content)
    
    return modified_content

def test_and_clone_repos(sphinx_base_dir):
    # Clone 
    os.chdir(sphinx_base_dir)
    current_hash = get_current_git_commit(Path(__file__).parent)
    for repo in REPOS_TO_TEST:
        # CLoning the repo
        subprocess.run(["git", "clone", repo.git_url], check=True, capture_output=True)
        os.chdir(repo.name)
        with open("MODULE.bazel", "r") as f:
            module_orig = f.read()
        module_local_override = replace_bazel_dep_with_local_override(module_orig)
        module_git_override = replace_bazel_dep_with_git_override(module_orig, current_hash)
        with open("MODULE.bazel", "w") as f:
            f.write(module_local_override)
        # TEST all commands
        for cmd in repo.commands:
            print("BUILDING WITH LOCAL OVERRIDE")
            out = subprocess.run(cmd.split(), capture_output=True, check=True, text=True)
            #print(out)
            #assert out.returncode == 0
            assert "Build completed successfully" in str(out.stderr) 
        for test_cmd in repo.test_commands:
            print("TESTING WITH LOCAL OVERRIDE")
            out = subprocess.run(test_cmd.split(), capture_output=True, check=True, text=True)
            assert out.returncode == 0
        with open("MODULE.bazel", "w") as f:
            f.write(module_git_override)
        for cmd in repo.commands:
            print("TESTING WITH GIt OVERRIDE")
            out = subprocess.run(cmd.split(), capture_output=True, check=True, text=True)
            #print(out)
            #assert out.returncode == 0
            assert "Build completed successfully" in str(out.stderr)
        os.chdir(Path.cwd().parent)
        # Now need to adapt the MODULE.bazel file.
   

