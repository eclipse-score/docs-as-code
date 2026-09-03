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
from src.helper_lib import find_ws_root, get_runfiles_dir

logger = logging.getLogger(__name__)

_MODULE_HASH_FILE = ".module_bazel_hash"


def get_env(name: str) -> str:
    val = os.environ.get(name, None)
    logger.debug(f"DEBUG: Env: {name} = {val}")
    if val is None:
        raise ValueError(f"Environment variable {name} is not set")
    return val


def _merged_external_needs() -> str:
    """Combine DATA and EXTERNAL_NEEDS_FILES into one JSON label list.

    Both env vars hold JSON lists of Bazel labels; the extension parses the
    resulting `external_needs_source` define uniformly.
    """
    data = json.loads(get_env("DATA") or "[]")
    external = json.loads(os.environ.get("EXTERNAL_NEEDS_FILES", "[]") or "[]")
    return json.dumps(data + external)


def _compute_hash(files: list[Path]) -> str:
    h = hashlib.sha256()
    for f in sorted(files, key=str):
        h.update(f.read_bytes())
    return h.hexdigest()


def clean_builddir_if_stale(build_dir: Path, sentinel_files: list[Path]) -> None:
    """Delete build_dir if the previous build had warnings or any sentinel file changed."""
    if not build_dir.exists():
        return

    warnings_txt = build_dir / "warnings.txt"
    has_warnings = warnings_txt.exists() and warnings_txt.stat().st_size > 0

    hash_file = build_dir / _MODULE_HASH_FILE
    hash_changed = (
        not hash_file.exists()
        or hash_file.read_text().strip() != _compute_hash(sentinel_files)
    )

    if has_warnings or hash_changed:
        print(
            "Previous build had warnings or the hash changed. Removing _build to ensure a clean build."
        )
        shutil.rmtree(build_dir)


def update_module_hash(build_dir: Path, sentinel_files: list[Path]) -> None:
    (build_dir / _MODULE_HASH_FILE).write_text(_compute_hash(sentinel_files))


