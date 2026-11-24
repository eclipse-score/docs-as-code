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
Sphinx side of the testcases: turns the testcases parsed by xml_parser.py into
'testcase' external needs, and writes the testcase caches into _build.
"""

import base64
import contextlib
import hashlib
import itertools
from pathlib import Path

from sphinx.application import Sphinx
from sphinx_needs import logging
from sphinx_needs.api import add_external_need

from src.extensions.score_source_code_linker.testlink import (
    DataOfTestCase,
    store_data_of_test_case_json,
    store_test_xml_parsed_json,
)
from src.extensions.score_source_code_linker.xml_parser import (
    find_test_folder,
    find_xml_files,
    parse_test_xml_files,
    parse_testcase_source_dirs,
)
from src.helper_lib.repo_info import (
    get_github_link,
    get_placeholder_github_link,
    load_known_good,
)

logger = logging.get_logger(__name__)


def build_testcase_needs(app: Sphinx, *, local_module: str) -> None:
    """
    Parse the test.xml files (xml_parser), add a 'testcase' need for each
    testcase and write the two testcase caches into _build.
    """
    testlogs_dir = find_test_folder()
    if testlogs_dir is None:
        return
    allowed_dirs = parse_testcase_source_dirs(
        getattr(app.config, "testcase_source_dirs", "")
    )
    if allowed_dirs:
        logger.info(
            f"Scoping testcase needs to source dirs: {allowed_dirs}",
            type="score_source_code_linker",
        )
    known_good_json_str = app.config.KNOWN_GOOD_JSON.strip()
    known_good = (
        load_known_good(Path(known_good_json_str)) if known_good_json_str else None
    )
    test_case_needs = parse_test_xml_files(
        find_xml_files(testlogs_dir),
        known_good,
        allowed_dirs,
        local_module=local_module,
    )
    for tc in test_case_needs:
        construct_and_add_need(app, tc, local_module=local_module)
    # Saving the test case needs for cache
    logger.info(
        f"Saving {len(test_case_needs)} test case needs to the cache `score_testcaseneeds_cache.json` in _build/."
    )
    store_data_of_test_case_json(
        app.outdir / "score_testcaseneeds_cache.json", test_case_needs
    )
    output = list(
        itertools.chain.from_iterable(tcn.get_test_links() for tcn in test_case_needs)
    )
    # This is not ideal, due to duplication, but I can't think of a better solution
    # right now
    logger.info(
        f"Saving {len(output)} parsed testcases to the cache `score_xml_parser_cache.json` in _build/."
    )
    store_test_xml_parsed_json(app.outdir / "score_xml_parser_cache.json", output)


def short_hash(input_str: str, length: int = 5) -> str:
    # Get a stable hash
    sha256 = hashlib.sha256(input_str.encode()).digest()
    # Encode to base32 (A-Z + 2-7), decode to str, remove padding
    b32 = base64.b32encode(sha256).decode("utf-8").rstrip("=")
    # Keep only alphabetic characters
    letters_only = "".join(filter(str.isalpha, b32))
    # Return the first `length` letters
    return letters_only[:length].lower()


def construct_and_add_need(app: Sphinx, tn: DataOfTestCase, *, local_module: str = ""):
    # We will now allow file to be empty in case of non fully fleshed out testcases
    file = tn.file if tn.file is not None else "<placeholder_file>"
    assert tn.name is not None
    name = tn.name
    if tn.repo is None:
        # I would change this to debug for now, as it seems too spammy in 'info'
        logger.debug(
            "Creating testcase need with fallback URL due to incomplete repo metadata: "
            f"name={name}, file={file}, repo={tn.repo}",
            type="score_source_code_linker",
        )
    external_url = get_github_link(
        tn.repo,
        tn.file,
        tn.line,
        plain_links=not tn.file,
        local_module=local_module,
    )
    if not external_url:
        # An unpinned dependency or a checkout without a remote has no source URL.
        # Sphinx-Needs still requires a URL for the external testcase Need.
        external_url = get_placeholder_github_link(tn.file, tn.line)
    # IDK if this is ideal or not
    with contextlib.suppress(BaseException):
        _ = add_external_need(
            app=app,
            need_type="testcase",
            title=name,
            tags="TEST",
            id=f"testcase__{name}_{short_hash(file + name)}",
            name=name,
            external_url=external_url,
            fully_verifies=tn.FullyVerifies if tn.FullyVerifies is not None else "",
            partially_verifies=tn.PartiallyVerifies
            if tn.PartiallyVerifies is not None
            else "",
            test_type=tn.TestType,
            derivation_technique=tn.DerivationTechnique,
            file=file,
            line=tn.line,
            result=tn.result,  # We just want the 'failed' or whatever
            result_text=tn.result_text if tn.result_text else "",
        )
