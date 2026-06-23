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

# Shared value types, used by both the decorator and the runtime applier
TestType = Literal[
    "fault-injection", "interface-test", "requirements-based", "resource-usage"
]
DerivationTechnique = Literal[
    "requirements-analysis",
    "design-analysis",
    "boundary-values",
    "equivalence-classes",
    "fuzz-testing",
    "error-guessing",
    "explorative-testing",
]


def _build_test_properties(
    *,
    partially_verifies: list[str] | None,
    fully_verifies: list[str] | None,
    test_type: TestType,
    derivation_technique: DerivationTechnique,
) -> dict[str, str]:
    """
    Build the cleaned property mapping that ends up in the XML.

    Single source of truth shared by the `add_test_properties` decorator
    (definition-time, for Python tests) and `apply_test_metadata`
    (runtime, for parameterized / RST-driven tests).
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

    properties = {
        "PartiallyVerifies": ", ".join(partially_verifies)
        if partially_verifies
        else "",
        "FullyVerifies": ", ".join(fully_verifies) if fully_verifies else "",
        "TestType": test_type,
        "DerivationTechnique": derivation_technique,
    }
    # NOTE: This might come back to bite us in some weird edgecase, though I have not thought of one so far
    # Remove keys with 'falsey' values
    return {k: v for k, v in properties.items() if v}


def add_test_properties(
    *,
    partially_verifies: list[str] | None = None,
    fully_verifies: list[str] | None = None,
    test_type: TestType,
    derivation_technique: DerivationTechnique,
) -> Decorator:
    """
    Decorator to add user properties, file and lineNr to testcases in the XML output
    """

    def decorator(func: TestFunction) -> TestFunction:
        cleaned_properties = _build_test_properties(
            partially_verifies=partially_verifies,
            fully_verifies=fully_verifies,
            test_type=test_type,
            derivation_technique=derivation_technique,
        )
        # Ensure a 'description' is there inside the Docstring
        if not func.__doc__ or not func.__doc__.strip():
            raise ValueError(
                f"{func.__name__} does not have a description. "
                + "Descriptions (in docstrings) are mandatory."
            )
        return pytest.mark.test_properties(cleaned_properties)(func)

    return decorator


def apply_test_metadata(
    *,
    record_property: Callable[[str, str], None],
    metadata: dict[str, list[str] | str],
    record_xml_attribute: Callable[[str, str], None] | None = None,
    file: str | None = None,
    line: int | None = None,
) -> None:
    """
    Runtime equivalent of `add_test_properties` for tests where the metadata is
    only known inside the test body (e.g. parameterized RST integration tests).

    Call this *early* in the test (before any assertion / pytest.fail) so the
    properties are attached to the XML even when the test fails.

    `metadata` is the dict parsed from the RST `test-metadata` block and is
    expected to carry the same keys as the decorator arguments.
    """
    if not metadata:  # no test-metadata block present: nothing to attach
        return

    cleaned_properties = _build_test_properties(
        partially_verifies=metadata.get("partially_verifies"),  # type: ignore[arg-type]
        fully_verifies=metadata.get("fully_verifies"),  # type: ignore[arg-type]
        test_type=metadata["test_type"],  # type: ignore[arg-type]
        derivation_technique=metadata["derivation_technique"],  # type: ignore[arg-type]
    )
    for key, value in cleaned_properties.items():
        record_property(key, value)

    # Optional: override the <testcase> file/line (otherwise the autouse
    # fixture below points them at the .py test location).
    if record_xml_attribute is not None and file is not None:
        record_xml_attribute("file", file)
    if record_xml_attribute is not None and line is not None:
        record_xml_attribute("line", str(line))


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo[None]):
    """Attach file and line info to the report for use in junitxml output."""

    outcome = yield  # pyright: ignore[reportUnknownVariableType]
    report = outcome.get_result()  # pyright: ignore[reportUnknownVariableType]

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
        for k, v in marker.args[0].items():  # pyright: ignore[reportUnknownVariableType]
            item.user_properties.append((k, str(v)))


@pytest.fixture(autouse=True)
def add_file_and_line_attr(
    record_xml_attribute: Callable[[str, str], None], request: pytest.FixtureRequest
) -> None:
    """Adding line & file to the <testcase> attribute in the XML"""
    node = request.node  # pyright: ignore[reportUnknownVariableType]
    raw_file_path, line_number, _ = node.location  # pyright: ignore[reportUnknownVariableType]

    # turning `../../../_main/<file_path>` into => <filepath>
    clean_file_path = raw_file_path.split("_main/")[-1]  # pyright: ignore[reportUnknownVariableType]
    record_xml_attribute("file", str(clean_file_path))
    # Convert pytest's 0-based source line number to 1-based numbering for XML output.
    record_xml_attribute("line", str(line_number + 1))
