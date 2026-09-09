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
from typing import Any, cast

import debugpy
from sphinx.cmd.build import main as sphinx_main
from sphinx_autobuild.__main__ import (
    main as sphinx_autobuild_main,  # type: ignore[reportUnknownVariableType] # sphinx_autobuild doesn't provide complete type annotations
)

from src.extensions.score_mounts._resolver import load_mounts_manifest, resolve_walk_dir
from src.helper_lib import find_ws_root, get_runfiles_dir

logger = logging.getLogger(__name__)


_MODULE_HASH_FILE = ".module_bazel_hash"
_CONFIG_ENVIRONMENT_VARIABLE = "SCORE_DOCS_CONFIG"
_CONFIG_VERSION = 1


def _config_string(config: dict[str, Any], name: str, default: str = "") -> str:
    """Read a string field from the versioned configuration payload."""
    value = config.get(name, default)
    if not isinstance(value, str):
        raise ValueError(
            f"{_CONFIG_ENVIRONMENT_VARIABLE} field '{name}' must be a string"
        )
    return value


def _config_string_list(
    config: dict[str, Any], name: str, default: list[str] | None = None
) -> list[str]:
    """Read and validate a list-of-strings field from the payload."""
    value = config.get(name, [] if default is None else default)
    if not isinstance(value, list):
        raise ValueError(
            f"{_CONFIG_ENVIRONMENT_VARIABLE} field '{name}' must be a list of strings"
        )
    items = cast(list[object], value)
    if not all(isinstance(item, str) for item in items):
        raise ValueError(
            f"{_CONFIG_ENVIRONMENT_VARIABLE} field '{name}' must be a list of strings"
        )
    return cast(list[str], items)


def _config_optional_string(config: dict[str, Any], name: str) -> str | None:
    """Read an optional string field, preserving JSON ``null`` as ``None``."""
    value = config.get(name)
    if value is not None and not isinstance(value, str):
        raise ValueError(
            f"{_CONFIG_ENVIRONMENT_VARIABLE} field '{name}' must be a string or null"
        )
    return cast(str | None, value)


def _config_optional_bool(config: dict[str, Any], name: str) -> bool | None:
    """Read an optional boolean field, preserving JSON ``null`` as ``None``."""
    value = config.get(name)
    if value is not None and not isinstance(value, bool):
        raise ValueError(
            f"{_CONFIG_ENVIRONMENT_VARIABLE} field '{name}' must be a boolean or null"
        )
    return cast(bool | None, value)


def parse_docs_config(raw: str | None = None) -> dict[str, Any]:
    """Parse and validate the single Bazel-to-CLI configuration contract.

    The process environment deliberately remains responsible only for runtime
    context supplied by Bazel or CI (workspace/runfiles locations and GitHub
    metadata). Documentation-target settings all travel in this payload so a
    command cannot accidentally combine values from different configuration
    transports.
    """
    if raw is None:
        raw = os.environ.get(_CONFIG_ENVIRONMENT_VARIABLE)
    if raw is None:
        raise ValueError(
            f"Environment variable {_CONFIG_ENVIRONMENT_VARIABLE} is not set"
        )

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(
            f"{_CONFIG_ENVIRONMENT_VARIABLE} must contain valid JSON: {error.msg}"
        ) from error
    if not isinstance(parsed, dict):
        raise ValueError(
            f"{_CONFIG_ENVIRONMENT_VARIABLE} must contain a JSON object, "
            f"got {type(parsed).__name__}"
        )

    config = cast(dict[str, Any], parsed)
    if "version" not in config:
        raise ValueError(
            f"{_CONFIG_ENVIRONMENT_VARIABLE} is missing required field 'version'"
        )
    if config["version"] != _CONFIG_VERSION:
        raise ValueError(
            f"Unsupported {_CONFIG_ENVIRONMENT_VARIABLE} version "
            f"{config['version']!r}; supported version is {_CONFIG_VERSION}"
        )

    action = config.get("action")
    if not isinstance(action, str) or not action:
        raise ValueError(
            f"{_CONFIG_ENVIRONMENT_VARIABLE} field 'action' must be a non-empty string"
        )
    _config_string(config, "source_directory")
    _config_string(config, "package_directory", "")
    _config_string(config, "output_directory", "_build")
    _config_string(config, "config_file", "")
    _config_string_list(config, "external_needs_sources")
    _config_string_list(config, "testcase_source_dirs")
    _config_optional_string(config, "mounts_manifest")
    _config_optional_string(config, "source_links")
    _config_optional_string(config, "metamodel")
    _config_optional_string(config, "known_good")
    _config_optional_string(config, "master_doc")
    _config_optional_bool(config, "bundle_needs_export")
    _config_optional_bool(config, "plain_links")
    return config


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


