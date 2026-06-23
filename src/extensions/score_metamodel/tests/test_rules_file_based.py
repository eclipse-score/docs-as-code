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

import pytest
from sphinx.testing.util import SphinxTestApp
from sphinx_needs.data import SphinxNeedsData
from sphinx_needs.data import NeedsExtendType
from sphinx_needs.need_item import NeedItem
from score_pytest.attribute_plugin import _build_test_properties

RST_DIR = Path(__file__).absolute().parent / "rst"

### List of relative paths of all rst files in RST_DIR
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
class ErrorChecks:
    """
    Represents one EXPECT or EXPECT-NOT statement parsed from an rst test file.

    Attributes:
        expected: True if this is EXPECT, False if EXPECT-NOT.
        statement_line: Absolute source line where EXPECT / EXPECT-NOT is declared.
        statement: Message text after the ':' part.
        offset: Parsed integer from '[+x]'.
        error_line: Computed target line number (statement_line + offset).
    """

    expected: bool
    statement_line: int
    statement: str
    offset: int
    error_line: int


@dataclass
class WarningInfo:
    #### Class to hold information about warnings
    # Contains the line number and the expected and not expected warnings.
    lineno: int = 0
    warnings: list[ErrorChecks] = field(default_factory=list)


@dataclass
class RstData:
    #### Holds filename, all infos about warnings and
    # which checks to enable if not all
    filename: str
    enabled_checks: str = ""
    warning_infos: list[WarningInfo] = field(default_factory=list)
    found_objects: list[int] = field(default_factory=list)
    syntax_errors: list[str] = field(default_factory=list)
    metadata: dict[str, list[str] | str] = field(default_factory=dict)


def parse_line_for_message(line: str) -> str:
    #### Extract the warning message from the line
    # The line format is "#EXPECT: <warning message>"
    # or "#EXPECT-NOT: <warning message>"
    # or "#CHECK: <checks>"
    return line.split(": ", 1)[1].strip()


def parse_line_nr_in_expect_line(text: str) -> int | None:
    match = re.search(r"\[(\+\d+)\]", text)
    if match is None:
        return None
    return int(match.group(1).removeprefix("+"))


import re, yaml


def extract_test_data(rst_file: Path) -> tuple[RstData, list[ErrorChecks]]:
    ### Extract test data from the given rst file
    # The function returns a list of WarningInfo objects
    # containing the line number and the expected and not expected warnings.
    # If no test data is found, it returns None.
    rst_data = RstData(filename=str(rst_file.relative_to(RST_DIR)))
    parsed_checks: list[ErrorChecks] = []
    with open(rst_file) as f:
        for no, line in enumerate(f, start=1):
            # Beginning of new need
            # We filter for '::' as well so we ONLY get directives not comments
            if line.startswith(".. ") and "::" in line:
                rst_data.found_objects.append(no)
                continue
            # # Warning Statements
            # if line.startswith("#EXPECT") or line.startswith("#EXPECT-NOT"):
            #     offset = parse_line_nr_in_expect_line(line)
            #     # If offset is not set, this is an error and should not count.
            #     if offset is None:
            #         rst_data.syntax_errors.append(
            #             f"Warning lines have to have a target warning line like `EXPECT[+1]`. Following line does not have this: \n\t{line}"
            #         )
            #         continue
            #     # Offset == 1 means that there is no newline between 'EXPECT/-NOT' and the '.. xyz'.
            #     # This is not allowed as this will lead to a silent parsing error and the need will not be registered
            #     if offset == 1:
            #         rst_data.syntax_errors.append(
            #             "Warning lines have '+1' as offset. There *HAS* to be a new line between Warning Statement and need. "
            #             "Please add a new line and increase the offset accordingly to the following line:\n\t"
            #             f"{line}"
            #         )
            #         continue
            #
            #     # Parse the Warning
            #     errCheck = ErrorChecks(
            #         expected=line.startswith("#EXPECT["),
            #         statement_line=no,
            #         statement=parse_line_for_message(line),
            #         offset=offset,
            #         error_line=no + offset,
            #     )
            #     parsed_checks.append(errCheck)
            #     continue
            #
            # # See if we have any checks enabled
            # if line.startswith("#CHECK:"):
            #     assert not rst_data.enabled_checks, "only one CHECK per file allowed"
            #     rst_data.enabled_checks = parse_line_for_message(line)

    return rst_data, parsed_checks


