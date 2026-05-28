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
from sphinx_needs.logging import get_logger

RST_DIR = Path(__file__).absolute().parent / "rst"
DOCS_DIR = Path(__file__).absolute().parent.parent.parent.parent.parent

### List of relative paths of all rst files in RST_DIR


RST_FILES = [str(f.relative_to(RST_DIR)) for f in Path(RST_DIR).rglob("*.rst")]

logger = get_logger(__file__)


@pytest.fixture
def sphinx_base_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    ### Create a temporary directory for Sphinx and copy all necessary files.
    base_dir: Path = tmp_path_factory.mktemp("docs")
    shutil.copy(RST_DIR / "conf.py", base_dir)
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

            # Warning Statements
            if line.startswith("#EXPECT") or line.startswith("#EXPECT-NOT"):
                offset = parse_line_nr_in_expect_line(line)
                # If offset is not set, this is an error and should not count.
                if offset is None:
                    rst_data.syntax_errors.append(
                        f"Warning lines have to have a target warning line like `EXPECT[+1]`. Following line does not have this: \n\t{line}"
                    )
                    continue
                # Offset == 1 means that there is no newline between 'EXPECT/-NOT' and the '.. xyz'.
                # This is not allowed as this will lead to a silent parsing error and the need will not be registered
                if offset == 1:
                    rst_data.syntax_errors.append(
                        "Warning lines have '+1' as offset. There *HAS* to be a new line between Warning Statement and need."
                        "Please add a new line and increase the offset accordingly to the following line:\n\t"
                        f"{line}"
                    )
                    continue

                # Parse the Warning
                errCheck = ErrorChecks(
                    expected=line.startswith("#EXPECT["),
                    statement_line=no,
                    statement=parse_line_for_message(line),
                    offset=offset,
                    error_line=no + offset,
                )
                parsed_checks.append(errCheck)
                continue

            # See if we have any checks enabled
            if line.startswith("#CHECK:"):
                assert not rst_data.enabled_checks, "only one CHECK per file allowed"
                rst_data.enabled_checks = parse_line_for_message(line)

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
    warning_info: WarningInfo,
    warnings: list[str],
) -> list[str]:
    """
    Filtering only warnings that belong to this file & line. But also deleting the prefix.
    Filter out the filepath:linenr prefix from warning. So that the 'expect-not' can be generic
    Without having to pay attention to the filename for example 'EXPECT-NOT: test' then matching
    a random warning because 'test' is in the filename of 'graph/test_graph_checks.rst'
    """
    prefix = f"{rst_data.filename}:{warning_info.lineno}: WARNING:"
    return [warning.removeprefix(prefix) for warning in warnings if prefix in warning]


def warning_matches(
    rst_data: RstData,
    warning_info: WarningInfo,
    expected_message: str,
    warnings: list[str],
) -> str | None:
    ### Checks if any element of the warning list is includes the given warning info.
    # It returns the matched warning or None if no match is found.

    for warning in filter_warnings_by_position(rst_data, warning_info, warnings):
        if expected_message in warning:
            return warning
    return None


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from text"""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


@pytest.mark.parametrize("rst_file", RST_FILES)
def test_rst_files(
    rst_file: str,
    sphinx_app_setup: Callable[[Path], SphinxTestApp],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ### Test function to check rules in the given rst file
    # The function uses the SphinxTestApp to build the documentation
    # and checks for the expected/unexpected warnings.
    rst_data_raw, parsed_checks_raw = extract_test_data(RST_DIR / rst_file)
    if not rst_data_raw:
        raise AssertionError(
            "Unable to extract test data from the rst file: "
            f"{rst_file}. Please check the file for the correct format."
        )
    rst_data = group_test_data(rst_data_raw, parsed_checks_raw)

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
    app.config.score_metamodel_checks = rst_data.enabled_checks
    app.build()

    # Collect the warnings

    # ╓                                                          ╖
    # ║ Enable this if you need to see errors for debugging      ║
    # ║ purposes                                                 ║
    # ╙                                                          ╜
    raw_warnings = app.warning.getvalue().splitlines()
    warnings = [strip_ansi_codes(w) for w in raw_warnings]

    # Enable this if you need to see errors for debugging purposes
    # print(
    #     "\n".join(strip_ansi_codes(w) for w warnings
    # )

    # Check if the expected warnings are present
    for warning_info in rst_data.warning_infos:
        for check in warning_info.warnings:
            if check.expected:
                if not warning_matches(
                    rst_data, warning_info, check.statement, warnings
                ):
                    actual = filter_warnings_by_position(
                        rst_data, warning_info, warnings
                    )
                    loc = f"{rst_data.filename}:{warning_info.lineno}"
                    msg = f"{loc} Expected warning not found:\n"
                    msg += f"  Expected: '{check.statement}'\n"
                    msg += "  Actual:\n"
                    for a in actual:
                        msg += f"    - {a}\n"
                    pytest.fail(msg, pytrace=False)
            else:
                if unexpected := warning_matches(
                    rst_data, warning_info, check.statement, warnings
                ):
                    loc = f"{rst_data.filename}:{warning_info.lineno}"
                    msg = f"{loc} Unexpected warning found:\n"
                    msg += f"  Not Expected: '{check.statement}'\n"
                    msg += f"  Actual: '{unexpected}'\n"
                    pytest.fail(msg, pytrace=False)
