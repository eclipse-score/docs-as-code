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

"""Unit tests for the Sphinx-Needs JSON merge tool."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem as FFS

from scripts_bazel import merge_needs_json


def _write_json(fs: FFS, path: Path, data: object) -> Path:
    fs.create_file(path, contents=json.dumps(data))
    return path


def test_merges_all_needs_and_ignores_version_keys(fs: FFS) -> None:
    first = _write_json(
        fs,
        Path("/inputs/first.json"),
        {
            "current_version": "first-version",
            "project": "first project",
            "project_url": "https://example.test/first",
            "versions": {
                "first-version": {
                    "created_by": "first",
                    "needs": {
                        "REQ-1": {
                            "id": "REQ-1",
                            "title": "First",
                            "type": "req",
                        }
                    },
                }
            },
        },
    )
    second = _write_json(
        fs,
        Path("/inputs/second.json"),
        {
            "current_version": "second-version",
            "project": "second project",
            "project_url": "https://example.test/second",
            "versions": {
                "second-version": {
                    "created_by": "first",
                    "needs": {
                        "REQ-2": {
                            "id": "REQ-2",
                            "title": "Second",
                            "type": "req",
                        }
                    },
                }
            },
        },
    )
    output = Path("/outputs/nested/merged.json")

    assert (
        merge_needs_json.main(["--output", str(output), str(first), str(second)]) == 0
    )

    merged = json.loads(output.read_text(encoding="utf-8"))
    assert merged["project_url"] == "https://example.test/first"
    assert set(merged["versions"]) == {"first-version"}
    assert merged["versions"]["first-version"]["needs"].keys() == {
        "REQ-1",
        "REQ-2",
    }
    assert merged["versions"]["first-version"]["created_by"] == "first"


def test_identical_duplicate_need_is_ignored(fs: FFS) -> None:
    first_data = {
        "versions": {
            "first-version": {
                "needs": {
                    "REQ-1": {"id": "REQ-1", "type": "req"},
                }
            }
        }
    }
    first = _write_json(fs, Path("/inputs/first.json"), first_data)
    second = _write_json(fs, Path("/inputs/second.json"), first_data)
    output = Path("/outputs/merged.json")

    assert (
        merge_needs_json.main(["--output", str(output), str(first), str(second)]) == 0
    )

    merged = json.loads(output.read_text(encoding="utf-8"))
    assert list(merged["versions"]["first-version"]["needs"]) == ["REQ-1"]


def test_conflicting_need_returns_error_without_writing_output(
    fs: FFS, capsys: pytest.CaptureFixture[str]
) -> None:
    first = _write_json(
        fs,
        Path("/inputs/first.json"),
        {
            "versions": {
                "first-version": {
                    "needs": {
                        "REQ-1": {
                            "id": "REQ-1",
                            "title": "First",
                            "type": "req",
                        }
                    }
                }
            }
        },
    )
    second = _write_json(
        fs,
        Path("/inputs/second.json"),
        {
            "versions": {
                "other-version": {
                    "needs": {
                        "REQ-1": {
                            "id": "REQ-1",
                            "title": "Different",
                            "type": "req",
                        }
                    }
                }
            }
        },
    )
    output = Path("/outputs/merged.json")
    _write_json(fs, output, {"previous": "result"})

    assert (
        merge_needs_json.main(["--output", str(output), str(first), str(second)]) == 1
    )

    assert json.loads(output.read_text(encoding="utf-8")) == {"previous": "result"}
    captured = capsys.readouterr()
    assert "conflicting Need 'REQ-1'" in captured.err
    assert "first.json" in captured.err
    assert "second.json" in captured.err


@pytest.mark.parametrize(("boolean", "number"), [(True, 1), (False, 0)])
def test_json_comparison_distinguishes_booleans_from_numbers(
    boolean: bool,
    number: int,
) -> None:
    assert not merge_needs_json._json_values_equal(  # pyright: ignore[reportPrivateUsage]
        {"nested": [boolean]},
        {"nested": [number]},
    )


def test_ignores_version_metadata_and_recalculates_needs_amount(fs: FFS) -> None:
    first = _write_json(
        fs,
        Path("/inputs/first.json"),
        {
            "versions": {
                "first-version": {
                    "created_by": "first",
                    "needs_amount": 1,
                    "needs": {
                        "REQ-1": {"id": "REQ-1", "type": "req"},
                    },
                }
            }
        },
    )
    second = _write_json(
        fs,
        Path("/inputs/second.json"),
        {
            "versions": {
                "second-version": {
                    "created_by": "second",
                    "needs_amount": 999,
                    "needs": {
                        "REQ-2": {"id": "REQ-2", "type": "req"},
                    },
                }
            }
        },
    )

    merged = merge_needs_json.merge_needs_json([first, second])
    raw_merged_versions = merged["versions"]
    assert isinstance(raw_merged_versions, dict)
    merged_versions = cast(dict[str, object], raw_merged_versions)
    raw_merged_version = merged_versions["first-version"]
    assert isinstance(raw_merged_version, dict)
    merged_version = cast(dict[str, object], raw_merged_version)
    assert merged_version["created_by"] == "first"
    assert merged_version["needs_amount"] == 2
    raw_merged_needs = merged_version["needs"]
    assert isinstance(raw_merged_needs, dict)
    merged_needs = cast(dict[str, object], raw_merged_needs)
    assert set(merged_needs) == {"REQ-1", "REQ-2"}


@pytest.mark.parametrize(
    ("payload", "expected_error"),
    [
        ({"project": "missing versions"}, "field 'versions' must be an object"),
        (
            {"versions": {}},
            "field 'versions' must contain exactly one entry, got 0",
        ),
        (
            {"versions": {"1.0": {}, "2.0": {}}},
            "field 'versions' must contain exactly one entry, got 2",
        ),
        (
            {"versions": {"1.0": {}}},
            "version '1.0' must contain object 'needs'",
        ),
        (
            {"versions": {"1.0": {"needs": {"REQ-1": None}}}},
            "Need 'REQ-1' in version '1.0' must be an object",
        ),
    ],
)
def test_rejects_invalid_schema(
    fs: FFS,
    capsys: pytest.CaptureFixture[str],
    payload: object,
    expected_error: str,
) -> None:
    source = _write_json(fs, Path("/inputs/invalid.json"), payload)
    output = Path("/outputs/merged.json")

    assert merge_needs_json.main(["--output", str(output), str(source)]) == 1

    captured = capsys.readouterr()
    assert expected_error in captured.err
    assert "invalid.json" in captured.err
    assert not output.exists()


def test_rejects_invalid_json(fs: FFS, capsys: pytest.CaptureFixture[str]) -> None:
    source = Path("/inputs/invalid.json")
    fs.create_file(source, contents="{not json")
    output = Path("/outputs/merged.json")

    assert merge_needs_json.main(["--output", str(output), str(source)]) == 1

    assert "invalid JSON at line 1, column 2" in capsys.readouterr().err
    assert not output.exists()


@pytest.mark.parametrize(
    ("contents", "expected_error"),
    [
        (
            '{"versions": {"v": {"needs": {}}}, "versions": {"other": {"needs": {}}}}',
            "duplicate object key 'versions'",
        ),
        (
            '{"versions": {"v": {"needs": {"REQ-1": {"score": NaN}}}}}',
            "non-standard JSON constant 'NaN' is not allowed",
        ),
    ],
)
def test_rejects_non_canonical_json(
    fs: FFS,
    capsys: pytest.CaptureFixture[str],
    contents: str,
    expected_error: str,
) -> None:
    source = Path("/inputs/non_canonical.json")
    fs.create_file(source, contents=contents)
    output = Path("/outputs/merged.json")

    assert merge_needs_json.main(["--output", str(output), str(source)]) == 1

    captured = capsys.readouterr()
    assert expected_error in captured.err
    assert "non_canonical.json" in captured.err
    assert not output.exists()


def test_failed_output_serialization_keeps_existing_file(
    fs: FFS,
) -> None:
    output = Path("/outputs/merged.json")
    _write_json(fs, output, {"previous": "result"})

    with pytest.raises(ValueError, match="Out of range float values"):
        merge_needs_json._write_needs_json(  # pyright: ignore[reportPrivateUsage]
            output, {"invalid": float("nan")}
        )

    assert json.loads(output.read_text(encoding="utf-8")) == {"previous": "result"}
