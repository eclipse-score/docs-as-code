# *******************************************************************************
# Copyright (c) 2024 Contributors to the Eclipse Foundation
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

"""Run local documentation builds and live preview from Bazel's docs targets."""

import argparse
import hashlib
import json
import logging
import os
import shutil
import sys
import time
from collections.abc import Mapping
from pathlib import Path
from typing import cast

import debugpy
from sphinx.cmd.build import main as sphinx_main
from sphinx_autobuild.__main__ import (
    main as sphinx_autobuild_main,  # type: ignore[reportUnknownVariableType] # sphinx_autobuild doesn't provide complete type annotations
)

from src.extensions.score_mounts._resolver import load_mounts_manifest, resolve_walk_dir
from src.helper_lib import get_runfiles_dir

logger = logging.getLogger(__name__)


_MODULE_HASH_FILE = ".module_bazel_hash"


class Environment:
    """Typed access to the process environment used by the CLI config loader."""

    def __init__(self, values: Mapping[str, str] | None = None) -> None:
        self._values = os.environ if values is None else values

    def get(self, name: str, default: str | None = None) -> str:
        """Read a value, raising when it is missing and no default is supplied."""
        value = self._values.get(name)
        logger.debug("Env: %s = %s", name, value)
        if value is not None:
            # Preserve an explicitly configured value, including an empty string.
            return value
        elif default is not None:
            # A caller-provided default makes this environment variable optional.
            return default
        else:
            # A missing value without a default is required configuration.
            raise ValueError(f"Environment variable {name} is not set")

    def optional_path(self, name: str) -> Path | None:
        """Read an optional path from the environment."""
        value = self.get(name, "")
        return Path(value) if value else None

    def required_path(self, name: str) -> Path:
        """Read a required path from the environment."""
        value = self.get(name, "")
        if not value:
            raise ValueError(f"Environment variable {name} is not set")
        return Path(value)

    def json(self, name: str, default: str | None = None) -> object:
        """Read and decode a JSON value from the environment."""
        return json.loads(self.get(name, default))

    def string_list(self, name: str, default: str | None = None) -> list[str]:
        """Read a JSON list and validate that every item is a string."""
        raw_value = self.get(name, default)
        # DATA was historically allowed to be present but empty. Treat that as
        # an empty list while still requiring the environment variable itself.
        if not raw_value:
            return []
        value = json.loads(raw_value)
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in cast(list[object], value)
        ):
            raise ValueError(
                f"Environment variable {name} must contain a list of strings"
            )
        return cast(list[str], value)


def _merged_external_needs(env: Environment) -> list[str]:
    """Combine DATA and EXTERNAL_NEEDS_FILES into one label list.

    Both env vars hold JSON lists of Bazel labels; the extension parses the
    resulting `external_needs_source` define uniformly.
    """
    return env.string_list("DATA") + env.string_list(
        "EXTERNAL_NEEDS_FILES", default="[]"
    )


