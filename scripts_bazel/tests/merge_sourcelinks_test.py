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

"""Tests for merge_sourcelinks.py"""

import json
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem as FFS
from score_pytest.attribute_plugin import add_test_properties

from scripts_bazel.merge_sourcelinks import main as merge_sourcelinks
from src.helper_lib.repo_info import LOCAL_REPO


def link(file: str) -> dict[str, str | int]:
    """A source link found in `file`; combine it with `repo(...)`."""
    return {
        "file": file,
        "line": 10,
        "tag": "# req-Id:",
        "need": "tool_req__docs_arch_types",
        "full_line": "# req-Id: tool_req__docs_arch_types",
    }


def repo(name: str, hash: str = "", url: str = "") -> dict[str, str | int]:
    return {"repo_name": name, "hash": hash, "url": url}


def write_json(fs: FFS, path: str, data: object) -> None:
    fs.create_file(path, contents=json.dumps(data))


def read_json(path: str) -> object:
    return json.loads(Path(path).read_text())


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_merge_sourcelinks_basic(fs: FFS):
    """Each link gets the repository of its file's header."""
    write_json(fs, "a.json", [repo(LOCAL_REPO), link("a.py")])
    write_json(fs, "b.json", [repo(LOCAL_REPO), link("b.py")])

    merge_sourcelinks(["--output", "merged.json", "a.json", "b.json"])

    assert read_json("merged.json") == [
        link("a.py") | repo(LOCAL_REPO),
        link("b.py") | repo(LOCAL_REPO),
    ]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_merge_sourcelinks_deduplicates_identical_references(fs: FFS):
    """The same link from two inputs appears once in the output."""
    write_json(fs, "a.json", [repo(LOCAL_REPO), link("a.py")])

    merge_sourcelinks(["--output", "merged.json", "a.json", "a.json"])

    assert read_json("merged.json") == [link("a.py") | repo(LOCAL_REPO)]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_merge_sourcelinks_with_one_empty_file(fs: FFS):
    """An input without any entry is a no-op."""
    write_json(fs, "a.json", [repo(LOCAL_REPO), link("a.py")])
    write_json(fs, "empty.json", [])

    merge_sourcelinks(["--output", "merged.json", "a.json", "empty.json"])

    assert read_json("merged.json") == [link("a.py") | repo(LOCAL_REPO)]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_merge_sourcelinks_wrong_schema(fs: FFS, caplog: pytest.LogCaptureFixture):
    """An input that does not start with the repository header is not merged."""
    write_json(fs, "a.json", [link("a.py")])

    merge_sourcelinks(["--output", "merged.json", "a.json"])

    assert read_json("merged.json") == []
    assert (
        "Unexpected schema in sourcelinks file 'a.json': "
        "expected first element to be a metadata dict with a 'repo_name' key. "
    ) in caplog.text


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_merge_sourcelinks_with_known_good(fs: FFS):
    """known_good.json replaces URL and hash; the local repository stays empty."""
    baselibs = repo(
        "score_baselibs",
        hash="old-hash",
        url="https://github.com/eclipse-score/baselibs.git",
    )
    write_json(fs, "external.json", [baselibs, link("external.py")])
    write_json(fs, "local.json", [repo(LOCAL_REPO), link("local.py")])
    write_json(
        fs,
        "known_good.json",
        {
            "modules": {
                "target_sw": {
                    "score_baselibs": {
                        "repo": "https://github.com/eclipse-score/baselibs.git",
                        "hash": "abc123",
                    }
                }
            }
        },
    )

    merge_sourcelinks(
        [
            "--output",
            "merged.json",
            "--known_good",
            "known_good.json",
            "external.json",
            "local.json",
        ]
    )

    assert read_json("merged.json") == [
        link("external.py")
        | repo(
            "score_baselibs",
            hash="abc123",
            url="https://github.com/eclipse-score/baselibs",
        ),
        link("local.py") | repo(LOCAL_REPO),
    ]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_merge_sourcelinks_without_known_good_preserves_external_metadata(fs: FFS):
    """Standalone builds have no known_good.json; URL and hash stay as they are."""
    baselibs = repo(
        "score_baselibs",
        hash="abc123",
        url="https://github.com/eclipse-score/baselibs.git",
    )
    write_json(fs, "external.json", [baselibs, link("external.py")])
    write_json(fs, "local.json", [repo(LOCAL_REPO), link("local.py")])

    merge_sourcelinks(["--output", "merged.json", "external.json", "local.json"])

    assert read_json("merged.json") == [
        link("external.py") | baselibs,
        link("local.py") | repo(LOCAL_REPO),
    ]
