# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Merge Sphinx-Needs ``needs.json`` files into one inventory.

The first input provides the top-level metadata (for example ``project_url``).
Each input is expected to contain exactly one entry under ``versions``.  The
entry's version key is only a Sphinx-Needs serialization detail and is not used
for merging.  An identical Need may occur in more than one input, but the same
Need ID with different content is an error because silently choosing one of the
definitions would produce an unreliable inventory.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path
from typing import NoReturn, cast

JsonObject = dict[str, object]
_MISSING = object()


def _schema_error(path: Path, message: str) -> ValueError:
    return ValueError(f"invalid needs.json {path}: {message}")


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> JsonObject:
    """Build a JSON object while rejecting duplicate keys.

    Python's default JSON decoder silently keeps the last value for duplicate
    keys.  That is dangerous for an inventory because a malformed input could
    change a Need without leaving any trace in the merge output.
    """
    result: JsonObject = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate object key {key!r}")
        result[key] = value
    return result


def _reject_non_standard_constant(value: str) -> NoReturn:
    """Reject NaN and infinities, which are not valid JSON values."""
    raise ValueError(f"non-standard JSON constant {value!r} is not allowed")


def _single_version(data: JsonObject, source_path: Path) -> tuple[str, JsonObject]:
    """Validate and return the one version container from one needs document."""
    raw_versions = data.get("versions")
    if not isinstance(raw_versions, dict):
        raise _schema_error(source_path, "field 'versions' must be an object")
    versions = cast(dict[object, object], raw_versions)
    if len(versions) != 1:
        raise _schema_error(
            source_path,
            f"field 'versions' must contain exactly one entry, got {len(versions)}",
        )

    version, raw_version = next(iter(versions.items()))
    if not isinstance(version, str):
        raise _schema_error(source_path, "version keys must be strings")
    if not isinstance(raw_version, dict):
        raise _schema_error(source_path, f"version {version!r} must be an object")

    version_data = cast(JsonObject, raw_version)
    raw_needs = version_data.get("needs")
    if not isinstance(raw_needs, dict):
        raise _schema_error(
            source_path,
            f"version {version!r} must contain object 'needs'",
        )
    needs = cast(dict[object, object], raw_needs)
    for need_id, need in needs.items():
        if not isinstance(need_id, str):
            raise _schema_error(
                source_path,
                f"version {version!r} contains a non-string Need ID",
            )
        if not isinstance(need, dict):
            raise _schema_error(
                source_path,
                f"Need {need_id!r} in version {version!r} must be an object",
            )

    return version, version_data


def _load_needs_json(path: Path) -> JsonObject:
    """Load and validate one input file, adding its path to schema errors."""
    try:
        with path.open(encoding="utf-8") as file:
            raw_data: object = json.load(
                file,
                object_pairs_hook=_reject_duplicate_keys,
                parse_constant=_reject_non_standard_constant,
            )
    except json.JSONDecodeError as exc:
        raise _schema_error(
            path,
            f"invalid JSON at line {exc.lineno}, column {exc.colno}: {exc.msg}",
        ) from exc
    except OSError as exc:
        raise ValueError(f"could not read needs.json {path}: {exc}") from exc
    except UnicodeDecodeError as exc:
        raise _schema_error(path, f"file is not valid UTF-8: {exc.reason}") from exc
    except ValueError as exc:
        raise _schema_error(path, f"invalid JSON: {exc}") from exc

    if not isinstance(raw_data, dict):
        raise _schema_error(path, "top-level value must be an object")

    data = cast(JsonObject, raw_data)
    _single_version(data, path)
    return data


def _json_values_equal(left: object, right: object) -> bool:
    """Compare values using JSON's types instead of Python's equality rules."""
    return json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


def _merge_needs(
    destination_version: JsonObject,
    source_version: JsonObject,
    source_path: Path,
    need_sources: dict[str, Path],
) -> None:
    """Merge Needs from one version container and refresh derived metadata."""
    destination_needs = cast(JsonObject, destination_version["needs"])
    source_needs = cast(JsonObject, source_version["needs"])

    for need_id, need in source_needs.items():
        existing = destination_needs.get(need_id, _MISSING)
        if existing is not _MISSING and not _json_values_equal(existing, need):
            raise ValueError(
                f"conflicting Need {need_id!r} between "
                f"{need_sources[need_id]} and {source_path}"
            )
        if existing is _MISSING:
            destination_needs[need_id] = need
            need_sources[need_id] = source_path

    # Sphinx-Needs exports this value next to ``needs``. It is derived from the
    # inventory and must describe the merged result, not the first input.
    destination_version["needs_amount"] = len(destination_needs)


def merge_needs_json(files: Sequence[Path]) -> JsonObject:
    """Return the merged inventory for ``files``.

    The first file is copied as the base document, so its top-level metadata
    remains authoritative.  Its one version key is retained only as the output
    container key; version keys from later files are ignored.  All input files
    are validated, including the first one even when it is the only input.
    """
    if not files:
        raise ValueError("at least one needs.json input is required")

    merged = _load_needs_json(files[0])
    output_version, destination_version = _single_version(merged, files[0])
    destination_needs = cast(JsonObject, destination_version["needs"])
    need_sources = {need_id: files[0] for need_id in destination_needs}
    destination_version["needs_amount"] = len(destination_needs)

    for source_path in files[1:]:
        source = _load_needs_json(source_path)
        _, source_version = _single_version(source, source_path)
        _merge_needs(
            destination_version,
            source_version,
            source_path,
            need_sources,
        )

    merged["versions"] = {output_version: destination_version}
    return merged


def _write_needs_json(path: Path, data: JsonObject) -> None:
    """Atomically write JSON with stable formatting.

    The temporary file is created beside the destination so ``os.replace`` is
    atomic on the filesystems used by Bazel.  This also means a failed write
    cannot leave a partially-written needs.json behind.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    file_descriptor: int | None = None
    try:
        file_descriptor, temporary_name = tempfile.mkstemp(
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
        )
        temporary_path = Path(temporary_name)
        with os.fdopen(file_descriptor, "w", encoding="utf-8") as file:
            file_descriptor = None
            json.dump(data, file, indent=2, ensure_ascii=False, allow_nan=False)
            file.write("\n")
            file.flush()
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if file_descriptor is not None:
            os.close(file_descriptor)
        if temporary_path is not None:
            with suppress(FileNotFoundError):
                temporary_path.unlink()


def main(argv: list[str] | None = None) -> int:
    """Run the merge CLI and return zero on success, one on input failure."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", required=True, type=Path, help="Path for the merged needs.json"
    )
    parser.add_argument(
        "files", nargs="+", type=Path, help="Input Sphinx-Needs needs.json files"
    )
    args = parser.parse_args(argv)

    try:
        merged = merge_needs_json(args.files)
        _write_needs_json(args.output, merged)
    except (OSError, ValueError) as exc:
        print(f"merge_needs_json: error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