class DocsCliConfig:
    """Configuration consumed by the documentation launcher.

    Keeping environment parsing in one place lets the launcher operate on a
    stable configuration object. Paths stored on this object are resolved to
    the filesystem visible to the current process. The logical package and
    source paths remain available for repository metadata such as GitHub edit
    links.
    """

    action: str
    ws_root: Path | None
    package_directory: Path
    package_dir: Path
    source_directory_relative: Path
    source_directory: Path
    output_directory: Path
    build_dir: Path
    external_needs_sources: list[str]
    testcase_source_dirs: list[str]
    mounts_manifest: Path | None
    sphinx_config_file: Path | None
    metamodel_yaml: Path | None
    score_sourcelinks_json: Path | None
    known_good_json: Path | None
    sphinx_extra_opts: list[str]
    github_repository: str | None

    @property
    def is_bazel_build(self) -> bool:
        """Whether this configuration belongs to the sandboxed Needs action."""
        return self.action == "build_needs_json"

    @property
    def is_bazel_run(self) -> bool:
        """Whether this configuration belongs to a ``bazel run`` target."""
        return self.ws_root is not None and not self.is_bazel_build

    @property
    def is_direct(self) -> bool:
        """Whether the launcher was started outside Bazel."""
        return not self.is_bazel_build and not self.is_bazel_run

    @classmethod
    def from_environment(cls, env: Environment | None = None) -> "DocsCliConfig":
        """Load configuration from the process environment or a test mapping."""
        return cls(env if env is not None else Environment())

    def __init__(self, env: Environment):
        """
        Load launcher configuration from the current Bazel environment.

        Specifically, this method handles bazel build and run differences.
        """
        self.action = env.get("ACTION")
        self.ws_root = env.optional_path("BUILD_WORKSPACE_DIRECTORY")
        if self.ws_root is not None:
            self._require_directory(self.ws_root, "BUILD_WORKSPACE_DIRECTORY")
        # An empty PACKAGE_DIR intentionally denotes the workspace root.
        self.package_directory = Path(env.get("PACKAGE_DIR", ""))
        self.source_directory_relative = Path(env.get("SOURCE_DIRECTORY"))

        if self.is_bazel_build:
            # Build actions run from the execution root and do not expose the
            # caller's workspace directory. Their source and output paths must
            # therefore be resolved from the action's current working directory.
            self.package_dir = Path.cwd()
            self.source_directory = (
                self.package_dir / self.source_directory_relative
            ).absolute()
            self.output_directory = env.required_path("OUTPUT_DIRECTORY").absolute()
        else:
            workspace_root = self.ws_root or Path.cwd()
            self.package_dir = workspace_root / self.package_directory
            self.source_directory = self.package_dir / self.source_directory_relative
            self.output_directory = self.package_dir / "_build"
        self.build_dir = self.output_directory
        self._require_directory(self.source_directory, "SOURCE_DIRECTORY")

        self.external_needs_sources = _merged_external_needs(env)
        self.testcase_source_dirs = env.string_list("TEST_SOURCES", "[]")
        self.mounts_manifest = self._resolve_input_path(
            env.optional_path("MOUNTS_MANIFEST")
        )
        self._require_file(self.mounts_manifest, "MOUNTS_MANIFEST")
        self.sphinx_config_file = self._resolve_input_path(
            env.optional_path("SPHINX_CONFIG_FILE")
        )
        self._require_file(self.sphinx_config_file, "SPHINX_CONFIG_FILE")
        self.metamodel_yaml = self._resolve_input_path(
            env.optional_path("SCORE_METAMODEL_YAML")
        )
        self._require_file(self.metamodel_yaml, "SCORE_METAMODEL_YAML")
        self.score_sourcelinks_json = self._resolve_execution_path(
            env.optional_path("SCORE_SOURCELINKS")
        )
        self._require_file(self.score_sourcelinks_json, "SCORE_SOURCELINKS")
        self.known_good_json = self._resolve_execution_path(
            env.optional_path("KNOWN_GOOD_JSON")
        )
        self._require_file(self.known_good_json, "KNOWN_GOOD_JSON")
        self.sphinx_extra_opts = (
            env.string_list("SPHINX_EXTRA_OPTS", "[]") if self.is_bazel_build else []
        )
        self.github_repository = env.get("GITHUB_REPOSITORY", "") or None

    def _resolve_input_path(self, path: Path | None) -> Path | None:
        """Resolve an optional config input in its current execution context."""
        if path is None or path.is_absolute():
            return path
        elif self.is_bazel_build:
            return (Path.cwd() / path).absolute()
        elif self.is_bazel_run:
            # Interactive Bazel targets receive runfiles-relative paths from
            # ``rlocationpath``. The runfiles tree is the only stable location
            # for generated files and external repository inputs.
            return get_runfiles_dir() / path
        else:
            # Direct invocations resolve relative inputs from the workspace or
            # current working directory.
            return ((self.ws_root or Path.cwd()) / path).absolute()

    def _resolve_execution_path(self, path: Path | None) -> Path | None:
        """Resolve a path consumed directly from the process working directory."""
        if path is None or path.is_absolute():
            return path
        elif self.is_bazel_run:
            # ``KNOWN_GOOD_JSON`` comes from Bazel's ``$(location)`` expansion,
            # not ``$(rlocationpath)``. Bazel-run processes use the workspace as
            # their working directory, so preserve that consumer-facing path.
            return ((self.ws_root or Path.cwd()) / path).absolute()
        else:
            return (Path.cwd() / path).absolute()

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


def _compute_hash(files: list[Path]) -> str:
    h = hashlib.sha256()
    for f in sorted(files, key=str):
        h.update(f.read_bytes())
    return h.hexdigest()


def _build_has_warnings(build_dir: Path) -> bool:
    """Return whether the previous build recorded any warnings."""
    warnings_txt = build_dir / "warnings.txt"
    return warnings_txt.exists() and warnings_txt.stat().st_size > 0


def _module_hash_changed(build_dir: Path, sentinel_files: list[Path]) -> bool:
    """Return whether the build's recorded module-input hash is stale."""
    hash_file = build_dir / _MODULE_HASH_FILE
    return not hash_file.exists() or hash_file.read_text().strip() != _compute_hash(
        sentinel_files
    )


def clean_builddir_if_stale(build_dir: Path, sentinel_files: list[Path]) -> None:
    """Delete build_dir if the previous build had warnings or any sentinel file changed."""
    if not build_dir.exists():
        return

    if _build_has_warnings(build_dir) or _module_hash_changed(
        build_dir, sentinel_files
    ):
        print(
            "Previous build had warnings or the hash changed. Removing _build to ensure a clean build."
        )
        shutil.rmtree(build_dir)