def _resolve_context_path(
    raw_path: str,
    *,
    is_bazel_build: bool,
    ws_root: Path | None,
    runfiles_dir: Path | None,
) -> Path:
    """Resolve a payload path in either a runfiles tree or an action sandbox."""
    path = Path(raw_path)
    if path.is_absolute():
        return path
    if is_bazel_build:
        # Bazel action paths are relative to the execution root. The launcher
        # is invoked with that directory as its working directory.
        return Path.cwd() / path
    if runfiles_dir is not None:
        # Interactive binaries receive rlocation-relative paths in the payload.
        return runfiles_dir / path
    if ws_root is not None:
        return ws_root / path
    return Path.cwd() / path


def _sphinx_define(name: str, value: str | None) -> list[str]:
    """Return one Sphinx configuration define when a field is configured."""
    if value is None:
        return []
    return [f"--define={name}={value}"]


def sphinx_arguments(
    config: dict[str, Any],
    ws_root: Path | None,
    package_dir: Path,
    build_dir: Path,
    runfiles_dir: Path | None = None,
) -> list[str]:
    """Generate the complete Sphinx command from one validated payload."""
    action = _config_string(config, "action")
    is_bazel_build = action == "build_needs_json"
    source_directory = _config_string(config, "source_directory")
    external_needs_sources = _config_string_list(config, "external_needs_sources")
    testcase_source_dirs = _config_string_list(config, "testcase_source_dirs")
    base_arguments = [
        str(package_dir / source_directory),
        str(build_dir),
        "-W",  # treat warning as errors
        "--keep-going",  # do not abort after one error
        "-T",  # show details in case of errors in extensions
        "--jobs",
        "auto",
        # These are the only diagnostics shared by all builders. Keeping them
        # here ensures interactive and sandboxed invocations have one source
        # for warning behavior and never receive duplicate options.
    ]

    base_arguments.extend(
        _sphinx_define("external_needs_source", json.dumps(external_needs_sources))
    )
    base_arguments.extend(
        _sphinx_define("testcase_source_dirs", json.dumps(testcase_source_dirs))
    )

    mounts_manifest = _config_optional_string(config, "mounts_manifest")
    if mounts_manifest:
        base_arguments.extend(
            _sphinx_define(
                "mounts_manifest",
                str(
                    _resolve_context_path(
                        mounts_manifest,
                        is_bazel_build=is_bazel_build,
                        ws_root=ws_root,
                        runfiles_dir=runfiles_dir,
                    )
                ),
            )
        )
    else:
        base_arguments.extend(_sphinx_define("mounts_manifest", ""))

    for config_name, payload_name in (
        ("master_doc", "master_doc"),
        ("score_bundle_needs_export", "bundle_needs_export"),
        ("score_source_code_linker_plain_links", "plain_links"),
    ):
        value = config.get(payload_name)
        if value is not None:
            if isinstance(value, bool):
                base_arguments.extend(
                    _sphinx_define(config_name, "1" if value else "0")
                )
            else:
                base_arguments.extend(_sphinx_define(config_name, str(value)))

    for config_name, payload_name in (
        ("score_sourcelinks_json", "source_links"),
        ("score_metamodel_yaml", "metamodel"),
        ("KNOWN_GOOD_JSON", "known_good"),
    ):
        raw_path = _config_optional_string(config, payload_name)
        if raw_path:
            resolved_path = _resolve_context_path(
                raw_path,
                is_bazel_build=is_bazel_build,
                ws_root=ws_root,
                runfiles_dir=runfiles_dir,
            )
            base_arguments.extend(_sphinx_define(config_name, str(resolved_path)))

    if is_bazel_build:
        # The Bazel action declares ``build_dir`` as its output tree, and that
        # tree must contain only the Needs inventory consumed by downstream
        # actions. Keep Sphinx's internal doctree cache beside it instead of
        # mixing action state into the declared output.
        base_arguments.extend(["-d", str(build_dir) + "_doctrees"])

    else:
        # Interactive builds keep warnings in the workspace so developers can
        # inspect them after a failed build. A Bazel action reports failure
        # through its exit code and must leave its declared output tree free of
        # this diagnostic side file.
        base_arguments.extend(["--warning-file", str(build_dir / "warnings.txt")])

    generated_config = _config_string(config, "config_file", "")
    if generated_config:
        config_file = _resolve_context_path(
            generated_config,
            is_bazel_build=is_bazel_build,
            ws_root=ws_root,
            runfiles_dir=runfiles_dir,
        )
        base_arguments.extend(["-c", str(config_file.parent)])

    if github_repository := os.getenv("GITHUB_REPOSITORY"):
        # GITHUB_REPOSITORY is expected as "owner/repo"; partition("/") splits
        # once into (owner, separator, repo), so we can ignore the separator.
        github_user, _, github_repo = github_repository.partition("/")

        base_arguments.append(f"-A=github_user={github_user}")
        base_arguments.append(f"-A=github_repo={github_repo}")
        base_arguments.append("-A=github_version=main")
        # doc_path must be repo-relative so the edit URL does not contain the
        # absolute runner filesystem path (e.g. /home/runner/work/…/docs).
        relative_doc_path = (
            Path(_config_string(config, "package_directory", "")) / source_directory
        )
        base_arguments.append(f"-A=doc_path={relative_doc_path}")

    return base_arguments


