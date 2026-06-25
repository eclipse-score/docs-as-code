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
"""
Consumer tests: verify that downstream repos build successfully against this branch.

Via Python (requires ide_support to have been run first):
    bazel run //:ide_support  # once, to set up .venv_docs
    python -m pytest src/tests/test_consumer.py -s
    python -m pytest src/tests/test_consumer.py -k "score and local"
    python -m pytest src/tests/test_consumer.py -k "process_description"
    python -m pytest src/tests/test_consumer.py --disable-cache

Known non-passing tests are sometimes marked xfail and do not count as failures.
"""

import re
import shutil
import subprocess
import warnings
from dataclasses import dataclass
from pathlib import Path

import pytest
from pytest import TempPathFactory

from src.helper_lib import find_git_root, get_current_git_hash, get_github_base_url

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

CACHE_DIR = Path.home() / ".cache" / "docs_as_code_consumer_tests"

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass
class ConsumerRepo:
    name: str
    git_url: str
    commands: list[str]

    def __init__(
        self, name: str, git_url: str | None = None, commands: list[str] | None = None
    ) -> None:
        self.name = name

        if git_url:
            self.git_url = git_url
        else:
            self.git_url = f"https://github.com/eclipse-score/{name}.git"

        if commands:
            self.commands = commands
        else:
            # The minimum is to ensure that the repo can build against the current score_docs_as_code branch.
            # If docs works, then usually docs_checl and needs_json will work as well.
            self.commands = ["bazel run //:docs"]


REPOS_TO_TEST: list[ConsumerRepo] = [
    ConsumerRepo(
        name="process_description",
        commands=[
            "bazel run //:ide_support",
            "bazel run //:docs_check",
            "bazel run //:docs",
            "bazel build //:needs_json",
        ],
    ),
    ConsumerRepo(
        name="score",
        commands=[
            "bazel run //:ide_support",
            "bazel run //:docs_check",
            "bazel run //:docs",
            "bazel build //:needs_json",
        ],
    ),
    ConsumerRepo(
        name="module_template",
        commands=[
            "bazel run //:ide_support",
            "bazel run //:docs_check",
            "bazel run //:docs",
            "bazel build //:needs_json",
            "bazel test //tests/...",
        ],
    ),
    ConsumerRepo(name="infrastructure"),
    ConsumerRepo(name="itf"),
    ConsumerRepo(name="baselibs"),
    ConsumerRepo(name="inc_someip_gateway"),
]

# ---------------------------------------------------------------------------
# MODULE.bazel manipulation
# ---------------------------------------------------------------------------


def _strip_score_docs_overrides(content: str) -> str:
    """Comment out any existing *_override blocks for score_docs_as_code."""
    lines = content.splitlines()
    result = []
    i = 0
    while i < len(lines):
        line = lines[i]
        # Check if this line starts an *_override block (e.g. git_override, local_path_override)
        if re.match(r"^\s*\w+_override\s*\(", line):
            # Collect the entire block by tracking parenthesis depth
            block_start = i
            depth = line.count("(") - line.count(")")
            i += 1
            while i < len(lines) and depth > 0:
                depth += lines[i].count("(") - lines[i].count(")")
                i += 1
            # Extract the block
            block = lines[block_start:i]
            block_text = "\n".join(block)
            # Comment out if it's for score_docs_as_code
            if (
                'module_name = "score_docs_as_code"' in block_text
                or "module_name = 'score_docs_as_code'" in block_text
            ):
                result.extend("# " + ln if ln.strip() else "#" for ln in block)
            else:
                result.extend(block)
        else:
            result.append(line)
            i += 1
    return "\n".join(result) + ("\n" if content.endswith("\n") else "")


# Match bazel_dep with required name and optional version attribute (anchored to line start, MULTILINE flag required)
# ^bazel_dep\(name = ["']score_docs_as_code["']  — literal call with either quote style
# (?:, version = ["'][^"']+["'])?                 — optional version argument, any value
# \)                                              — closing paren
_BAZEL_DEP_PATTERN = r"""^bazel_dep\(name = ["']score_docs_as_code["'](?:, version = ["'][^"']+["'])?\)"""


