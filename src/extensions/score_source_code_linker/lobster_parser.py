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
"""
Alternative producer for test links, reading ``*.lobster`` activity traces
instead of ``bazel-testlogs/**/test.xml``.

``lobster-gtest`` already parses the GoogleTest XML itself, so the ``.lobster``
pools are a downstream artifact of the very same data: every ``RecordProperty``
other than ``lobster-tracing`` is rendered into the item's ``text`` field as
``:Key: value`` lines, and the test result is condensed into ``status``.

This module produces exactly the same two caches as ``xml_parser.run_xml_parser``
so that everything downstream (``group_by_need``, the repo grouping and
``inject_links_into_needs``) works unchanged. Which of the two producers runs is
decided by the ``score_testlink_source`` configuration value.

Known fidelity losses compared to the XML producer:
  * ``result_text`` is always empty - lobster-gtest drops the ``<failure>``
    message and only keeps a boolean outcome.
  * ``skipped`` cannot be distinguished from ``passed`` - lobster-gtest only
    inspects the ``<failure>`` element, so a ``GTEST_SKIP()`` test is reported
    as ``ok``.
"""

# req-Id: tool_req__docs_test_link_testcase

import itertools
import json
import os
import re
from pathlib import Path

from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx_needs import logging

from src.extensions.score_source_code_linker.helpers import (
    parse_info_from_known_good,
    parse_repo_name_from_path,
)
from src.extensions.score_source_code_linker.needlinks import (
    DefaultMetaData,
    MetaData,
)
from src.extensions.score_source_code_linker.testlink import (
    DataOfTestCase,
    store_data_of_test_case_json,
    store_test_xml_parsed_json,
)
from src.extensions.score_source_code_linker.xml_parser import construct_and_add_need
from src.helper_lib import find_ws_root

logger = logging.get_logger(__name__)

LOBSTER_ACTIVITY_SCHEMA = "lobster-act-trace"

# lobster-gtest renders the RecordProperty keys through ``str.capitalize()``,
# which is lossy ("TestType" -> "Testtype"). Map them back to the field names
# of DataOfTestCase.
_TEXT_KEY_MAP = {
    "partiallyverifies": "PartiallyVerifies",
    "fullyverifies": "FullyVerifies",
    "testtype": "TestType",
    "derivationtechnique": "DerivationTechnique",
}

# ``_resolve_test_status`` in lobster-gtest only knows these three outcomes.
_STATUS_MAP = {
    "ok": "passed",
    "fail": "failed",
    "not run": "disabled",
}

_TEXT_LINE_RE = re.compile(r"^:([A-Za-z]+):\s*(.*)$")


def parse_text_block(text: str | None) -> dict[str, str]:
    """Turn a lobster ``text`` blob into DataOfTestCase field names.

    ``":Testtype: requirements-based"`` becomes
    ``{"TestType": "requirements-based"}``. Unknown keys (e.g. ``:Description:``)
    are dropped, mirroring ``xml_parser.parse_properties``.
    """
    properties: dict[str, str] = {}
    for line in (text or "").splitlines():
        match = _TEXT_LINE_RE.match(line.strip())
        if match is None:
            continue
        field = _TEXT_KEY_MAP.get(match.group(1).lower())
        if field is not None:
            properties[field] = match.group(2).strip()
    return properties


def normalize_test_name(name: str) -> str:
    """Align the lobster naming with the one used by the XML producer.

    lobster-gtest builds ``f"{suite_name}:{test_name}"`` while
    ``read_test_xml_file`` joins the same two parts with ``"__"``. Normalizing
    here keeps the generated ``testcase__<name>_<hash>`` IDs identical for both
    producers.
    """
    return name.replace(":", "__")


def get_metadata_from_lobster_path(raw_filepath: Path) -> MetaData:
    """Derive repo metadata from the location of the ``.lobster`` file.

    Mirrors ``xml_parser.get_metadata_from_test_path``, but keys off ``bazel-bin``
    instead of ``bazel-testlogs``. External repositories show up as
    ``bazel-bin/external/<repo>+/...``, everything else is the local repository.
    """
    md = DefaultMetaData()
    path_str = str(raw_filepath)
    if "bazel-bin/" in path_str:
        clean_filepath = Path(path_str.split("bazel-bin/")[-1])
    elif "bazel-out/" in path_str:
        # bazel-bin is a symlink into bazel-out/<config>/bin; strip the two
        # leading path segments so that a possible "external/<repo>+" prefix
        # becomes visible to parse_repo_name_from_path.
        remainder = Path(path_str.split("bazel-out/")[-1]).parts[2:]
        clean_filepath = Path(*remainder) if remainder else raw_filepath
    else:
        return md

    md["repo_name"] = parse_repo_name_from_path(clean_filepath)
    known_good_json = os.environ.get("KNOWN_GOOD_JSON")
    if md["repo_name"] != "local_repo" and known_good_json:
        md["hash"], md["url"] = parse_info_from_known_good(
            Path(known_good_json), md["repo_name"]
        )
    return md


