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

import re
import shutil
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest
from score_metamodel.tests import need as test_need
from sphinx.testing.util import SphinxTestApp
from sphinx_needs.data import NeedsExtendType, SphinxNeedsData
from sphinx_needs.need_item import NeedItem

from score_pytest.attribute_plugin import apply_test_metadata

RST_DIR = Path(__file__).absolute().parent / "rst"

# Relative paths of all rst files in RST_DIR
RST_FILES = [str(f.relative_to(RST_DIR)) for f in Path(RST_DIR).rglob("*.rst")]


@pytest.fixture
def sphinx_base_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    ### Create a temporary directory for Sphinx and copy all necessary files.
    base_dir: Path = tmp_path_factory.mktemp("docs")
    shutil.copy(RST_DIR / "conf.py", base_dir)
    shutil.copy(RST_DIR / "needs.json", base_dir)
    return base_dir


@pytest.fixture
def index_file() -> Callable[[Path], str]:
    ### Returns a function that creates an index.rst file.
    def _create_rst_file(rst_file: Path) -> str:
        ### returns an index.rst file with a toctree
        # that refers to the given rst file.
        index_rst: str = f"""
.. toctree::
   {rst_file.relative_to(RST_DIR)}
"""
        return index_rst

    return _create_rst_file


@pytest.fixture
def sphinx_app_setup(
    sphinx_base_dir: Path, index_file: Callable[[Path], str]
) -> Callable[[Path], SphinxTestApp]:
    ### Returns a function that creates a SphinxTestApp instance.
    def _create_app(rst_file: Path) -> SphinxTestApp:
        ### Create a SphinxTestApp instance.
        # The source directory is set to the temporary directory.
        # Create folder structure of rst file in the temporary directory.
        rst_folder = sphinx_base_dir / rst_file.parent.relative_to(RST_DIR)
        rst_folder.mkdir(parents=True, exist_ok=True)
        # Copy the rst file to the temporary directory.
        shutil.copy(str(rst_file), rst_folder)
        index_context: str = index_file(rst_file)
        (sphinx_base_dir / "index.rst").write_text(index_context)
        app: SphinxTestApp = SphinxTestApp(
            freshenv=True,
            srcdir=sphinx_base_dir,
            outdir=sphinx_base_dir / "out",
            buildername="html",
        )
        return app

    return _create_app


@dataclass
class RstData:
    #### Holds filename, all infos about warnings and
    # which checks to enable if not all
    filename: str
    enabled_checks: str = ""
    found_objects: list[int] = field(default_factory=list)
    metadata: dict[str, list[str] | str] = field(default_factory=dict)


def count_need_objects(rst_file: Path) -> RstData:
    rst_data = RstData(filename=str(rst_file.relative_to(RST_DIR)))
    with open(rst_file) as f:
        for no, line in enumerate(f, start=1):
            # Beginning of new need
            # We filter for '::' as well so we ONLY get directives not comments
            if line.startswith(".. ") and "::" in line:
                rst_data.found_objects.append(no)
    return rst_data


def filter_warnings_by_position(
    rst_data: RstData,
    line_nr: int,
    warnings: list[str],
) -> list[str]:
    """
    Filtering only warnings that belong to this file & line. But also deleting the prefix.
    Filter out the filepath:linenr prefix from warning. So that the 'expect-not' can be generic
    Without having to pay attention to the filename for example 'EXPECT-NOT: test' then matching
    a random warning because 'test' is in the filename of 'graph/test_graph_checks.rst'
    """
    prefix = f"{rst_data.filename}:{line_nr}: WARNING:"
    return [warning.removeprefix(prefix) for warning in warnings if prefix in warning]


def warning_matches(
    rst_data: RstData,
    line_nr: int,
    expected_message: str,
    warnings: list[str],
) -> str | None:
    ### Checks if any element of the warning list includes the given warning info.
    # It returns the matched warning or None if no match is found.
    for warning in filter_warnings_by_position(rst_data, line_nr, warnings):
        if expected_message in warning:
            return warning
    return None


def _clean_list(values: list[str] | None) -> list[str]:
    ### Strip whitespace and drop empty entries from a possibly-None list.
    return [item.strip() for item in (values or []) if item.strip()]