def watch_arguments(
    config: dict[str, Any], ws_root: Path | None, runfiles_dir: Path | None
) -> list[str]:
    """Build autobuild options using the payload's resolved mount manifest."""
    mounts_manifest = _config_optional_string(config, "mounts_manifest")
    watch_arguments: list[str] = []
    if mounts_manifest:
        manifest_path = _resolve_context_path(
            mounts_manifest,
            is_bazel_build=False,
            ws_root=ws_root,
            runfiles_dir=runfiles_dir,
        )
        for watch_dir in mounted_watch_dirs(
            manifest_path,
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
    config = parse_docs_config()
    args = parse_args(argv)
    if args.debug:
        debugpy.listen(("0.0.0.0", args.debug_port))
        logger.info("Waiting for client to connect on port: " + str(args.debug_port))
        debugpy.wait_for_client()

    action = _config_string(config, "action")
    is_bazel_build = action == "build_needs_json"
    ws_root = find_ws_root()
    runtime_paths = [
        _config_string(config, "config_file", ""),
        _config_optional_string(config, "mounts_manifest") or "",
        _config_optional_string(config, "source_links") or "",
        _config_optional_string(config, "metamodel") or "",
        _config_optional_string(config, "known_good") or "",
    ]
    # Avoid requiring a complete runfiles tree for ordinary local builds that
    # only use workspace paths. Bazel-run targets with generated inputs have at
    # least one relative runtime path and obtain the real runfiles directory.
    needs_runfiles = any(
        path and not Path(path).is_absolute() for path in runtime_paths
    )
    runfiles_dir = (
        get_runfiles_dir() if ws_root is not None and needs_runfiles else None
    )

    if is_bazel_build:
        # Bazel owns the action's paths; never use the caller's workspace cache.
        package_dir = Path.cwd()
        build_dir = _resolve_context_path(
            _config_string(config, "output_directory"),
            is_bazel_build=True,
            ws_root=None,
            runfiles_dir=None,
        )
    else:
        # Interactive output is relative to the package containing docs(). An
        # absent workspace marker is supported for direct CLI experimentation.
        effective_ws_root = ws_root or Path.cwd()
        package_dir = effective_ws_root / _config_string(
            config, "package_directory", ""
        )
        output_directory = _config_string(config, "output_directory", "_build")
        build_dir = (
            Path(output_directory)
            if Path(output_directory).is_absolute()
            else package_dir / output_directory
        )

    effective_ws_root = ws_root or Path.cwd()

    sentinel_files = [
        effective_ws_root / "MODULE.bazel",
        effective_ws_root / "MODULE.bazel.lock",
        package_dir / "BUILD",
    ]
    if not is_bazel_build:
        clean_builddir_if_stale(build_dir, sentinel_files)

    warning_file = build_dir / "warnings.txt"
    base_arguments = sphinx_arguments(
        config, ws_root, package_dir, build_dir, runfiles_dir
    )

    if action == "live_preview":
        sphinx_autobuild_main(
            base_arguments
            + [
                # Note: bools need to be passed via '0' and '1' from the command line.
                "--define=skip_rescanning_via_source_code_linker=1",
                f"--port={args.port}",
            ]
            + watch_arguments(config, ws_root, runfiles_dir)
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
        update_module_hash(build_dir, sentinel_files)
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