def update_module_hash(build_dir: Path, sentinel_files: list[Path]) -> None:
    (build_dir / _MODULE_HASH_FILE).write_text(_compute_hash(sentinel_files))


def mounted_watch_dirs(
    manifest_path: Path, ws_root: Path | None, runfiles_dir: Path | None = None
) -> list[str]:
    """Return the directories provided by docs bundles for ``sphinx-autobuild``.

    This deliberately uses the same manifest and path-resolution rules as the
    ``score_mounts`` extension.  The extension consumes the paths during a
    Sphinx build; autobuild needs them separately to notice edits that happen
    outside the primary Sphinx source directory.
    """
    manifest = load_mounts_manifest(manifest_path)
    watch_dirs: list[str] = []
    seen: set[str] = set()

    def add_watch_dir(path: Path) -> None:
        path_string = str(path)
        if path_string not in seen:
            seen.add(path_string)
            watch_dirs.append(path_string)

    for spec in manifest.mounts:
        # A data-only bundle has no source directory. Passing its empty
        # ``src_root`` to resolve_walk_dir would watch the workspace root,
        # which makes sphinx-autobuild observe unrelated files (including its
        # own output). Watch the generated data directories instead.
        if spec.src_root:
            add_watch_dir(resolve_walk_dir(manifest, spec, ws_root, runfiles_dir))

        for data_file in spec.data:
            if ws_root is not None and runfiles_dir is not None:
                runfiles_str = str(runfiles_dir)
                if "/bazel-out/" in runfiles_str:
                    # The runfiles path points into the execroot's output
                    # tree. Use the execroot prefix just like score_mounts.
                    walk_file = Path(runfiles_str.split("/bazel-out/")[0]) / data_file
                else:
                    walk_file = (
                        ws_root
                        / "bazel-bin"
                        / data_file.removeprefix("bazel-out/k8-fastbuild/bin/")
                    )
            else:
                walk_file = Path.cwd() / data_file
            add_watch_dir(walk_file.parent)

    return watch_dirs


def sphinx_arguments(config: DocsCliConfig) -> list[str]:
    """Resolve package sources and Bazel-provided configuration for every builder."""
    base_arguments = [
        str(config.source_directory),
        str(config.output_directory),
        "-W",  # treat warning as errors
        "--keep-going",  # do not abort after one error
        "-T",  # show details in case of errors in extensions
        "--jobs",
        "auto",
        # Merge DATA (:needs_json / :docs_sources) with EXTERNAL_NEEDS_FILES
        # (:needs_json_file) into one define consumed by the Sphinx extensions.
        f"--define=external_needs_source={json.dumps(config.external_needs_sources)}",
        f"--define=testcase_source_dirs={json.dumps(config.testcase_source_dirs)}",
        # Path to the Bazel-emitted mounts manifest (empty when no mounts are
        # configured); consumed by the score_mounts extension.
        f"--define=mounts_manifest={config.mounts_manifest or ''}",
    ]

    if config.is_bazel_build:
        # The Bazel action declares ``build_dir`` as its output tree, and that
        # tree must contain only the Needs inventory consumed by downstream
        # actions. Keep Sphinx's internal doctree cache beside it instead of
        # mixing action state into the declared output.
        base_arguments.extend(["-d", str(config.build_dir) + "_doctrees"])

        # The sandboxed Needs rule transports options as JSON so spaces, quotes and
        # equals signs survive the environment boundary. Append them last so an
        # action-specific value can override one of the shared defaults above.
        base_arguments.extend(config.sphinx_extra_opts)
    else:
        # Interactive builds keep warnings in the workspace so developers can
        # inspect them after a failed build. A Bazel action reports failure
        # through its exit code and must leave its declared output tree free of
        # this diagnostic side file.
        base_arguments.extend(
            ["--warning-file", str(config.build_dir / "warnings.txt")]
        )

    if config.sphinx_config_file:
        # ``DocsCliConfig`` has already resolved the action path from the
        # execution root or the interactive runfiles tree. Sphinx needs the
        # containing directory rather than the ``conf.py`` path itself.
        base_arguments.extend(["-c", str(config.sphinx_config_file.parent)])

    metamodel_yaml = config.metamodel_yaml
    if metamodel_yaml:
        # ``DocsCliConfig`` resolves runfiles-relative paths for interactive
        # targets and execution-root paths for the sandboxed action. The
        # sandbox must not perform a second runfiles lookup because that would
        # escape the action's declared inputs.
        base_arguments.append(f"--define=score_metamodel_yaml={metamodel_yaml}")

    if config.score_sourcelinks_json:
        base_arguments.append(
            f"--define=score_sourcelinks_json={config.score_sourcelinks_json}"
        )

    if config.github_repository:
        # GITHUB_REPOSITORY is expected as "owner/repo"; partition("/") splits
        # once into (owner, separator, repo), so we can ignore the separator.
        github_user, _, github_repo = config.github_repository.partition("/")

        base_arguments.append(f"-A=github_user={github_user}")
        base_arguments.append(f"-A=github_repo={github_repo}")
        base_arguments.append("-A=github_version=main")
        # doc_path must be repo-relative so the edit URL does not contain the
        # absolute runner filesystem path (e.g. /home/runner/work/…/docs).
        relative_doc_path = config.package_directory / config.source_directory_relative
        base_arguments.append(f"-A=doc_path={relative_doc_path}")

    if config.known_good_json:
        base_arguments.append(f"--define=KNOWN_GOOD_JSON={config.known_good_json}")

    return base_arguments


