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

"""Copy ``docs_assets`` files unchanged into the HTML output.

``sphinx_mounts`` only mounts documents that Sphinx reads. Assets (Doxygen
HTML, PDFs, images, ...) are never read by Sphinx; they are copied into the
output at the destination Bazel computed for them in the mounts manifest."""

from __future__ import annotations

import os
import shutil
from collections.abc import Iterable, Mapping
from pathlib import Path, PurePosixPath

from src.extensions.score_mounts._resolver import AssetSpec, resolve_output_file


def plan_asset_copies(
    assets: Iterable[AssetSpec],
    ws_root: Path | None,
    runfiles_dir: Path | None = None,
) -> dict[str, Path]:
    """Map each output path, relative to the HTML output root, to its source.

    A directory's contents keep their sub-structure below the destination; a
    file goes to ``<destination>/<basename>``. An empty destination is the
    output root. Two assets writing the same output path are rejected.
    """
    copies: dict[str, Path] = {}
    for asset in assets:
        source = resolve_output_file(asset.path, ws_root, runfiles_dir)
        exists = source.is_dir() if asset.is_directory else source.is_file()
        if not exists:
            raise ValueError(
                "score_mounts: resolved asset does not exist: "
                f"{source} (destination={asset.destination or '.'})"
            )
        destination = PurePosixPath(asset.destination)
        if asset.is_directory:
            planned = _directory_files(source, destination)
        else:
            planned = [((destination / source.name).as_posix(), source)]
        for output_path, source_file in planned:
            if output_path in copies:
                raise ValueError(
                    f"score_mounts: asset output path {output_path} is written by "
                    f"both {copies[output_path]} and {source_file}"
                )
            copies[output_path] = source_file
    return copies


# Folders the HTML builder fills itself, relative to the output root.
_SPHINX_RESERVED_DIRS = ("_static", "_images", "_sources", "_downloads")
# Files the HTML builder writes at the output root besides the pages.
_SPHINX_ROOT_FILES = frozenset(
    {"genindex.html", "search.html", "searchindex.js", "objects.inv", ".buildinfo"}
)


def check_asset_conflicts(
    copies: Mapping[str, Path], sphinx_pages: Iterable[str]
) -> None:
    """Reject an asset that would overwrite output written by Sphinx.

    ``sphinx_pages`` are the output paths of all pages, as the builder's
    target URIs (for example ``child/index.html``). The previous build's
    copy of an asset is not a conflict, so this check never looks at what is
    already on disk.
    """
    pages = set(sphinx_pages)
    for output_path, source in copies.items():
        first_part = PurePosixPath(output_path).parts[0]
        if (
            output_path in pages
            or output_path in _SPHINX_ROOT_FILES
            or first_part in _SPHINX_RESERVED_DIRS
        ):
            raise ValueError(
                f"score_mounts: asset {source} would overwrite Sphinx output "
                f"{output_path}; mount it at a different place"
            )


def copy_assets(copies: Mapping[str, Path], outdir: Path) -> int:
    """Copy every planned asset below ``outdir`` and return how many were copied.

    A target whose size and modification time match its source is left alone;
    copying keeps the source's metadata so the next build can skip it.
    """
    copied = 0
    for output_path, source in copies.items():
        target = outdir / output_path
        source_stat = source.stat()
        if target.is_file():
            target_stat = target.stat()
            if (
                target_stat.st_size == source_stat.st_size
                and target_stat.st_mtime_ns == source_stat.st_mtime_ns
            ):
                continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        copied += 1
    return copied


def _directory_files(
    source: Path, destination: PurePosixPath
) -> list[tuple[str, Path]]:
    """List every file below ``source`` with its output path.

    In the runfiles tree, files and directories are symlinks into Bazel's
    output tree, so the walk follows them.
    """
    planned: list[tuple[str, Path]] = []
    for root, _dirs, files in os.walk(source, followlinks=True):
        relative_root = Path(root).relative_to(source)
        for name in files:
            output_path = destination / PurePosixPath(*relative_root.parts, name)
            planned.append((output_path.as_posix(), Path(root) / name))
    return planned
