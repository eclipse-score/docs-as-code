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
import json
from pathlib import Path

from src.extensions.score_source_code_linker.testlink import (
    DataForTestLink,
    DataForTestLink_JSON_Decoder,
    DataForTestLink_JSON_Encoder,
    DataOfTestCase,
    load_test_xml_parsed_json,
    store_test_xml_parsed_json,
)
from attribute_plugin import add_test_properties


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_testlink_serialization_roundtrip():
    """Ensure that Encode/Decode is reversible"""
    link = DataForTestLink(
        name="my_test",
        file=Path("some/file.py"),
        line=123,
        need="REQ_001",
        verify_type="fully",
        result="passed",
        result_text="All good",
    )
    dumped = json.dumps(link, cls=DataForTestLink_JSON_Encoder)
    loaded = json.loads(dumped, object_hook=DataForTestLink_JSON_Decoder)

    assert isinstance(loaded, DataForTestLink)
    assert loaded == link


def test_testlink_encoder_handles_path():
    data = {"file": Path("some/thing.py")}
    encoded = json.dumps(data, cls=DataForTestLink_JSON_Encoder)
    assert '"file": "some/thing.py"' in encoded


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_decoder_ignores_irrelevant_dicts():
    """Ensure Decoder ignores data it doesn't understand"""
    input_data = {"foo": "bar"}
    result = DataForTestLink_JSON_Decoder(input_data)
    assert result == input_data


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_clean_text_removes_ansi_and_html_unescapes():
    """
    Test if text clean works as intended.
    It should remove ANSI color & text styles, as well as convert HTML things back to Chars
    """
    raw = "\x1b[31m&lt;b&gt;Warning&lt;/b&gt;\x1b[0m\nExtra line"
    cleaned = DataOfTestCase.clean_text(raw)
    assert cleaned == "<b>Warning</b> Extra line"


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_testcaseneed_to_dict_multiple_links():
    """
    Ensure that a DataOfTestCase can transform itself into a list of DataForTestLink.
    """
    case = DataOfTestCase(
        name="TC_01",
        file="src/test.py",
        line="10",
        result="failed",
        TestType="unit",
        DerivationTechnique="manual",
        result_text="Something went wrong",
        PartiallyVerifies="REQ-1, REQ-2",
        FullyVerifies="REQ-3",
    )

    links = case.get_test_links()

    assert len(links) == 3
    need_ids = [link.need for link in links]
    assert set(need_ids) == {"REQ-1", "REQ-2", "REQ-3"}

    for link in links:
        assert link.file == Path("src/test.py")
        assert link.line == 10
        assert link.name == "TC_01"
        assert link.result == "failed"


@add_test_properties(
    partially_verifies=["tool_req__docs_test_link_testcase"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_store_and_load_testlinks_roundtrip(tmp_path):
    """Ensure that Encode/Decode is reversible"""
    file = tmp_path / "testlinks.json"

    links = [
        DataForTestLink(
            name="L1",
            file=Path("abc.py"),
            line=1,
            need="REQ_A",
            verify_type="partially",
            result="passed",
            result_text="Looks good",
        ),
        DataForTestLink(
            name="L2",
            file=Path("def.py"),
            line=2,
            need="REQ_B",
            verify_type="fully",
            result="failed",
            result_text="Needs work",
        ),
    ]

    store_test_xml_parsed_json(file, links)
    assert file.exists()

    reloaded = load_test_xml_parsed_json(file)

    assert reloaded == links
    for link in reloaded:
        assert isinstance(link, DataForTestLink)
