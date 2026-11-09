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
import sys
from collections.abc import Callable, Collection
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import pytest
from score_metamodel.tests import need as test_need
from score_pytest.attribute_plugin import add_test_properties, apply_test_metadata
from sphinx.testing.util import SphinxTestApp
from sphinx_needs.data import NeedsExtendType, SphinxNeedsData
from sphinx_needs.need_item import NeedItem
from sphinx_needs.needs_schema import FieldLiteralValue
from sphinx_needs.views import NeedsView

RST_DIR = Path(__file__).absolute().parent / "rst"

# Relative paths of all rst files in RST_DIR
RST_FILES = [str(f.relative_to(RST_DIR)) for f in Path(RST_DIR).rglob("*.rst")]
_NEED_DIRECTIVE_PATTERN = re.compile(r"^\s*\.\.\s+([A-Za-z][\w-]*)::")


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


def count_need_objects(rst_file: Path, need_directives: Collection[str]) -> RstData:
    rst_data = RstData(filename=str(rst_file.relative_to(RST_DIR)))
    need_directive_names = set(need_directives) | {"needextend"}
    with open(rst_file) as f:
        for no, line in enumerate(f, start=1):
            # Nested Needs are indented below their containing Need. Parse the
            # directive name so nested notes, code blocks, and other ordinary
            # reStructuredText directives are not mistaken for Needs.
            match = _NEED_DIRECTIVE_PATTERN.match(line)
            if match and match.group(1) in need_directive_names:
                rst_data.found_objects.append(no)
    return rst_data


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
def test_count_need_objects_ignores_nested_non_need_directives(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Only configured Need directives count, including an explicit needextend."""
    monkeypatch.setattr(sys.modules[__name__], "RST_DIR", tmp_path)
    rst_file = tmp_path / "nested.rst"
    rst_file.write_text(
        """.. stkh_req:: Parent
   :id: stkh_req__parent

   .. note::
      This ordinary directive must not be counted.

   .. code-block:: text

      This ordinary directive must not be counted either.

.. needextend:: stkh_req__parent
""",
        encoding="utf-8",
    )

    rst_data = count_need_objects(rst_file, {"stkh_req"})

    assert rst_data.found_objects == [1, 11]


def filter_messages_by_position(
    rst_data: RstData,
    line_nr: int,
    messages: list[str],
    level: str = "WARNING",
) -> list[str]:
    """Select diagnostics for this need and strip the location and severity.

    Sphinx emits info messages without a severity prefix. Matching the need's
    location keeps expectations from matching diagnostics for another need.
    """
    severity = f" {level}:" if level else ""
    prefix = f"{rst_data.filename}:{line_nr}:{severity}"
    return [message.removeprefix(prefix) for message in messages if prefix in message]


def message_matches(
    rst_data: RstData,
    line_nr: int,
    expected_message: str,
    messages: list[str],
    level: str = "WARNING",
) -> str | None:
    """Return a matching diagnostic at the need's location, if present."""
    for message in filter_messages_by_position(rst_data, line_nr, messages, level):
        if expected_message in message:
            return message
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


def _get_test_metadata_need(needs_view: NeedsView, rst_data: RstData) -> NeedItem:
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


def _get_expectations(need: NeedItem | NeedsExtendType, option_name: str) -> list[str]:
    """Get test warning annotations from a need or needextend directive."""
    if isinstance(need, NeedItem):
        return cast("list[str]", need.get(option_name) or [])

    for name, _, value in need["modifications"]:
        if name == option_name and isinstance(value, FieldLiteralValue):
            return cast("list[str]", value.value or [])
    return []


def _check_need_messages(
    rst_data: RstData,
    need: NeedItem | NeedsExtendType,
    messages: list[str],
    *,
    info: bool = False,
) -> None:
    """Check location-scoped expectations in the warning or info stream."""
    level = "" if info else "WARNING"
    label = "info" if info else "warning"
    expected_option = "expect_info" if info else "expect"
    unexpected_option = "expect_info_not" if info else "expect_not"
    # needextend-affected needs (those with 'modifications') are skipped here;
    # their expectations are checked on the extending need itself.
    if need.get("modifications"):
        return

    line_nr = need.get("lineno")

    for raw in _get_expectations(need, expected_option):
        expected = raw.strip()
        if message_matches(rst_data, line_nr, expected, messages, level):
            continue
        actual = filter_messages_by_position(rst_data, line_nr, messages, level)
        actual_block = "".join(f"    - {a}\n" for a in actual)
        pytest.fail(
            f"{rst_data.filename}:{line_nr} Expected {label} not found:\n"
            f" Expected {label} in line: '{line_nr}'\n"
            f" Expected {label} string: '{expected}'\n"
            f"  Actual {label}:\n{actual_block}",
            pytrace=False,
        )

    for raw in _get_expectations(need, unexpected_option):
        not_expected = raw.strip()
        unexpected = message_matches(rst_data, line_nr, not_expected, messages, level)
        if not unexpected:
            continue
        pytest.fail(
            f"{rst_data.filename}:{line_nr} Unexpected {label} found:\n"
            f"  Not expected {label} found on line'{line_nr}'\n"
            f"  {label.capitalize()} text NOT expected:  '{not_expected}'\n"
            f"  Actual: '{unexpected}'\n",
            pytrace=False,
        )


@add_test_properties(
    partially_verifies=[],
    test_type="interface-test",
    derivation_technique="explorative-testing",
)
@pytest.mark.parametrize("rst_file", RST_FILES)
def test_rst_files(
    record_property: Callable[[str, object], None],
    record_xml_attribute: Callable[[str, str], None],
    rst_file: str,
    sphinx_app_setup: Callable[[Path], SphinxTestApp],
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    """Build each RST test fixture and validate its warnings and Needs."""
    ### Build the given rst file with Sphinx and check expected/unexpected warnings.
    # Build the documentation
    app = sphinx_app_setup(RST_DIR / rst_file)
    monkeypatch.chdir(app.srcdir)  # Sphinx resolves paths relative to the source dir
    app.build()

    need_directives = {
        str(need_type["directive"]) for need_type in app.config.needs_types
    }
    rst_data = count_need_objects(RST_DIR / rst_file, need_directives)

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
    infos = [strip_ansi_codes(line) for line in app.status.getvalue().splitlines()]
    for need in all_needs:
        _check_need_messages(rst_data, need, warnings)
        _check_need_messages(rst_data, need, infos, info=True)
