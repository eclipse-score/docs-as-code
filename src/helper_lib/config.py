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
import os
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
    the filesystem visible to the current process. Paths inside the Sphinx
    source tree belong to Sphinx itself; this config handles launcher paths,
    including inputs located through Bazel runfiles.
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

    @property
    def uses_ide_support_runfiles(self) -> bool:
        """Whether direct invocation found the dedicated IDE runfiles tree."""
        return (
            self.is_direct
            and self._runfiles_dir is not None
            and self._runfiles_dir.name == "ide_support.runfiles"
        )

    def __init__(self, env: Environment | None = None):
        """
        Load launcher configuration from the current Bazel environment.

        Specifically, this method handles bazel build and run differences.
        """

        self._env = env if env is not None else Environment()

        # These three must be queried first:
        self.ws_root = self._env.optional_path("BUILD_WORKSPACE_DIRECTORY")
        self._runfiles = Runfiles.Create()
        self.environment = self._identify_environment()

        # Sanity checks
        if self.ws_root:
            self._require_directory(self.ws_root, "BUILD_WORKSPACE_DIRECTORY")

        logger.debug(
            "Resolved documentation environment: environment=%s, cwd=%s, "
            "workspace_root=%s, action=%s",
            self.environment.value,
            Path.cwd(),
            self.ws_root,
            self.action,
        )

    @cached_property
    def action(self) -> str | None:
        # Environment.get uses an empty string as its optional default; expose
        # a missing or empty action as None to distinguish it from real actions.
        return self._env.get("ACTION", "") or None

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
    def _runfiles_dir(self) -> Path | None:
        """Return the runfiles tree when one is available to this process."""
        if self._runfiles:
            # RUNFILES_DIR is optional when Bazel uses a manifest-only layout;
            # resolve_input_path can still use the runfiles library in that case.
            runfiles_dir = Environment(self._runfiles.EnvVars()).optional_path(
                "RUNFILES_DIR"
            )
            if runfiles_dir is not None:
                return runfiles_dir

        if self.is_direct:
            # IDE builds run outside Bazel but still consume the runfiles tree
            # produced by the dedicated ide_support target.
            if self.git_root is not None:
                ide_runfiles_dir = self.git_root / "bazel-bin" / "ide_support.runfiles"
                if ide_runfiles_dir.is_dir():
                    return ide_runfiles_dir
            else:
                return None
        else:
            # A sandboxed process can resolve runfiles through its manifest
            # even when no directory-form runfiles root is exposed.
            return None

        return None

    def _resolve_runfiles_path(self, path: Path | str) -> Path | None:
        """Resolve a runfiles-relative input through Bazel or the IDE runfiles tree.

        ``Rlocation`` supports manifest-only runfiles layouts. Direct IDE
        invocations do not have a runfiles library instance, so they use the
        runfiles directory discovered from the local ``ide_support`` target.
        """
        path = Path(path)
        if path.is_absolute():
            return path

        # Bazel's external repository paths can be expressed as
        # ``_main/../<canonical-repo>/...``. Normalize that intentional parent
        # traversal before asking the runfiles library to resolve the key.
        normalized_path = Path(os.path.normpath(path.as_posix()))
        if normalized_path.parts and normalized_path.parts[0] == "..":
            return None

        if self._runfiles:
            location = self._runfiles.Rlocation(normalized_path.as_posix())
            if location:
                return Path(location).absolute()

        if self._runfiles_dir is not None:
            return Path(os.path.abspath(self._runfiles_dir / normalized_path))
        return None

    def relative_to_runfiles(self, path: Path) -> Path | None:
        """Return a path's runfiles-relative spelling when it lies in runfiles."""
        if self._runfiles_dir is None:
            return None
        try:
            return path.resolve().relative_to(self._runfiles_dir.resolve())
        except ValueError:
            return None

    def resolve_bazel_output_path(self, path: Path | str) -> Path:
        """Resolve an execroot-relative Bazel output in the current context.

        ``bazel run`` exposes generated outputs below ``bazel-bin``. Some
        runfiles layouts instead point into the execroot's ``bazel-out`` tree,
        in which case the execroot prefix is recovered from that runfiles path.
        Sandboxed builds already run from the execroot.
        """
        path = Path(path)
        if path.is_absolute():
            return path

        runfiles_dir = self._runfiles_dir
        if self.is_bazel_run and runfiles_dir is not None:
            runfiles_spelling = runfiles_dir.as_posix()
            if "/bazel-out/" in runfiles_spelling:
                execroot = Path(runfiles_spelling.split("/bazel-out/", 1)[0])
                return execroot / path

        if self.is_bazel_run and self.ws_root is not None:
            parts = path.parts
            if len(parts) >= 3 and parts[0] == "bazel-out" and parts[2] == "bin":
                return self.ws_root / "bazel-bin" / Path(*parts[3:])

        return Path.cwd() / path

    def resolve_input_path(
        self, path: Path, *, runfiles_relative: bool = False
    ) -> Path | None:
        """Resolve an input path for the current mode or explicitly from runfiles.

        ``runfiles_relative`` is for callers that already know the value is a
        runfiles address, including direct IDE invocations using ide_support.
        Otherwise the path origin follows the active launcher mode.
        """
        if path.is_absolute():
            return path

        if runfiles_relative or self.is_bazel_run:
            # docs.bzl passes rlocationpath values to interactive Bazel targets;
            # this also handles manifest-only layouts and direct IDE callers.
            return self._resolve_runfiles_path(path)
        elif self.is_bazel_build:
            # Build actions pass declared input paths relative to their
            # execution root, not runfiles-relative paths.
            return path.absolute()
        else:
            # Direct invocations resolve relative inputs from the workspace
            # when present, or otherwise from the caller's current directory.
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