def group_test_data(rst_data: RstData, parsed_checks: list[ErrorChecks]) -> RstData:
    """
    Take parsed data from the file and group it together with parsed checks.
    Groups the corresponding error_lines with the need lines as well as doing
    some checks (is the error_line that the Warning Statement refers to actually there) etc.
    """
    # We now evaluate all of the warnings and group them
    # We do this to avoid re-iteration over all warnings twice.
    grouped: dict[int, WarningInfo] = {}
    for check in parsed_checks:
        # Lookup if the offsets are correct
        if check.error_line not in rst_data.found_objects:
            rst_data.syntax_errors.append(
                "Warning Statement offset does not point to a need/object line. "
                f"Statement Line {check.statement_line} -> target line {check.error_line}:\n\t"
                "Warning Statement\n\t"
                f"{check.statement}"
            )
            continue
        # We want one `WarningInfo` per 'need' or 'Error Line'.
        # If there is one for the current error_line then append it
        # Otherwise create it and put it into the outside group
        info = grouped.get(check.error_line)
        if info is None:
            info = WarningInfo(lineno=check.error_line)
            grouped[check.error_line] = info
        info.warnings.append(check)

    # Just sorting the data in deterministic way for future things
    rst_data.warning_infos = [grouped[k] for k in sorted(grouped)]
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
    ### Checks if any element of the warning list is includes the given warning info.
    # It returns the matched warning or None if no match is found.

    for warning in filter_warnings_by_position(rst_data, line_nr, warnings):
        if expected_message in warning:
            return warning
    return None


def parse_test_metadata(need: NeedItem) -> dict[str, list[str] | str]:
    metadata = {}
    
    metadata["fully_verifies"] = [item.strip() for item in need.get("fully_verifies_list").split(",") if item.strip()]
    metadata["partially_verifies"] = [item.strip() for item in need.get("partially_verifies_list").split(",") if item.strip()]
    metadata["test_type"] = need.get("test_type")
    metadata["derivation_technique"] = need.get("derivation_technique")
    metadata["description"] = need.get("content")
    metadata["check"] = need.get("check")
    assert metadata["fully_verifies"] or metadata["partially_verifies"], (
        f"Error in need: {need.get('id')}. Either fully_verifies or partially_verifies must be provided"
    )
    return metadata


