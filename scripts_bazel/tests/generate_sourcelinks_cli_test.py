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

"""Tests for generate_sourcelinks_cli.py"""

import json
from pathlib import Path

import pytest
from pyfakefs.fake_filesystem import FakeFilesystem as FFS
from score_pytest.attribute_plugin import add_test_properties

from scripts_bazel.generate_sourcelinks_cli import main as generate_sourcelinks_cli
from src.helper_lib.repo_info import LOCAL_REPO


def link(file: str, line: int, tag: str, repo_name: str) -> dict[str, str | int]:
    """The JSON entry for a source line `<tag> tool_req__docs_arch_types`."""
    return {
        "file": file,
        "line": line,
        "tag": tag,
        "need": "tool_req__docs_arch_types",
        "full_line": f"{tag} tool_req__docs_arch_types",
        "repo_name": repo_name,
        # The merge fills in hash and url.
        "hash": "",
        "url": "",
    }


def read_json(path: str) -> object:
    return json.loads(Path(path).read_text())


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_generate_sourcelinks_cli_basic(fs: FFS):
    """A `#` tag is stored with its file, line and need below the local repository."""
    fs.create_file(
        "src/source.py",
        contents="# Some code here\n# req-Id: tool_req__docs_arch_types\ndef f(): pass\n",
    )

    generate_sourcelinks_cli(["--output", "links.json", "src/source.py"])

    assert read_json("links.json") == [
        {"repo_name": LOCAL_REPO, "hash": "", "url": ""},
        link("src/source.py", line=2, tag="# req-Id:", repo_name=LOCAL_REPO),
    ]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_generate_sourcelinks_cli_parses_cpp_traceability_tag(fs: FFS):
    """A `//` tag is recognized as well."""
    fs.create_file("src/source.cc", contents="// req-Id: tool_req__docs_arch_types\n")

    generate_sourcelinks_cli(["--output", "links.json", "src/source.cc"])

    assert read_json("links.json") == [
        {"repo_name": LOCAL_REPO, "hash": "", "url": ""},
        link("src/source.cc", line=1, tag="// req-Id:", repo_name=LOCAL_REPO),
    ]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_generate_sourcelinks_cli_parse_external_module(fs: FFS):
    """`external/<repo>+/` names the repository and is cut from the file path."""
    fs.create_file(
        "external/score_baselibs+/src/source.py",
        contents="# req-Id: tool_req__docs_arch_types\n",
    )

    generate_sourcelinks_cli(
        ["--output", "links.json", "external/score_baselibs+/src/source.py"]
    )

    assert read_json("links.json") == [
        {"repo_name": "score_baselibs", "hash": "", "url": ""},
        link("src/source.py", line=1, tag="# req-Id:", repo_name=LOCAL_REPO),
    ]


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_generate_sourcelinks_cli_file_not_exists(fs: FFS):
    """A source file that does not exist aborts the generator."""
    with pytest.raises(AssertionError):
        generate_sourcelinks_cli(["--output", "links.json", "src/missing.py"])
