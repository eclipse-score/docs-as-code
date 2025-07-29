# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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
import pytest

from ..external_needs import ExternalNeedsSource, parse_external_needs_sources_from_DATA


def test_empty_list():
    assert parse_external_needs_sources_from_DATA("[]") == []


def test_single_entry_with_path():
    result = parse_external_needs_sources_from_DATA('["@repo//foo/bar:baz"]')
    # IF a target has a path, it will not be reported as external needs
    assert result == []


def test_single_entry_no_path():
    result = parse_external_needs_sources_from_DATA('["@repo//:target"]')
    # If a target is not named "needs_json", it will not be reported as external needs
    assert result == []


def test_single_entry_json_no_path():
    result = parse_external_needs_sources_from_DATA('["@repo//:needs_json"]')
    assert result == [
        ExternalNeedsSource(bazel_module="repo", path_to_target="", target="needs_json")
    ]


def test_multiple_entries():
    result = parse_external_needs_sources_from_DATA(
        '["@repo1//:needs_json", "@repo2//:needs_json"]'
    )
    assert result == [
        ExternalNeedsSource(
            bazel_module="repo1", path_to_target="", target="needs_json"
        ),
        ExternalNeedsSource(
            bazel_module="repo2", path_to_target="", target="needs_json"
        ),
    ]


def test_multiple_entries_2():
    result = parse_external_needs_sources_from_DATA(
        '["@repo1//:needs_json", "@repo2//path:needs_json"]'
    )

    assert result == [
        ExternalNeedsSource(
            bazel_module="repo1", path_to_target="", target="needs_json"
        )
    ]


def test_invalid_entry():
    with pytest.raises(ValueError):
        _ = parse_external_needs_sources_from_DATA('["@not_a_valid_string"]')


def test_parser(): ...