def apply_test_metadata_props(
    *,
    record_property,
    record_xml_attribute=None,
    metadata: dict,
    file: str | None = None,
    line: int | None = None,
) -> None:
    if not metadata:  # files without a test-metadata block: nothing to attach
        return
    props = _build_test_properties(
        partially_verifies=metadata.get("partially_verifies"),
        fully_verifies=metadata.get("fully_verifies"),
        test_type=metadata["test_type"],
        derivation_technique=metadata["derivation_technique"],
    )
    for k, v in props.items():
        record_property(k, v)
    if record_xml_attribute is not None and file is not None:
        record_xml_attribute("file", file)
    if record_xml_attribute is not None and line is not None:
        record_xml_attribute("line", str(line))


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from text"""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


@pytest.mark.parametrize("rst_file", RST_FILES)
def test_rst_files(
    record_property,
    record_xml_attribute,
    rst_file: str,
    sphinx_app_setup: Callable[[Path], SphinxTestApp],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ### Test function to check rules in the given rst file
    # The function uses the SphinxTestApp to build the documentation
    # and checks for the expected/unexpected warnings.
    rst_data, parsed_checks_raw = extract_test_data(RST_DIR / rst_file)
    # rst_data = group_test_data(rst_data_raw, parsed_checks_raw)

    # ╓                                                          ╖
    # ║ Will be activated once 'architecture_check.rst' is fixed ║
    # ╙                                                          ╜

    # if not rst_data.warning_infos:
    #     raise AssertionError(
    #         "Could not find any Warning Statements (EXPECT/-NOT) in rst file: "
    #         f"{rst_file}. Please check the file for the correct format."
    #     )

    # We can check if we have any of our own parsing errors
    # before we even build the sphinx app and check sphinx errors
    if rst_data.syntax_errors:
        pytest.fail("\n".join(rst_data.syntax_errors), pytrace=False)

    #              ╭──────────────────────────────────────────────────────────╮
    #              │             Actual Sphinx RST Test Execution             │
    #              ╰──────────────────────────────────────────────────────────╯

    app: SphinxTestApp = sphinx_app_setup(RST_DIR / rst_file)
    monkeypatch.chdir(app.srcdir)  # Change working directory to the source directory

    # Build the documentation with the enabled checks

    app.build()

    #            ────────────────────[ Get & parse metadata needs ]──────────────────

    needs_all_needs = SphinxNeedsData(app.env).get_needs_view()
    extends = SphinxNeedsData(app.env).get_or_create_extends().values()
    needs_all_needs_list = list(needs_all_needs.values()) + list(extends)
    # if len(needs_all_needs) != len(rst_data.found_objects):
    #     pytest.fail(
    #         "Sphinx parsed needs and our own parser disagree on the number of needs. "
    #         f"Please double check the document: {rst_data.filename}\n"
    #         f"Sphinx Parsed Needs: {len(needs_all_needs)} | Own Parser Needs: {len(rst_data.found_objects)} "
    #         f"We have found need objects at lines: {rst_data.found_objects} ",
    #         pytrace=False,
    #     )
    test_metadata_need = needs_all_needs.filter_types(["test_metadata"]).values()
    # if len(test_metadata_need) != 1:
    #     pytest.fail(
    #         f"Error in file: {rst_data.filename}. Only '1' test_metadata need is allowed per RST file.",
    #         pytrace=False,
    #     )
    rst_data.enabled_checks = list(test_metadata_need)[0].get("CHECK")
    app.config.score_metamodel_checks = (
        rst_data.enabled_checks if rst_data.enabled_checks is not None else ""
    )
    rst_data.metadata = parse_test_metadata(list(test_metadata_need)[0])
    apply_test_metadata_props(
        record_property=record_property,
        record_xml_attribute=record_xml_attribute,
        metadata=rst_data.metadata,
        file=rst_data.filename,  # optional: point <testcase> at the .rst, not the .py
    )

    # Collect the warnings

    # ╓                                                          ╖
    # ║ Enable this if you need to see errors for debugging      ║
    # ║ purposes                                                 ║
    # ╙                                                          ╜
    raw_warnings = app.warning.getvalue().splitlines()
    # We have some warnings supressed (in conf.py) therefore we are already
    # limiting the warnings that could be published here.
    # We do not want to limit the warnings outright as that will make debugging harder
    warnings = [strip_ansi_codes(w) for w in raw_warnings]

    # Enable this if you need to see errors for debugging purposes
    # print("\n".join(w for w in warnings))

    # Check if the expected warnings are present
    for need in needs_all_needs_list:
        if need.get("expect") and not need.get("modifications"):
            expected_warnings_raw = need.get("expect")
            line_nr = need.get("lineno")
            expected_warnings = expected_warnings_raw.split(",")
            for expected_warning_raw in expected_warnings:
                expected_warning = expected_warning_raw.strip()
                if not warning_matches(rst_data, line_nr, expected_warning, warnings):
                    actual = filter_warnings_by_position(rst_data, line_nr, warnings)
                    loc = f"{rst_data.filename}:{line_nr}"
                    msg = f"{loc} Expected warning not found:\n"
                    msg += f" Expected warning in line: '{line_nr}'\n"
                    msg += f"  Expected warning string: '{expected_warning}'\n"
                    msg += "  Actual warning:\n"
                    for a in actual:
                        msg += f"    - {a}\n"
                    pytest.fail(msg, pytrace=False)
        if need.get("expect_not") and not need.get("modifications"):
            non_expected_warnings_raw = need.get("expect_not")
            line_nr = need.get("lineno")
            non_expected_warnings = non_expected_warnings_raw.split(",")
            for not_expected_warning_raw in non_expected_warnings:
                not_expected_warning = not_expected_warning_raw.strip()
                if unexpected := warning_matches(
                    rst_data, line_nr, not_expected_warning, warnings
                ):
                    loc = f"{rst_data.filename}:{line_nr}"
                    msg = f"{loc} Unexpected warning found:\n"
                    msg += f"  Not expected warning found on line'{line_nr}'\n"
                    msg += f"  Warning Text NOT expected:  '{not_expected_warning}'\n"
                    msg += f"  Actual: '{unexpected}'\n"
                    pytest.fail(msg, pytrace=False)

    # pytest.fail(print("\n".join(strip_ansi_codes(w) for w in warnings)),pytrace=False)
