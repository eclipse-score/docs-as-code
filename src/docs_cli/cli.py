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
from pathlib import Path

import debugpy
from sphinx.cmd.build import main as sphinx_main
from sphinx_autobuild.__main__ import (
    main as sphinx_autobuild_main,  # type: ignore[reportUnknownVariableType] # sphinx_autobuild doesn't provide complete type annotations
)

from src.extensions.score_mounts._resolver import load_mounts_manifest, resolve_walk_dir
from src.helper_lib import Environment, get_runfiles_dir
from src.helper_lib.config import DocsCliConfig

logger = logging.getLogger(__name__)


_MODULE_HASH_FILE = ".module_bazel_hash"
env = Environment()


def _merged_external_needs() -> str:
    """Combine DATA and EXTERNAL_NEEDS_FILES into one JSON label list.

    Both env vars hold JSON lists of Bazel labels; the extension parses the
    resulting `external_needs_source` define uniformly.
    """
    data = env.string_list("DATA")
    external = env.string_list("EXTERNAL_NEEDS_FILES", "[]")
    return json.dumps(data + external)


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


def sphinx_arguments(
    ws_root: Path,
    package_dir: Path,
    build_dir: Path,
    config: DocsCliConfig,
) -> list[str]:
    """Resolve package sources and Bazel-provided configuration for every builder."""
    source_directory = env.required_path("SOURCE_DIRECTORY")
    base_arguments = [
        str(package_dir / source_directory),
        str(build_dir),
        "-W",  # treat warning as errors
        "--keep-going",  # do not abort after one error
        "-T",  # show details in case of errors in extensions
        "--jobs",
        "auto",
        # Merge DATA (:needs_json / :docs_sources) with EXTERNAL_NEEDS_FILES
        # (:needs_json_file) into one define consumed by the Sphinx extensions.
        f"--define=external_needs_source={_merged_external_needs()}",
        f"--define=testcase_source_dirs={env.get('TEST_SOURCES', '[]')}",
        # Path to the Bazel-emitted mounts manifest (empty when no mounts are
        # configured); consumed by the score_mounts extension.
        f"--define=mounts_manifest={env.optional_path('MOUNTS_MANIFEST') or ''}",
    ]

    if config.is_bazel_build:
        # The Bazel action declares ``build_dir`` as its output tree, and that
        # tree must contain only the Needs inventory consumed by downstream
        # actions. Keep Sphinx's internal doctree cache beside it instead of
        # mixing action state into the declared output.
        base_arguments.extend(["-d", str(build_dir) + "_doctrees"])

        # The sandboxed Needs rule transports options as JSON so spaces, quotes and
        # equals signs survive the environment boundary. Append them last so an
        # action-specific value can override one of the shared defaults above.
        base_arguments.extend(env.string_list("SPHINX_EXTRA_OPTS", "[]"))
    else:
        # Interactive builds keep warnings in the workspace so developers can
        # inspect them after a failed build. A Bazel action reports failure
        # through its exit code and must leave its declared output tree free of
        # this diagnostic side file.
        base_arguments.extend(["--warning-file", str(build_dir / "warnings.txt")])

    if config_file := env.optional_path("SPHINX_CONFIG_FILE"):
        # The action receives ctx.file.config.path, which is interpreted from
        # the action's execution-root working directory. Resolve it locally
        # instead of using runfiles lookup; interactive targets receive a
        # runfiles-relative path and need that lookup before Sphinx gets the
        # containing directory.
        if config.is_bazel_build:
            config_file = config_file.absolute()
        elif not config_file.is_absolute():
            config_file = get_runfiles_dir() / config_file
        base_arguments.extend(["-c", str(config_file.parent)])

    if metamodel_yaml := env.optional_path("SCORE_METAMODEL_YAML"):
        # Under ``bazel run``, this environment variable is runfiles-relative
        # and must be resolved through RUNFILES_DIR. A sandboxed Needs action
        # instead expands the metamodel label to an execution-root path in
        # SPHINX_EXTRA_OPTS; applying runfiles lookup there would escape the
        # action's declared inputs.
        if not config.is_bazel_build and not metamodel_yaml.is_absolute():
            runfiles_dir = env.optional_path("RUNFILES_DIR")
            metamodel_yaml = (
                runfiles_dir / metamodel_yaml
                if runfiles_dir is not None
                else ws_root / metamodel_yaml
            )
        metamodel_yaml = metamodel_yaml.absolute()
        base_arguments.append(f"--define=score_metamodel_yaml={metamodel_yaml}")

    if github_repository := env.get("GITHUB_REPOSITORY", ""):
        # GITHUB_REPOSITORY is expected as "owner/repo"; partition("/") splits
        # once into (owner, separator, repo), so we can ignore the separator.
        github_user, _, github_repo = github_repository.partition("/")

        base_arguments.append(f"-A=github_user={github_user}")
        base_arguments.append(f"-A=github_repo={github_repo}")
        base_arguments.append("-A=github_version=main")
        # doc_path must be repo-relative so the edit URL does not contain the
        # absolute runner filesystem path (e.g. /home/runner/work/…/docs).
        relative_doc_path = (
            env.optional_path("PACKAGE_DIR") or Path()
        ) / source_directory
        base_arguments.append(f"-A=doc_path={relative_doc_path}")

    if known_good_json := env.optional_path("KNOWN_GOOD_JSON"):
        base_arguments.append(f"--define=KNOWN_GOOD_JSON={known_good_json}")

    return base_arguments


