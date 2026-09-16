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
"""Unit tests for score_coverage_report's Sphinx wiring.

These tests exercise the extension module directly against a fake ``app``
(a plain namespace with just the attributes the module reads) rather than a
full Sphinx application, keeping them fast and independent of a Sphinx-Needs
build environment.

``setup`` is the module's only public name; everything these white-box tests
reach for is deliberately private, so the private-usage rule is disabled for
the whole file instead of being silenced on each of the ~20 call sites.
Access stays qualified (``coverage_report._x``) because several of these names
are rebound by ``monkeypatch``, which only works on the module attribute.
"""

# pyright: reportPrivateUsage=false

import zipfile
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment

import src.extensions.score_coverage_report as coverage_report


def _fake_app(**config_values: object) -> Sphinx:
    """A stand-in exposing only ``app.config``, which is all the module reads.

    Cast to ``Sphinx`` so call sites keep the production signature: building a
    real application just to read two config values would make these tests
    depend on a full Sphinx-Needs environment.
    """
    return cast(Sphinx, SimpleNamespace(config=SimpleNamespace(**config_values)))


def test_resolve_lcov_path_prefers_env_var_over_conf_py(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("SCORE_COVERAGE_LCOV", "/env/coverage.lcov")
    app = _fake_app(score_coverage_lcov_path="conf_py_coverage.lcov")

    result = coverage_report._resolve_lcov_path(app)

    assert result == Path("/env/coverage.lcov")


def test_resolve_lcov_path_falls_back_to_conf_py(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SCORE_COVERAGE_LCOV", raising=False)
    monkeypatch.setattr(coverage_report, "find_ws_root", lambda: None)
    app = _fake_app(score_coverage_lcov_path="conf_py_coverage.lcov")

    result = coverage_report._resolve_lcov_path(app)

    assert result == Path("conf_py_coverage.lcov")


def test_resolve_lcov_path_resolves_relative_path_against_workspace_root(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("SCORE_COVERAGE_LCOV", raising=False)
    monkeypatch.setattr(coverage_report, "find_ws_root", lambda: tmp_path)
    app = _fake_app(score_coverage_lcov_path="_build/coverage.lcov")

    result = coverage_report._resolve_lcov_path(app)

    assert result == tmp_path / "_build" / "coverage.lcov"


def test_resolve_lcov_path_defaults_to_bazel_combined_report(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("SCORE_COVERAGE_LCOV", raising=False)
    monkeypatch.setattr(coverage_report, "find_ws_root", lambda: tmp_path)
    app = _fake_app(score_coverage_lcov_path="")

    result = coverage_report._resolve_lcov_path(app)

    assert result == tmp_path / coverage_report.DEFAULT_LCOV_PATH


def test_resolve_lcov_path_prefers_coverage_report_dir(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A workspace artifact directory wins over the bazel-out symlink."""
    coverage_dir = tmp_path / coverage_report.DEFAULT_COVERAGE_DIR / "lcov_report"
    coverage_dir.mkdir(parents=True)
    tracefile = coverage_dir / "lcov.dat"
    tracefile.write_text("SF:src/logging/sink.cpp\nDA:1,1\nend_of_record\n")
    monkeypatch.delenv("SCORE_COVERAGE_LCOV", raising=False)
    monkeypatch.setattr(coverage_report, "find_ws_root", lambda: tmp_path)
    app = _fake_app(score_coverage_lcov_path="")

    assert coverage_report._resolve_lcov_path(app) == tracefile


def test_resolve_lcov_path_ignores_coverage_report_dir_without_tracefile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    coverage_dir = tmp_path / coverage_report.DEFAULT_COVERAGE_DIR / "html_report"
    coverage_dir.mkdir(parents=True)
    (coverage_dir / "index.html").write_text("<html></html>")
    monkeypatch.delenv("SCORE_COVERAGE_LCOV", raising=False)
    monkeypatch.setattr(coverage_report, "find_ws_root", lambda: tmp_path)
    app = _fake_app(score_coverage_lcov_path="")

    result = coverage_report._resolve_lcov_path(app)

    assert result == tmp_path / coverage_report.DEFAULT_LCOV_PATH


def test_resolve_lcov_path_falls_back_to_default_without_workspace_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SCORE_COVERAGE_LCOV", raising=False)
    monkeypatch.setattr(coverage_report, "find_ws_root", lambda: None)
    app = _fake_app(score_coverage_lcov_path="")

    result = coverage_report._resolve_lcov_path(app)

    assert result == Path(coverage_report.DEFAULT_LCOV_PATH)


def test_load_coverage_returns_empty_dict_for_missing_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("SCORE_COVERAGE_LCOV", raising=False)
    monkeypatch.setattr(coverage_report, "find_ws_root", lambda: None)
    app = _fake_app(score_coverage_lcov_path=str(tmp_path / "does_not_exist.lcov"))

    assert coverage_report._load_coverage(app) == {}


def test_load_coverage_reads_tracefile_from_report_archive(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """A ``bazel coverage`` report may be a ZIP despite its ``.dat`` name."""
    archive = tmp_path / "_coverage_report.dat"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("html_report/index.html", "<html></html>")
        zf.writestr(
            coverage_report.ARCHIVE_LCOV_MEMBER,
            "SF:src/logging/sink.cpp\nDA:1,1\nDA:2,0\nend_of_record\n",
        )
    monkeypatch.delenv("SCORE_COVERAGE_LCOV", raising=False)
    monkeypatch.setattr(coverage_report, "find_ws_root", lambda: None)
    app = _fake_app(score_coverage_lcov_path=str(archive))

    files = coverage_report._load_coverage(app)

    assert files["src/logging/sink.cpp"].lines_found == 2
    assert files["src/logging/sink.cpp"].lines_hit == 1


def test_load_coverage_returns_empty_dict_for_archive_without_tracefile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    archive = tmp_path / "_coverage_report.dat"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("html_report/index.html", "<html></html>")
    monkeypatch.delenv("SCORE_COVERAGE_LCOV", raising=False)
    monkeypatch.setattr(coverage_report, "find_ws_root", lambda: None)
    app = _fake_app(score_coverage_lcov_path=str(archive))

    assert coverage_report._load_coverage(app) == {}


def test_load_coverage_parses_existing_lcov_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    lcov_file = tmp_path / "coverage.lcov"
    lcov_file.write_text("SF:src/parser/reader.cpp\nDA:1,1\nend_of_record\n")
    monkeypatch.delenv("SCORE_COVERAGE_LCOV", raising=False)
    monkeypatch.setattr(coverage_report, "find_ws_root", lambda: None)
    app = _fake_app(score_coverage_lcov_path=str(lcov_file))

    files = coverage_report._load_coverage(app)

    assert "src/parser/reader.cpp" in files
    assert files["src/parser/reader.cpp"].lines_found == 1


def test_component_coverage_callable_returns_none_without_captured_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(coverage_report, "_build_environment", None)
    monkeypatch.setattr(coverage_report, "_coverage_by_file", {})
    monkeypatch.setattr(coverage_report, "_coverage_by_component", None)

    assert coverage_report._component_coverage_callable("comp__example_parser") is None


def test_component_coverage_callable_returns_none_without_declared_source_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.extensions.score_coverage_report.lcov_parser import FileCoverage

    monkeypatch.setattr(coverage_report, "_build_environment", object())
    monkeypatch.setattr(
        coverage_report,
        "_coverage_by_file",
        {
            "src/parser/reader.cpp": FileCoverage(
                path="src/parser/reader.cpp", lines_found=10, lines_hit=8
            )
        },
    )
    monkeypatch.setattr(coverage_report, "_coverage_by_component", None)
    monkeypatch.setattr(coverage_report, "_component_source_roots", lambda env: {})

    assert coverage_report._component_coverage_callable("comp__example_parser") is None


def test_component_coverage_callable_aggregates_declared_source_root(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.extensions.score_coverage_report.lcov_parser import FileCoverage

    monkeypatch.setattr(coverage_report, "_build_environment", object())
    monkeypatch.setattr(
        coverage_report,
        "_coverage_by_file",
        {
            "src/parser/reader.cpp": FileCoverage(
                path="src/parser/reader.cpp", lines_found=10, lines_hit=8
            )
        },
    )
    monkeypatch.setattr(coverage_report, "_coverage_by_component", None)
    monkeypatch.setattr(
        coverage_report,
        "_component_source_roots",
        lambda env: {"comp__example_parser": "src/parser"},
    )

    result = coverage_report._component_coverage_callable("comp__example_parser")

    assert result is not None
    assert result.component_id == "comp__example_parser"
    assert result.lines_found == 10
    assert result.lines_hit == 8


def test_invalidate_component_coverage_forces_recomputation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(coverage_report, "_coverage_by_component", {"stale": object()})

    coverage_report._invalidate_component_coverage(
        _fake_app(), cast(BuildEnvironment, object())
    )

    assert coverage_report._coverage_by_component is None


def test_parse_source_roots_reads_one_pair_per_line() -> None:
    raw = "comp__example_parser: src/parser\ncomp__example_logging: src/logging"

    assert coverage_report._parse_source_roots(raw) == {
        "comp__example_parser": "src/parser",
        "comp__example_logging": "src/logging",
    }


def test_parse_source_roots_tolerates_indentation_and_blank_lines() -> None:
    raw = "\n   comp__a: src/a\n\n  comp__b :  src/nested/deep  \n"

    assert coverage_report._parse_source_roots(raw) == {
        "comp__a": "src/a",
        "comp__b": "src/nested/deep",
    }


def test_parse_source_roots_skips_malformed_lines() -> None:
    raw = "comp__a: src/a\nsrc/no_component_id\ncomp__b:\n: src/no_id"

    assert coverage_report._parse_source_roots(raw) == {"comp__a": "src/a"}


def _env_with_needs(
    monkeypatch: pytest.MonkeyPatch, needs: dict[str, dict[str, str]]
) -> BuildEnvironment:
    monkeypatch.setattr(
        coverage_report,
        "SphinxNeedsData",
        lambda env: SimpleNamespace(get_needs_mutable=lambda: needs),
    )
    return cast(BuildEnvironment, object())


def test_component_source_roots_collects_from_mod_needs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = _env_with_needs(
        monkeypatch,
        {
            "mod__example": {
                "id": "mod__example",
                "type": "mod",
                "source_roots": (
                    "comp__example_parser: src/parser\n"
                    "comp__example_logging: src/logging"
                ),
            },
            "comp__example_parser": {"id": "comp__example_parser", "type": "comp"},
        },
    )

    assert coverage_report._component_source_roots(env) == {
        "comp__example_parser": "src/parser",
        "comp__example_logging": "src/logging",
    }


def test_component_source_roots_ignores_non_mod_needs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = _env_with_needs(
        monkeypatch,
        {
            "comp__example_parser": {
                "id": "comp__example_parser",
                "type": "comp",
                "source_roots": "comp__example_parser: src/parser",
            },
            "mod__empty": {"id": "mod__empty", "type": "mod"},
        },
    )

    assert coverage_report._component_source_roots(env) == {}


def test_component_source_roots_merges_multiple_modules(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    env = _env_with_needs(
        monkeypatch,
        {
            "mod__a": {
                "id": "mod__a",
                "type": "mod",
                "source_roots": "comp__example_parser: src/parser",
            },
            "mod__b": {
                "id": "mod__b",
                "type": "mod",
                "source_roots": "comp__example_logging: src/logging",
            },
        },
    )

    assert coverage_report._component_source_roots(env) == {
        "comp__example_parser": "src/parser",
        "comp__example_logging": "src/logging",
    }