def watch_arguments(config: DocsCliConfig) -> list[str]:
    """Build autobuild options using the same runfiles resolution as Sphinx."""
    mounts_manifest = config.mounts_manifest
    watch_arguments: list[str] = []
    if mounts_manifest:
        # ``DocsCliConfig`` has already resolved the manifest to the filesystem
        # path consumed by score_mounts. Keep the runfiles root separately for
        # resolving mounted data directories.
        ws_root = config.ws_root
        runfiles_dir = get_runfiles_dir() if config.is_bazel_run else None
        for watch_dir in mounted_watch_dirs(
            mounts_manifest,
            ws_root,
            runfiles_dir,
        ):
            watch_arguments.extend(["--watch", watch_dir])
    return watch_arguments


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-dp", "--debug_port", help="port to listen to debugging client", default=5678
    )
    parser.add_argument(
        "--debug", help="Enable Debugging via debugpy", action="store_true"
    )
    parser.add_argument("--github_user", help=argparse.SUPPRESS)
    parser.add_argument("--github_repo", help=argparse.SUPPRESS)
    parser.add_argument(
        "--port",
        type=int,
        help="Port to use for the live_preview ACTION. Default is 8000. "
        "Use 0 for auto detection of a free port.",
        default=8000,
    )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    """Run the requested builder and record whether its output can be reused."""
    args = parse_args(argv)
    if args.debug:
        debugpy.listen(("0.0.0.0", args.debug_port))
        logger.info("Waiting for client to connect on port: " + str(args.debug_port))
        debugpy.wait_for_client()

    config = DocsCliConfig.from_environment()
    action = config.action
    is_bazel_build = config.is_bazel_build

    # Interactive Bazel targets reuse the package cache. A direct invocation
    # uses the current directory as its workspace fallback. Build actions do
    # not inspect sentinels because their declared output is always isolated.
    workspace_root = config.ws_root or Path.cwd()
    sentinel_files = [
        workspace_root / "MODULE.bazel",
        workspace_root / "MODULE.bazel.lock",
        config.package_dir / "BUILD",
    ]
    if not is_bazel_build:
        clean_builddir_if_stale(config.build_dir, sentinel_files)

    warning_file = config.build_dir / "warnings.txt"
    base_arguments = sphinx_arguments(config)

    if action == "live_preview":
        sphinx_autobuild_main(
            base_arguments
            + [
                # Note: bools need to be passed via '0' and '1' from the command line.
                "--define=skip_rescanning_via_source_code_linker=1",
                f"--port={args.port}",
            ]
            + watch_arguments(config)
        )
        return 0

    if action == "incremental":
        builder = "html"
    elif action in ("check", "build_needs_json"):
        builder = "needs"
    elif action == "linkcheck":
        builder = "linkcheck"
    else:
        raise ValueError(f"Unknown action: {action}")

    base_arguments.extend(["-b", builder])

    start_time = time.perf_counter()
    exit_code = sphinx_main(base_arguments)
    end_time = time.perf_counter()
    print(f"docs ({action}) finished in {end_time - start_time:.1f} seconds")

    if is_bazel_build:
        # The declared output is owned by the action. Do not record an
        # interactive cache hash or write a warning marker into the workspace.
        return exit_code

    if exit_code == 0:
        update_module_hash(config.build_dir, sentinel_files)
    else:
        with warning_file.open("a", encoding="utf-8") as f:
            f.write("-" * 80 + "\n")
            f.write(f"Build failed with exit code {exit_code}\n")

    return exit_code


if __name__ == "__main__":
    # Extensions need stable runfiles paths even when Sphinx changes directory.
    for variable in ("RUNFILES_DIR", "JAVA_RUNFILES"):
        if os.environ.get(variable):
            os.environ[variable] = str(Path(os.environ[variable]).absolute())

    sys.exit(main())