def _mounted_watch_dirs(
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Add debuging functionality
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

    args = parser.parse_args()
    if args.debug:
        debugpy.listen(("0.0.0.0", args.debug_port))
        logger.info("Waiting for client to connect on port: " + str(args.debug_port))
        debugpy.wait_for_client()

    ws_root = Path(os.getenv("BUILD_WORKSPACE_DIRECTORY", ""))
    # Docs source and output are resolved relative to the package where docs()
    # was called. For the root BUILD, PACKAGE_DIR == "" so this is unchanged.
    package_dir = ws_root / os.environ.get("PACKAGE_DIR", "")

    build_dir = package_dir / "_build"
    sentinel_files = [
        ws_root / "MODULE.bazel",
        ws_root / "MODULE.bazel.lock",
        package_dir / "BUILD",
    ]
    clean_builddir_if_stale(build_dir, sentinel_files)

    warning_file = build_dir / "warnings.txt"

    source_directory = get_env("SOURCE_DIRECTORY")
    base_arguments = [
        str(package_dir / source_directory),
        str(build_dir),
        "--warning-file",
        str(warning_file),
        "-W",  # treat warning as errors
        "--keep-going",  # do not abort after one error
        "-T",  # show details in case of errors in extensions
        "--jobs",
        "auto",
        # Merge DATA (:needs_json / :docs_sources) with EXTERNAL_NEEDS_FILES
        # (:needs_json_file) into a single define. The sphinx_docs rule cannot
        # receive per-target env vars, so --define is the only channel that
        # works for both the py_binary and the needs_json target.
        f"--define=external_needs_source={_merged_external_needs()}",
        f"--define=testcase_source_dirs={os.environ.get('TEST_SOURCES', '[]')}",
        f"--define=score_testlink_source={os.environ.get('TESTLINK_SOURCE', 'xml')}",
        # Path to the Bazel-emitted mounts manifest (empty when no mounts are
        # configured); consumed by the score_mounts extension.
        f"--define=mounts_manifest={os.environ.get('MOUNTS_MANIFEST', '')}",
    ]

    generated_config = os.environ.get("SPHINX_CONFIG_FILE", "")
    if generated_config:
        # Under ``bazel run`` this is a runfiles-relative path.  Sphinx wants
        # the directory containing a file literally named ``conf.py``.
        config_file = Path(generated_config)
        if not config_file.is_absolute():
            config_file = get_runfiles_dir() / config_file
        base_arguments.extend(["-c", str(config_file.parent)])

    metamodel_yaml = os.environ.get("SCORE_METAMODEL_YAML", "")
    if metamodel_yaml:
        # ``docs`` passes a runfiles-relative path under ``bazel run``.  Keep
        # the workspace-relative fallback for direct invocations.
        if not os.path.isabs(metamodel_yaml):
            runfiles_dir = os.environ.get("RUNFILES_DIR", "")
            metamodel_yaml = str(
                (Path(runfiles_dir) / metamodel_yaml)
                if runfiles_dir
                else (ws_root / metamodel_yaml)
            )
        metamodel_yaml = os.path.abspath(metamodel_yaml)
        base_arguments.append(f"--define=score_metamodel_yaml={metamodel_yaml}")

    if github_repository := os.getenv("GITHUB_REPOSITORY"):
        # GITHUB_REPOSITORY is expected as "owner/repo"; partition("/") splits
        # once into (owner, separator, repo), so we can ignore the separator.
        github_user, _, github_repo = github_repository.partition("/")

        base_arguments.append(f"-A=github_user={github_user}")
        base_arguments.append(f"-A=github_repo={github_repo}")
        base_arguments.append("-A=github_version=main")
        # doc_path must be repo-relative so the edit URL does not contain the
        # absolute runner filesystem path (e.g. /home/runner/work/…/docs).
        relative_doc_path = Path(os.environ.get("PACKAGE_DIR", "")) / source_directory
        base_arguments.append(f"-A=doc_path={relative_doc_path}")

    if os.getenv("KNOWN_GOOD_JSON"):
        base_arguments.append(f"--define=KNOWN_GOOD_JSON={get_env('KNOWN_GOOD_JSON')}")

    action = get_env("ACTION")
    if action == "live_preview":
        (build_dir / "score_source_code_linker_cache.json").unlink(missing_ok=True)
        mounts_manifest = os.environ.get("MOUNTS_MANIFEST", "")
        watch_arguments: list[str] = []
        if mounts_manifest:
            # ``MOUNTS_MANIFEST`` is runfiles-relative under ``bazel run`` and
            # an ordinary path for direct invocations, matching score_mounts.
            manifest_path = (
                get_runfiles_dir() / mounts_manifest
                if find_ws_root()
                else Path(mounts_manifest)
            )
            ws_root = find_ws_root()
            for watch_dir in _mounted_watch_dirs(
                manifest_path,
                ws_root,
                get_runfiles_dir() if ws_root is not None else None,
            ):
                watch_arguments.extend(["--watch", watch_dir])
        sphinx_autobuild_main(
            base_arguments
            + [
                # Note: bools need to be passed via '0' and '1' from the command line.
                "--define=skip_rescanning_via_source_code_linker=1",
                f"--port={args.port}",
            ]
            + watch_arguments
        )
    else:
        if action == "incremental":
            builder = "html"
        elif action == "check":
            builder = "needs"
        elif action == "linkcheck":
            builder = "linkcheck"
        else:
            raise ValueError(f"Unknown action: {action}")

        base_arguments.extend(
            [
                "-b",
                builder,
            ]
        )

        start_time = time.perf_counter()
        exit_code = sphinx_main(base_arguments)
        end_time = time.perf_counter()
        print(f"docs ({action}) finished in {end_time - start_time:.1f} seconds")

        if exit_code == 0:
            update_module_hash(build_dir, sentinel_files)
        else:
            with warning_file.open("a", encoding="utf-8") as f:
                f.write("-" * 80 + "\n")
                f.write(f"Build failed with exit code {exit_code}\n")

        sys.exit(exit_code)
