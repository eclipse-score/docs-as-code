# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
import pytest

from src.extensions.score_mounts._resolver import (
    MountSpec,
    label_to_bazel_bin_path,
    label_to_runfile_path,
    parse_mounts_source,
)


def test_parse_empty_string():
    assert parse_mounts_source("") == []


def test_parse_empty_list():
    assert parse_mounts_source("[]") == []


def test_parse_single_entry():
    raw = '[{"label": "//src:docs_dir", "mount_at": "_mounted/internal"}]'
    assert parse_mounts_source(raw) == [
        MountSpec(label="//src:docs_dir", mount_at="_mounted/internal"),
    ]


def test_parse_entry_with_attach_to_and_entry_doc():
    raw = (
        '[{"label": "//src:docs_dir", "mount_at": "_mounted/x", '
        '"attach_to": "index", "entry_doc": "start"}]'
    )
    assert parse_mounts_source(raw) == [
        MountSpec(
            label="//src:docs_dir",
            mount_at="_mounted/x",
            attach_to="index",
            entry_doc="start",
        ),
    ]


def test_parse_multiple_entries():
    raw = (
        '[{"label": "//src:docs_dir", "mount_at": "_mounted/a"},'
        ' {"label": "@x//:docs_sources", "mount_at": "_mounted/b"}]'
    )
    result = parse_mounts_source(raw)
    assert len(result) == 2
    assert result[0].mount_at == "_mounted/a"
    assert result[1].label == "@x//:docs_sources"


def test_parse_missing_required_key_raises():
    raw = '[{"label": "//src:docs_dir"}]'
    with pytest.raises(ValueError, match="missing required keys"):
        parse_mounts_source(raw)


def test_parse_non_list_raises():
    raw = '{"label": "//src:docs_dir", "mount_at": "x"}'
    with pytest.raises(ValueError, match="must decode to a list"):
        parse_mounts_source(raw)


def test_label_to_runfile_main_repo_with_path():
    assert label_to_runfile_path("//src:docs_dir") == "_main/src/docs_dir"


def test_label_to_runfile_main_repo_root_package():
    assert label_to_runfile_path("//:docs_dir") == "_main/docs_dir"


def test_label_to_runfile_external_root_package():
    assert label_to_runfile_path("@score_process//:docs_sources") == (
        "score_process+/docs_sources"
    )


def test_label_to_runfile_external_with_path():
    assert label_to_runfile_path("@x//foo/bar:baz") == "x+/foo/bar/baz"


def test_label_to_runfile_invalid_raises():
    with pytest.raises(ValueError):
        label_to_runfile_path("not_a_label")


def test_label_to_bazel_bin_main_repo_with_path():
    assert label_to_bazel_bin_path("//src:docs_dir") == "bazel-bin/src/docs_dir"


def test_label_to_bazel_bin_main_repo_root_package():
    assert label_to_bazel_bin_path("//:docs_dir") == "bazel-bin/docs_dir"


def test_label_to_bazel_bin_external_root_package():
    assert label_to_bazel_bin_path("@score_process//:docs_sources") == (
        "bazel-bin/external/score_process+/docs_sources"
    )


def test_label_to_bazel_bin_external_with_path():
    assert label_to_bazel_bin_path("@x//foo/bar:baz") == "bazel-bin/external/x+/foo/bar/baz"
