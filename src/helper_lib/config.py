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

import logging
from enum import Enum
from functools import cached_property
from pathlib import Path

from python.runfiles import Runfiles

from src.helper_lib import Environment, find_git_root

logger = logging.getLogger(__name__)


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

        self._env = env

        # These three must be queried first:
        self.ws_root = env.optional_path("BUILD_WORKSPACE_DIRECTORY")
        self._runfiles = Runfiles.Create()
        self.environment = self._identify_environment()

        # Sanity checks
        if self.ws_root:
            self._require_directory(self.ws_root, "BUILD_WORKSPACE_DIRECTORY")

        self.action = env.get("ACTION")

        logger.debug(
            "Resolved documentation paths: environment=%s, cwd=%s, "
            "package_dir=%s, source_directory=%s, output_dir=%s",
            self.environment.value,
            Path.cwd(),
            self.package_dir,
            self.source_dir_relative_to_ws,
            self.output_dir,
        )

    @cached_property
    def git_root(self) -> Path | None:
        """Return the Git root when it is visible from the current process."""
        if self.is_bazel_build:
            # A sandboxed build does not have the repository checkout available.
            # Searching upwards could accidentally escape the sandbox and find
            # an unrelated Git repository, so build actions do not auto-detect
            # a Git root.
            return None
        else:
            # Direct invocations and bazel run execute with the user's
            # workspace checkout visible, so Git metadata can be discovered
            # from the current working directory.
            assert self.is_direct or self.is_bazel_run
            return find_git_root()

    @cached_property
    def package_dir(self) -> Path:
        """Return the package directory in the current execution context."""
        if self.is_bazel_run:
            # bazel run starts in the workspace root rather than in the target
            # package. docs.bzl supplies PACKAGE_DIR as native.package_name()
            # so relative source and output paths can be located in that
            # package. An empty package name at the workspace root becomes
            # Path("") = Path(".").
            assert self.ws_root
            return self.ws_root / Path(self._env.get("PACKAGE_DIR"))
        else:
            # Build actions run from the execution root and direct invocations
            # run from their current working directory. In both cases the
            # supplied paths are already relative to the directory they need,
            # so no package prefix is required.
            return Path()

    @cached_property
    def output_dir(self) -> Path:
        """Return the directory in which the current action writes output."""
        if self.is_bazel_build:
            # A sandboxed build must write into the output tree declared by its
            # Bazel action; OUTPUT_DIRECTORY identifies that tree in the
            # action's execution environment.
            return self._env.required_path("OUTPUT_DIRECTORY")
        else:
            # bazel run and direct invocations are interactive and do not have
            # a declared action output tree. They keep their reusable build
            # cache below the resolved package directory instead.
            return self.package_dir / "_build"

    @cached_property
    def source_dir(self) -> Path:
        """Return the source directory in the current execution context."""
        # SOURCE_DIRECTORY is relative in every mode. package_dir is empty for
        # build and direct modes because those paths are already relative to
        # their execution directory; bazel run adds its workspace package
        # prefix here.
        source_dir_relative = self._env.required_path("SOURCE_DIRECTORY")
        assert not source_dir_relative.is_absolute()
        return self.package_dir / source_dir_relative

    @cached_property
    def source_dir_relative_to_ws(self) -> Path:
        """Return the source directory relative to the workspace when running."""
        if self.is_bazel_run:
            # bazel run has an absolute workspace root, so remove that prefix
            # to produce the workspace-relative path used by GitHub edit links.
            assert self.ws_root
            return self.source_dir.relative_to(self.ws_root)
        else:
            # Build actions intentionally have no workspace root in their
            # sandbox, and direct invocations use cwd as their path base. Their
            # source path is therefore already in the most useful relative
            # form available here.
            assert not self.ws_root
            return self.source_dir

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
