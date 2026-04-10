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
from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

import pytest

# Type aliases for better readability
TestFunction = Callable[..., Any]
Decorator = Callable[[TestFunction], TestFunction]


def add_test_properties(
    *,
    partially_verifies: list[str] | None = None,
    fully_verifies: list[str] | None = None,
    test_type: Literal[
        "fault-injection", "interface-test", "requirements-based", "resource-usage"
    ],
    derivation_technique: Literal[
        "requirements-analysis",
        "design-analysis",
        "boundary-values",
        "equivalence-classes",
        "fuzz-testing",
        "error-guessing",
        "explorative-testing",
    ],
) -> Decorator:
    """
    Decorator to add user properties, file and lineNr to testcases in the XML output
    """
    # Early error handling
    if partially_verifies is None and fully_verifies is None:
        raise ValueError(
            "Either 'partially_verifies' or 'fully_verifies' must be provided."
        )

    #          ╭──────────────────────────────────────╮
    #          │  HINT. This is currently commented   │
    #          │ out to not restrict usage a lot but  │
    #          │   will be commented back in in the   │
    #          │                future                │
    #          ╰──────────────────────────────────────╯

    # if not test_type:
    #     raise ValueError("'test_type' is required and cannot be empty.")
    #
    # if not derivation_technique:
    #     raise ValueError("'derivation_technique' is required and cannot be empty.")
    #

    def decorator(func: TestFunction) -> TestFunction:
        # Clean properties (skip None)
        properties = {
            "PartiallyVerifies": ", ".join(partially_verifies)
            if partially_verifies
            else "",
            "FullyVerifies": ", ".join(fully_verifies) if fully_verifies else "",
            "TestType": test_type,
            "DerivationTechnique": derivation_technique,
        }
        # Ensure a 'description' is there inside the Docstring
        if not func.__doc__ or not func.__doc__.strip():
            raise ValueError(
                f"{func.__name__} does not have a description. "
                + "Descriptions (in docstrings) are mandatory."
            )
        # NOTE: This might come back to bite us in some weird edgecase, though I have not thought of one so far
        # Remove keys with 'falsey' values
        cleaned_properties = {k: v for k, v in properties.items() if v}
        return pytest.mark.test_properties(cleaned_properties)(func)

    return decorator


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    """Attach file and line info to the report for use in junitxml output."""

    outcome = yield
    report = outcome.get_result()

    if report.when != "call":
        return
    # Since our decorator 'add_test_properties' will create a 'test_properties' marker
    # This function then searches for the nearest dictionary attached to an item with
    # that marker and parses this into properties.

    # In short:
    #   => This function adds the properties specified via the decorator to the item so
    #      they can be written to the XML output in the end
    # Note: This does NOT add 'line' and 'file' to the testcase.

    marker = item.get_closest_marker("test_properties")
    if not marker:
        return

    if not marker.args:
        raise ValueError(
            f"Marker 'test_properties' on {item.name} does not have any arguments. "
            + "Please ensure that the 'add_test_properties' decorator is used correctly."
        )

    if isinstance(marker.args[0], dict):
        for k, v in marker.args[0].items():
            item.user_properties.append((k, str(v)))


@pytest.fixture(autouse=True)
def add_file_and_line_attr(
    record_xml_attribute: Callable[[str, str], None], request: pytest.FixtureRequest
) -> None:
    """Adding line & file to the <testcase> attribute in the XML"""
    node = request.node
    raw_file_path, line_number, _ = node.location

    # turning `../../../_main/<file_path>` into => <filepath>
    clean_file_path = raw_file_path.split("_main/")[-1]
    record_xml_attribute("file", str(clean_file_path))
    # Convert pytest's 0-based source line number to 1-based numbering for XML output.
    record_xml_attribute("line", str(line_number + 1))
