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
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


def _log_debug(message: str):
    # TODO: why does logger not print anything?
    if logger.hasHandlers():
        logger.debug(message)
    else:
        print(message)


def find_git_root() -> Path:
    # TODO: is __file__ ever resolved into the bazel cache directories?
    # Then this function will not work!
    workspace = os.getenv("BUILD_WORKSPACE_DIRECTORY")
    if workspace:
        return Path(workspace)

    for parent in Path(__file__).resolve().parents:
        if (parent / ".git").exists():
            return parent

    sys.exit(
        "Could not find git root. "
        "Please run this script from the root of the repository."
    )


def get_runfiles_dir_impl(
    cwd: Path,
    conf_dir: Path,
    env_runfiles: Path | None,
    git_root: Path,
) -> Path:
    """Functional (and therefore testable) logic to determine the runfiles directory."""

    _log_debug(
        f"get_runfiles_dir_impl(\n  cwd={cwd},\n  conf_dir={conf_dir},\n"
        f"  env_runfiles={env_runfiles},\n  git_root={git_root}\n)"
    )

    if env_runfiles:
        # Runfiles are only available when running in Bazel.
        # Both `bazel build` and `bazel run` are supported.
        # i.e. `bazel build //:docs` and `bazel run //:docs`.
        _log_debug("Using env[RUNFILES_DIR] to find the runfiles...")

        if env_runfiles.is_absolute() and "bazel-out" in env_runfiles.parts:
            # In case of `bazel run` it will point to the global cache directory,
            # which has a new hash every time. And it's not pretty.
            # However, `bazel-out` is a symlink to that same cache directory!
            try:
                idx = env_runfiles.parts.index("bazel-out")
                runfiles_dir = git_root.joinpath(*env_runfiles.parts[idx:])
                _log_debug(f"Made runfiles dir pretty: {runfiles_dir}")
            except ValueError:
                sys.exit("Could not find bazel-out in runfiles path.")
        else:
            runfiles_dir = git_root / env_runfiles

    else:
        # The only way to land here is when running from within the virtual
        # environment created by the `:ide_support` rule.
        # i.e. esbonio or manual sphinx-build execution within the virtual
        # environment.
        _log_debug("Running outside bazel.")

        # TODO: "process-docs" is in SOURCE_DIR!!
        runfiles_dir = git_root / "bazel-bin" / "process-docs" / "ide_support.runfiles"

    return runfiles_dir


def get_runfiles_dir() -> Path:
    """Runfiles directory relative to conf.py"""

    # FIXME CONF_DIRECTORY is our invention. When running from esbonio, this is not
    # set. It seems to provide app.confdir instead...
    conf_dir = os.getenv("CONF_DIRECTORY")
    assert conf_dir

    env_runfiles = os.getenv("RUNFILES_DIR")

    runfiles = Path(
        get_runfiles_dir_impl(
            cwd=Path(os.getcwd()),
            conf_dir=Path(conf_dir),
            env_runfiles=Path(env_runfiles) if env_runfiles else None,
            git_root=find_git_root(),
        )
    )

    if not runfiles.exists():
        sys.exit(
            f"Could not find runfiles at {runfiles}. Have a look at "
            "README.md for instructions on how to build docs."
        )

    return runfiles
