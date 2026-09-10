# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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

from enum import Enum
from pathlib import Path

from python.runfiles import Runfiles

from src.helper_lib import Environment, find_git_root


class ExecutionEnvironment(Enum):
    BAZEL_RUN = "bazel_run"
    BAZEL_BUILD = "bazel_build"
    DIRECT = "direct"


class DocsCliConfig:
    """Configuration consumed by the documentation launcher.

    Keeping environment parsing in one place lets the launcher operate on a
    stable configuration object. Paths stored on this object are resolved to
    the filesystem visible to the current process. The logical package and
    source paths remain available for repository metadata such as GitHub edit
    links.
    """

    def _identify_environment(self) -> ExecutionEnvironment:
        """Identify how the current Python process was started."""
        if self.ws_root:
            return ExecutionEnvironment.BAZEL_RUN
        if self._runfiles:
            return ExecutionEnvironment.BAZEL_BUILD
        return ExecutionEnvironment.DIRECT

    @property
    def is_bazel_build(self):
        """Whether this configuration belongs to the sandboxed Needs action."""
        return self.environment == ExecutionEnvironment.BAZEL_BUILD

    @property
    def is_bazel_run(self):
        """Whether this configuration belongs to a ``bazel run`` target."""
        return self.environment == ExecutionEnvironment.BAZEL_RUN

    @property
    def is_direct(self):
        """Whether the launcher was started outside Bazel."""
        return self.environment == ExecutionEnvironment.DIRECT

    @classmethod
    def from_environment(cls, env: Environment | None = None) -> "DocsCliConfig":
        """Load configuration from the process environment or a test mapping."""
        return cls(env if env is not None else Environment())

    def __init__(self, env: Environment):
        """
        Load launcher configuration from the current Bazel environment.

        Specifically, this method handles bazel build and run differences.
        """

        # These three must be queried first:
        self.ws_root = env.optional_path("BUILD_WORKSPACE_DIRECTORY")
        self._runfiles = Runfiles.Create()
        self.environment = self._identify_environment()

        # Then fill the rest as required:
        if self.is_bazel_build or self.is_bazel_run:
            # git_root exists only in direct mode... and even then its optional!
            self.git_root = find_git_root()

        self.action = env.get("ACTION")

        # Sanity checks
        if self.ws_root:
            self._require_directory(self.ws_root, "BUILD_WORKSPACE_DIRECTORY")

    def _resolve_input_path(self, path: Path) -> Path | None:
        """
        Resolve an optional config input in its current execution context.
        """
        if self.is_bazel_build or self.is_bazel_run:
            # Interactive Bazel targets receive runfiles-relative paths from
            # ``rlocationpath``. The runfiles tree is the only stable location
            # for generated files and external repository inputs.
            assert self._runfiles
            loc = self._runfiles.Rlocation(str(path))
            return Path(loc).absolute() if loc else None
        else:
            # Direct invocations resolve relative inputs from the workspace or
            # current working directory.
            base = self.ws_root or Path.cwd()
            return (base / path).absolute()

    @staticmethod
    def _require_directory(path: Path, environment_name: str) -> None:
        """Fail while loading config when a required directory is unavailable."""
        if not path.is_dir():
            raise ValueError(
                f"Environment variable {environment_name} must name an existing "
                f"directory: {path}"
            )

    @staticmethod
    def _require_file(path: Path | None, environment_name: str) -> None:
        """Fail while loading config when an optional file is configured badly."""
        if path is not None and not path.is_file():
            raise ValueError(
                f"Environment variable {environment_name} must name an existing "
                f"file: {path}"
            )
