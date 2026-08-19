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
"""Unit tests for :mod:`score_module_verification_report.scanner`."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from src.extensions.score_module_verification_report.scanner import (
    discover_components,
    module_includes,
    scan_rst_needs,
    scan_source_tree,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ---------------------------------------------------------------------------
# scan_rst_needs
# ---------------------------------------------------------------------------


def test_scan_rst_needs_captures_mod_and_comp(tmp_path: Path) -> None:
    _write(
        tmp_path / "a.rst",
        ".. mod:: My Module\n"
        "   :id: mod__demo\n"
        "   :includes: comp__demo_x, comp__demo_y[version==2]\n"
        "\n"
        ".. comp:: X\n"
        "   :id: comp__demo_x\n"
        "   :safety: ASIL_B\n"
        "\n"
        ".. comp:: Y\n"
        "   :id: comp__demo_y\n"
        "   :version: 2\n",
    )
    needs = scan_rst_needs(str(tmp_path), directives={"mod", "comp"})
    assert len(needs) == 3
    mod = next(n for n in needs if n["directive"] == "mod")
    assert mod["id"] == "mod__demo"
    assert "comp__demo_x" in mod["includes"]
    comp_y = next(n for n in needs if n["id"] == "comp__demo_y")
    assert comp_y["version"] == "2"
    assert comp_y["title"] == "Y"


def test_scan_rst_needs_ignores_other_directives(tmp_path: Path) -> None:
    _write(
        tmp_path / "a.rst",
        ".. comp:: Kept\n"
        "   :id: comp__kept\n"
        "\n"
        ".. document:: Skipped\n"
        "   :id: doc__skipped\n",
    )
    needs = scan_rst_needs(str(tmp_path), directives={"mod", "comp"})
    assert [n["id"] for n in needs] == ["comp__kept"]


def test_scan_rst_needs_skips_entry_without_id(tmp_path: Path) -> None:
    _write(
        tmp_path / "a.rst",
        ".. comp:: Anonymous\n"
        "   :safety: QM\n",
    )
    assert scan_rst_needs(str(tmp_path), directives={"comp"}) == []


def test_scan_rst_needs_skips_non_rst_and_bad_encoding(tmp_path: Path) -> None:
    _write(tmp_path / "a.md", ".. comp:: not rst\n   :id: comp__x\n")
    (tmp_path / "b.rst").write_bytes(b"\xff\xfe not utf-8")
    assert scan_rst_needs(str(tmp_path), directives={"comp"}) == []


def test_scan_rst_needs_walks_recursively(tmp_path: Path) -> None:
    _write(tmp_path / "a.rst", ".. comp:: A\n   :id: comp__a\n")
    _write(tmp_path / "sub" / "b.rst", ".. comp:: B\n   :id: comp__b\n")
    ids = {n["id"] for n in scan_rst_needs(str(tmp_path), directives={"comp"})}
    assert ids == {"comp__a", "comp__b"}


# ---------------------------------------------------------------------------
# module_includes
# ---------------------------------------------------------------------------


def test_module_includes_parses_versions() -> None:
    needs = [
        {
            "directive": "mod",
            "id": "mod__demo",
            "includes": "comp__a, comp__b[version==3]",
        },
    ]
    result = module_includes(needs, "mod__demo")
    assert result == {"comp__a": None, "comp__b": "3"}


def test_module_includes_returns_none_when_mod_not_found() -> None:
    assert module_includes([], "mod__missing") is None


def test_module_includes_ignores_other_mod_needs() -> None:
    needs = [
        {"directive": "mod", "id": "mod__other", "includes": "comp__x"},
        {"directive": "comp", "id": "mod__demo"},
    ]
    assert module_includes(needs, "mod__demo") is None


def test_module_includes_empty_includes() -> None:
    needs = [{"directive": "mod", "id": "mod__demo", "includes": ""}]
    assert module_includes(needs, "mod__demo") == {}


# ---------------------------------------------------------------------------
# discover_components
# ---------------------------------------------------------------------------


def _env(needs: list[dict]) -> SimpleNamespace:
    return SimpleNamespace(module_verification_report_needs=needs)


def test_discover_components_filters_by_whitelist_and_version() -> None:
    env = _env(
        [
            {"directive": "comp", "id": "comp__demo_a", "title": "A"},
            {"directive": "comp", "id": "comp__demo_b", "title": "B",
             "version": "1"},
            {"directive": "comp", "id": "comp__demo_c", "title": "C"},
        ]
    )
    result = discover_components(
        env,
        component_prefix="comp__demo_",
        whitelist={"comp__demo_a": None, "comp__demo_b": "2"},
    )
    assert [c["id"] for c in result] == ["comp__demo_a"]
    assert result[0]["slug"] == "a"
    assert result[0]["title"] == "A"


def test_discover_components_sorted_by_id() -> None:
    env = _env(
        [
            {"directive": "comp", "id": "comp__demo_b", "title": "B"},
            {"directive": "comp", "id": "comp__demo_a", "title": "A"},
        ]
    )
    result = discover_components(
        env,
        component_prefix="comp__demo_",
        whitelist={"comp__demo_a": None, "comp__demo_b": None},
    )
    assert [c["id"] for c in result] == ["comp__demo_a", "comp__demo_b"]


def test_discover_components_prefix_mismatch_keeps_full_id_as_slug() -> None:
    env = _env(
        [{"directive": "comp", "id": "custom__x", "title": "X"}],
    )
    result = discover_components(
        env,
        component_prefix="comp__demo_",
        whitelist={"custom__x": None},
    )
    assert result[0]["slug"] == "custom__x"


def test_discover_components_falls_back_to_id_when_title_missing() -> None:
    env = _env([{"directive": "comp", "id": "comp__demo_a", "title": ""}])
    result = discover_components(
        env,
        component_prefix="comp__demo_",
        whitelist={"comp__demo_a": None},
    )
    assert result[0]["title"] == "comp__demo_a"


def test_discover_components_missing_attr_on_env() -> None:
    # Env may not have the attr yet if the read-hook did not run.
    assert discover_components(SimpleNamespace(), "comp__x_", {"a": None}) == []


# ---------------------------------------------------------------------------
# scan_source_tree
# ---------------------------------------------------------------------------


def test_scan_source_tree_populates_env(tmp_path: Path) -> None:
    _write(tmp_path / "a.rst", ".. mod:: M\n   :id: mod__demo\n")
    env = SimpleNamespace(srcdir=str(tmp_path))
    scan_source_tree(app=None, env=env, docnames=None)
    assert [n["id"] for n in env.module_verification_report_needs] == [
        "mod__demo"
    ]
