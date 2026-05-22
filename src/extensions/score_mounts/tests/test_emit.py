# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
import tomllib
from pathlib import Path

from src.extensions.score_mounts._emit import sanitize_bundle_toml_text, write_fragment


def test_write_fragment_single_entry(tmp_path: Path):
    resolved = [
        {
            "dir": "/abs/path/to/docs_dir",
            "mount_at": "_mounted/internal",
            "attach_to": "index",
            "entry_doc": "index",
        }
    ]
    fragment = write_fragment(resolved, outdir=tmp_path)
    assert fragment.is_file()
    parsed = tomllib.loads(fragment.read_text())
    assert parsed == {
        "mounts": [
            {
                "dir": "/abs/path/to/docs_dir",
                "mount_at": "_mounted/internal",
                "attach_to": "index",
            }
        ]
    }


def test_write_fragment_omits_attach_to_when_none(tmp_path: Path):
    resolved = [
        {
            "dir": "/abs/path",
            "mount_at": "_mounted/x",
            "attach_to": None,
            "entry_doc": "index",
        }
    ]
    fragment = write_fragment(resolved, outdir=tmp_path)
    parsed = tomllib.loads(fragment.read_text())
    assert "attach_to" not in parsed["mounts"][0]


def test_write_fragment_emits_non_default_entry_doc(tmp_path: Path):
    resolved = [
        {
            "dir": "/abs/path",
            "mount_at": "_mounted/x",
            "attach_to": None,
            "entry_doc": "start",
        }
    ]
    fragment = write_fragment(resolved, outdir=tmp_path)
    parsed = tomllib.loads(fragment.read_text())
    assert parsed["mounts"][0]["entry_doc"] == "start"


def test_write_fragment_multiple_entries(tmp_path: Path):
    resolved = [
        {"dir": "/a", "mount_at": "_mounted/a", "attach_to": None, "entry_doc": "index"},
        {"dir": "/b", "mount_at": "_mounted/b", "attach_to": "index", "entry_doc": "index"},
    ]
    fragment = write_fragment(resolved, outdir=tmp_path)
    parsed = tomllib.loads(fragment.read_text())
    assert len(parsed["mounts"]) == 2
    assert parsed["mounts"][0]["mount_at"] == "_mounted/a"
    assert parsed["mounts"][1]["attach_to"] == "index"


def test_sanitize_drops_top_level_mounts():
    host = '''[needs]
build_json = true

[[mounts]]
dir = "../bazel-bin/src/docs_dir"
mount_at = "_mounted/internal"
'''
    result = sanitize_bundle_toml_text(host)
    assert "mounts" not in tomllib.loads(result)
    assert tomllib.loads(result)["needs"]["build_json"] is True


def test_sanitize_drops_external_needs_and_banned_keys():
    host = '''[needs]
build_json = true
schema_definitions_from_json = "schemas.json"
schema_debug_path = "/abs/path"
build_needumls = "_plantuml_sources"

[[needs.external_needs]]
base_url = "https://example.com"
json_path = "../bazel-bin/foo/needs.json"

[[needs.types]]
directive = "req"
title = "Requirement"
prefix = "R_"
'''
    parsed = tomllib.loads(sanitize_bundle_toml_text(host))
    assert "external_needs" not in parsed["needs"]
    assert "schema_definitions_from_json" not in parsed["needs"]
    assert "schema_debug_path" not in parsed["needs"]
    assert "build_needumls" not in parsed["needs"]
    # Preserved entries:
    assert parsed["needs"]["build_json"] is True
    assert parsed["needs"]["types"][0]["directive"] == "req"