def _write_module_bazel(
    repo_path: Path, override_type: str, commit: str, remote: str
) -> None:
    """Overwrite MODULE.bazel with the requested override type applied."""
    original = (repo_path / "MODULE.bazel").read_text(encoding="utf-8")
    base = _strip_score_docs_overrides(original)

    if override_type == "local":
        replacement = """bazel_dep(name = "score_docs_as_code")
local_path_override(
    module_name = "score_docs_as_code",
    path = "../docs_as_code"
)"""
    else:
        replacement = f"""bazel_dep(name = "score_docs_as_code")
git_override(
    module_name = "score_docs_as_code",
    remote = "{remote}",
    commit = "{commit}"
)"""

    (repo_path / "MODULE.bazel").write_text(
        re.sub(_BAZEL_DEP_PATTERN, replacement, base, flags=re.MULTILINE),
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# Repo helpers
# ---------------------------------------------------------------------------

_cloned: set[Path] = set()


def _ensure_repo(repo_path: Path, git_url: str, use_cache: bool) -> None:
    """Clone or update a repo exactly once per session per path."""
    if repo_path in _cloned:
        return
    if repo_path.exists():
        if use_cache:
            subprocess.run(
                ["git", "fetch", "origin"],
                check=True,
                capture_output=True,
                cwd=repo_path,
            )
            subprocess.run(
                ["git", "reset", "--hard", "origin/main"],
                check=True,
                capture_output=True,
                cwd=repo_path,
            )
        else:
            shutil.rmtree(repo_path)
            subprocess.run(
                ["git", "clone", git_url],
                check=True,
                capture_output=True,
                cwd=repo_path.parent,
            )
    else:
        subprocess.run(
            ["git", "clone", git_url],
            check=True,
            capture_output=True,
            cwd=repo_path.parent,
        )
    _cloned.add(repo_path)


def _cleanup_before_cmd(cwd: Path, cmd: str) -> None:
    # ubproject.toml is created by :docs
    for p in cwd.glob("*/ubproject.toml"):
        p.unlink()

    # _build is created by :docs
    shutil.rmtree(cwd / "_build", ignore_errors=True)

    # for ide_support, also clear the venv and bazel cache to ensure a clean slate
    if cmd == "bazel run //:ide_support":
        shutil.rmtree(cwd / ".venv_docs", ignore_errors=True)
        subprocess.run(["bazel", "clean", "--async"], check=True, text=True, cwd=cwd)


def _run_bazel_cmd(cmd: str, repo_name: str, cwd: Path) -> None:
    """Stream a bazel command to stdout; fail on non-zero exit, warn on WARNING lines."""
    process = subprocess.Popen(
        cmd.split(),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1,
        cwd=cwd,
    )

    assert process.stdout is not None
    for line in process.stdout:
        print(line, end="")
        if "WARNING" in line:
            warnings.warn(f"{repo_name} `{cmd}`: {line.strip()}", stacklevel=2)
    process.stdout.close()

    rc = process.wait()
    if rc != 0:
        pytest.fail(
            f"`{cmd}` in {repo_name} exited with code {rc}",
            pytrace=False,
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def repos_base_dir(
    tmp_path_factory: TempPathFactory, pytestconfig: pytest.Config
) -> Path:
    if pytestconfig.getoption("--disable-cache"):
        return tmp_path_factory.mktemp("consumer_tests")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return CACHE_DIR


@pytest.fixture(scope="module")
def consumer_env(repos_base_dir: Path) -> tuple[str, str]:
    """Resolve git metadata and set up the local symlink used by local_path_override."""
    git_root = find_git_root()
    assert git_root, "Git root not found"

    dest = repos_base_dir / "docs_as_code"
    if dest.is_symlink():
        dest.unlink()
    elif dest.is_dir():
        shutil.rmtree(dest)
    dest.symlink_to(git_root)

    return get_github_base_url(git_root), get_current_git_hash(git_root)


# ---------------------------------------------------------------------------
# Remote-availability check (computed once at collection time)
# ---------------------------------------------------------------------------


def _check_remote_available() -> tuple[bool, str]:
    """Return (available, reason). Called once at module import."""
    git_root = find_git_root()
    if git_root is None:
        return False, "git root not found"

    dirty = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        cwd=git_root,
    ).stdout.strip()
    if dirty:
        return (
            False,
            "working tree has uncommitted changes; git_override would not reflect local state",
        )

    pushed = subprocess.run(
        ["git", "branch", "-r", "--contains", "HEAD"],
        capture_output=True,
        text=True,
        cwd=git_root,
    ).stdout.strip()
    if not pushed:
        return (
            False,
            "HEAD has not been pushed to any remote; git_override would reference an unavailable commit",
        )

    return True, ""


_REMOTE_AVAILABLE, _REMOTE_SKIP_REASON = _check_remote_available()

# ---------------------------------------------------------------------------
# Test parametrization
# ---------------------------------------------------------------------------


def _cmd_id(cmd: str) -> str:
    target = cmd.split()[-1].replace("//:", "").replace("//", "")
    return target.replace("...", "all").replace("/", "_").replace(":", "_")


def _make_params() -> list[pytest.param]:  # type: ignore[type-arg]
    params = []
    for repo in REPOS_TO_TEST:
        for override in ("local", "remote"):
            for cmd in repo.commands:
                marks = []
                if (
                    repo.name == "module_template"
                    and cmd == "bazel build //:needs_json"
                ):
                    marks.append(
                        pytest.mark.xfail(
                            reason="needs_json in module_template is currently broken",
                            strict=False,
                        )
                    )
                params.append(
                    pytest.param(
                        repo,
                        override,
                        cmd,
                        marks=marks,
                        id=f"{repo.name}-{override}-{_cmd_id(cmd)}",
                    )
                )
    return params  # pyright: ignore[reportUnknownVariableType]


@pytest.mark.parametrize("repo, override_type, cmd", _make_params())
def test_consumer_repo(
    repo: ConsumerRepo,
    override_type: str,
    cmd: str,
    repos_base_dir: Path,
    consumer_env: tuple[str, str],
    pytestconfig: pytest.Config,
) -> None:
    if override_type == "remote" and not _REMOTE_AVAILABLE:
        pytest.fail(_REMOTE_SKIP_REASON, pytrace=False)

    gh_url, current_hash = consumer_env
    use_cache = not bool(pytestconfig.getoption("--disable-cache"))

    repo_path = repos_base_dir / repo.name
    _ensure_repo(repo_path, repo.git_url, use_cache)
    _write_module_bazel(repo_path, override_type, current_hash, gh_url)
    _cleanup_before_cmd(repo_path, cmd)
    _run_bazel_cmd(cmd, repo.name, repo_path)