def item_to_test_case(item: dict[str, object], md: MetaData) -> DataOfTestCase:
    """Convert a single lobster activity item into a DataOfTestCase."""
    location = item.get("location")
    location = location if isinstance(location, dict) else {}
    line = location.get("line")
    status = item.get("status")

    properties: dict[str, object] = {
        "name": normalize_test_name(str(item.get("name", ""))),
        "file": location.get("file"),
        "line": str(line) if line is not None else None,
        "result": _STATUS_MAP.get(str(status), "disabled"),
        # lobster-gtest discards the <failure> message, so there is never a
        # result text. It must not be None though, is_valid() rejects that.
        "result_text": "",
    }
    text = item.get("text")
    properties.update(parse_text_block(text if isinstance(text, str) else None))
    properties.update(md)
    return DataOfTestCase.from_dict(properties)


def find_lobster_files(search_paths: list[Path]) -> list[Path]:
    """Collect all ``*.lobster`` files below the given directories.

    ``bazel-bin`` is a symlink into ``bazel-out``, so the search path itself is
    resolved first. Symlinks *below* it are deliberately not followed: runfiles
    trees link back into the workspace (and into ``bazel-bin`` itself), which
    would make the walk cyclic. ``.runfiles`` directories only ever contain
    copies of outputs that are also present in their regular location, so they
    are pruned as well.
    """
    found: list[Path] = []
    seen: set[Path] = set()
    for search_path in search_paths:
        if not search_path.exists():
            continue
        for root, dirs, files in os.walk(search_path.resolve()):
            dirs[:] = [d for d in dirs if not d.endswith(".runfiles")]
            for filename in files:
                if not filename.endswith(".lobster"):
                    continue
                path = Path(root) / filename
                if path in seen:
                    continue
                seen.add(path)
                found.append(path)
    return found


def read_lobster_file(file: Path) -> tuple[list[DataOfTestCase], list[str]]:
    """Read one ``.lobster`` file and return its test cases.

    Returns a tuple of the parsed test cases and the names of those that are
    missing mandatory properties (and will therefore not be linked).
    """
    try:
        document = json.loads(file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        logger.warning(
            f"Could not read lobster file '{file}': {exc}",
            type="score_source_code_linker",
        )
        return [], []

    if not isinstance(document, dict):
        return [], []
    if document.get("schema") != LOBSTER_ACTIVITY_SCHEMA:
        # Requirement and implementation pools carry no test information.
        return [], []

    data = document.get("data")
    if not isinstance(data, list):
        return [], []

    md = get_metadata_from_lobster_path(file)
    test_cases: list[DataOfTestCase] = []
    invalid: list[str] = []
    for item in data:
        if not isinstance(item, dict) or item.get("kind") != "test":
            continue
        test_case = item_to_test_case(item, md)
        if not test_case.is_valid():
            invalid.append(str(test_case.name))
        test_cases.append(test_case)
    return test_cases, invalid


def run_lobster_parser(app: Sphinx, _: BuildEnvironment) -> None:
    """Build testcase needs from ``*.lobster`` pools.

    Drop-in replacement for ``xml_parser.run_xml_parser``: it writes the very
    same caches, so the combining and injection steps stay untouched.
    """
    ws_root = find_ws_root()
    if ws_root is None:
        return

    lobster_files = find_lobster_files([ws_root / "bazel-bin"])
    logger.info(
        f"Found {len(lobster_files)} lobster files in total. Parsing them now",
        type="score_source_code_linker",
    )
    if not lobster_files:
        logger.info(
            "Did not find any '.lobster' files. If test data should be parsed, "
            "please build the corresponding unit()/component()/"
            "dependable_element() targets before building the documentation.",
            type="score_source_code_linker",
        )

    test_case_needs: list[DataOfTestCase] = []
    invalid_names: list[str] = []
    for file in lobster_files:
        test_cases, invalid = read_lobster_file(file)
        invalid_names.extend(invalid)
        test_case_needs.extend(test_cases)
        for test_case in test_cases:
            construct_and_add_need(app, test_case)

    if invalid_names:
        logger.info(
            f"Tests missing some properties: {', '.join(invalid_names)}",
            type="score_source_code_linker",
        )

    # Always write the caches, even when empty. Otherwise a stale cache from a
    # previous run (possibly produced by the XML parser) would silently be
    # picked up by build_and_save_combined_file.
    logger.info(
        f"Saving {len(test_case_needs)} test case needs to the cache "
        "`score_testcaseneeds_cache.json` in _build/.",
        type="score_source_code_linker",
    )
    store_data_of_test_case_json(
        app.outdir / "score_testcaseneeds_cache.json", test_case_needs
    )
    output = list(
        itertools.chain.from_iterable(tcn.get_test_links() for tcn in test_case_needs)
    )
    logger.info(
        f"Saving {len(output)} parsed testcases to the cache "
        "`score_xml_parser_cache.json` in _build/.",
        type="score_source_code_linker",
    )
    store_test_xml_parsed_json(app.outdir / "score_xml_parser_cache.json", output)