def watch_arguments(config: DocsCliConfig) -> list[str]:
    """Build autobuild options using the same runfiles resolution as Sphinx."""
    mounts_manifest = env.optional_path("MOUNTS_MANIFEST")
    watch_arguments: list[str] = []
    if mounts_manifest:
        # ``MOUNTS_MANIFEST`` is runfiles-relative under ``bazel run`` and
        # an ordinary path for direct invocations, matching score_mounts.
        manifest_path = (
            get_runfiles_dir() / mounts_manifest
            if config.is_bazel_run
            else mounts_manifest
        )
        for watch_dir in mounted_watch_dirs(
            manifest_path,
            config.ws_root,
            get_runfiles_dir() if config.is_bazel_run else None,
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

    config = DocsCliConfig.from_environment(env)
    ws_root = config.ws_root or Path()
    # Docs source and output are resolved relative to the package where docs()
    # was called; an empty PACKAGE_DIR denotes the workspace root.
    package_dir = ws_root / (env.optional_path("PACKAGE_DIR") or Path())
    build_dir = package_dir / "_build"
    if config.is_bazel_build:
        # Bazel owns the action's paths; never use the caller's workspace cache.
        package_dir = Path.cwd()
        build_dir = env.required_path("OUTPUT_DIRECTORY").absolute()

    sentinel_files = [
        ws_root / "MODULE.bazel",
        ws_root / "MODULE.bazel.lock",
        package_dir / "BUILD",
    ]
    if not config.is_bazel_build:
        clean_builddir_if_stale(build_dir, sentinel_files)

    warning_file = build_dir / "warnings.txt"
    base_arguments = sphinx_arguments(ws_root, package_dir, build_dir, config)

    if config.action == "live_preview":
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

    if config.action == "incremental":
        builder = "html"
    elif config.action in ("check", "build_needs_json"):
        builder = "needs"
    elif config.action == "linkcheck":
        builder = "linkcheck"
    else:
        raise ValueError(f"Unknown action: {config.action}")

    base_arguments.extend(["-b", builder])

    start_time = time.perf_counter()
    exit_code = sphinx_main(base_arguments)
    end_time = time.perf_counter()
    print(f"docs ({config.action}) finished in {end_time - start_time:.1f} seconds")

    if config.is_bazel_build:
        # The declared output is owned by the action. Do not record an
        # interactive cache hash or write a warning marker into the workspace.
        return exit_code

    if exit_code == 0:
        update_module_hash(build_dir, sentinel_files)
    else:
        with warning_file.open("a", encoding="utf-8") as f:
            f.write("-" * 80 + "\n")
            f.write(f"Build failed with exit code {exit_code}\n")

    return exit_code


if __name__ == "__main__":
    # Extensions need stable runfiles paths even when Sphinx changes directory.
    for variable in ("RUNFILES_DIR", "JAVA_RUNFILES"):
        value = env.optional_path(variable)
        if value:
            os.environ[variable] = str(value.absolute())

    sys.exit(main())