def parse_test_metadata(need: NeedItem) -> dict[str, Any]:
    metadata: dict[str, Any] = {
        "fully_verifies": _clean_list(need.get("fully_verifies_list")),
        "partially_verifies": _clean_list(need.get("partially_verifies_list")),
        "test_type": need.get("test_type"),
        "line_nr": need.get("lineno"),
        "file": need.get("docname"),
        "derivation_technique": need.get("derivation_technique"),
        "description": need.get("content"),
        "check": need.get("check"),
    }
    return metadata


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from text"""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


def clean_filepath(request: pytest.FixtureRequest) -> str:
    """
    Request Path:
        <bazel sandbox path>/file_based_tests_options.runfiles/_main/src/extensions/score_metamodel/tests/test_rules_file_based.py
    Output:
        src/extensions/score_metamodel/tests/rst/
    """
    return str(request.path.parent).rsplit("_main")[-1].removeprefix("/") + "/rst/"


def _validate_need_count(
    needs: list[NeedItem | NeedsExtendType], rst_data: RstData
) -> None:
    ### Fail if Sphinx and our own parser disagree on the number of needs.
    if len(needs) == len(rst_data.found_objects):
        return
    pytest.fail(
        "Sphinx parsed needs and our own parser disagree on the number of needs. "
        f"Please double check the document: {rst_data.filename}\n"
        f"Sphinx Parsed Needs: {len(needs)} | Own Parser Needs: {len(rst_data.found_objects)}\n"
        f"We have found need objects at lines: {rst_data.found_objects} ",
        pytrace=False,
    )


def _get_default_metadata_need() -> NeedItem:
    return test_need(
        fully_verifies=[],
        partially_verifies=[],
        test_type="",
        line_nr="",
        file="",
        derivation_technique="",
        description="",
    )


def _get_test_metadata_need(needs_view, rst_data: RstData) -> NeedItem:
    ### Return the single 'test_metadata' need, failing if there isn't exactly one.
    test_metadata_needs = needs_view.filter_types(["test_metadata"]).values()
    if not test_metadata_needs:
        return _get_default_metadata_need()
    if len(test_metadata_needs) > 1:
        pytest.fail(
            f"Error in file: {rst_data.filename}. "
            "Only '1' test_metadata need is allowed per RST file.",
            pytrace=False,
        )
    return next(iter(test_metadata_needs))


def _collect_warnings(app: SphinxTestApp) -> list[str]:
    ### Return cleaned build warnings, failing fast on unknown-option errors.
    # Some warnings are suppressed in conf.py, so the set here is already limited.
    warnings = [strip_ansi_codes(w) for w in app.warning.getvalue().splitlines()]
    unknown_option = [w for w in warnings if "unknown option" in w.lower()]
    if unknown_option:
        pytest.fail(
            "Error in RST. Unknown options specified. Errors:\n"
            + "\n".join(unknown_option),
            pytrace=False,
        )
    return warnings


def _check_need_warnings(
    rst_data: RstData, need: NeedItem | NeedsExtendType, warnings: list[str]
) -> None:
    ### Verify a need's 'expect' / 'expect_not' annotations against the warnings.
    # needextend-affected needs (those with 'modifications') are skipped here;
    # their expectations are checked on the extending need itself.
    if need.get("modifications"):
        return

    line_nr = need.get("lineno")

    for raw in need.get("expect") or []:
        expected = raw.strip()
        if warning_matches(rst_data, line_nr, expected, warnings):
            continue
        actual = filter_warnings_by_position(rst_data, line_nr, warnings)
        actual_block = "".join(f"    - {a}\n" for a in actual)
        pytest.fail(
            f"{rst_data.filename}:{line_nr} Expected warning not found:\n"
            f" Expected warning in line: '{line_nr}'\n"
            f" Expected warning string: '{expected}'\n"
            f"  Actual warning:\n{actual_block}",
            pytrace=False,
        )

    for raw in need.get("expect_not") or []:
        not_expected = raw.strip()
        unexpected = warning_matches(rst_data, line_nr, not_expected, warnings)
        if not unexpected:
            continue
        pytest.fail(
            f"{rst_data.filename}:{line_nr} Unexpected warning found:\n"
            f"  Not expected warning found on line'{line_nr}'\n"
            f"  Warning Text NOT expected:  '{not_expected}'\n"
            f"  Actual: '{unexpected}'\n",
            pytrace=False,
        )


@pytest.mark.parametrize("rst_file", RST_FILES)
def test_rst_files(
    record_property,
    record_xml_attribute,
    rst_file: str,
    sphinx_app_setup: Callable[[Path], SphinxTestApp],
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    ### Build the given rst file with Sphinx and check expected/unexpected warnings.
    rst_data = count_need_objects(RST_DIR / rst_file)

    # Build the documentation
    app = sphinx_app_setup(RST_DIR / rst_file)
    monkeypatch.chdir(app.srcdir)  # Sphinx resolves paths relative to the source dir
    app.build()

    # Get & parse metadata needs
    needs_data = SphinxNeedsData(app.env)
    needs_view = needs_data.get_needs_view()
    extends = needs_data.get_or_create_extends().values()
    all_needs = list(needs_view.values()) + list(extends)
    _validate_need_count(all_needs, rst_data)

    metadata_need = _get_test_metadata_need(needs_view, rst_data)
    rst_data.metadata = parse_test_metadata(metadata_need)
    line_nr = int(str(rst_data.metadata["line_nr"]))
    file_name = (
        clean_filepath(request) + str(rst_data.metadata["file"]) + ".rst"
        if rst_data.metadata["file"]
        else ""
    )
    apply_test_metadata(
        record_property=record_property,
        metadata=rst_data.metadata,
        record_xml_attribute=record_xml_attribute,
        file=file_name,
        line=line_nr,
    )

    # Collect warnings and verify each need's expectations
    warnings = _collect_warnings(app)
    for need in all_needs:
        _check_need_warnings(rst_data, need, warnings)
