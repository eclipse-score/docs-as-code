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
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

from src.extensions.score_source_code_linker.need_source_links import (
    NeedSourceLinks,
    SourceCodeLinks,
    SourceCodeLinks_JSON_Decoder,
    SourceCodeLinks_JSON_Encoder,
    load_source_code_links_combined_json,
    store_source_code_links_combined_json,
)
from src.extensions.score_source_code_linker.needlinks import NeedLink
from src.extensions.score_source_code_linker.testlink import DataForTestLink
from src.extensions.score_source_code_linker.tests.test_codelink import (
    NeedLinkTestEncoder,
    needlink_test_decoder,
)


def SourceCodeLinks_TEST_JSON_Decoder(
    d: dict[str, Any],
) -> SourceCodeLinks | dict[str, Any]:
    if "need" in d and "links" in d:
        links = d["links"]
        return SourceCodeLinks(
            need=d["need"],
            links=NeedSourceLinks(
                CodeLinks=[
                    needlink_test_decoder(cl) for cl in links.get("CodeLinks", [])
                ],
                TestLinks=[DataForTestLink(**tl) for tl in links.get("TestLinks", [])],
            ),
        )
    return d


class SourceCodeLinks_TEST_JSON_Encoder(json.JSONEncoder):
    def default(self, o: object):
        if isinstance(o, SourceCodeLinks):
            return {
                "need": o.need,
                "links": self.default(o.links),
            }
        if isinstance(o, NeedSourceLinks):
            return {
                "CodeLinks": [NeedLinkTestEncoder().default(cl) for cl in o.CodeLinks],
                "TestLinks": [asdict(tl) for tl in o.TestLinks],
            }
        if isinstance(o, Path):
            return str(o)
        return super().default(o)


@pytest.fixture
def sample_needlink() -> NeedLink:
    return NeedLink(
        file=Path("src/example.py"),
        line=10,
        tag="# req:",
        need="REQ_001",
        full_line="# req: REQ_001",
    )


@pytest.fixture
def sample_testlink() -> DataForTestLink:
    return DataForTestLink(
        name="test_example",
        file=Path("tests/test_example.py"),
        need="REQ_001",
        line=5,
        verify_type="partially",
        result="passed",
        result_text="",
    )


@pytest.fixture
def sample_source_code_links(sample_needlink, sample_testlink) -> SourceCodeLinks:
    return SourceCodeLinks(
        need="REQ_001",
        links=NeedSourceLinks(CodeLinks=[sample_needlink], TestLinks=[sample_testlink]),
    )


def test_encoder_outputs_serializable_dict(sample_source_code_links):
    encoded = json.dumps(sample_source_code_links, cls=SourceCodeLinks_JSON_Encoder)
    assert isinstance(encoded, str)
    assert "REQ_001" in encoded


def test_decoder_reconstructs_object(sample_source_code_links):
    encoded = json.dumps(sample_source_code_links, cls=SourceCodeLinks_JSON_Encoder)
    decoded = json.loads(encoded, object_hook=SourceCodeLinks_JSON_Decoder)
    assert isinstance(decoded, SourceCodeLinks)
    assert decoded.need == "REQ_001"
    assert isinstance(decoded.links, NeedSourceLinks)
    assert decoded.links.CodeLinks[0].need == "REQ_001"


def test_store_and_load_json(tmp_path: Path, sample_source_code_links):
    test_file = tmp_path / "combined_links.json"
    store_source_code_links_combined_json(test_file, [sample_source_code_links])
    assert test_file.exists()

    loaded = load_source_code_links_combined_json(test_file)
    assert isinstance(loaded, list)
    assert len(loaded) == 1
    assert isinstance(loaded[0], SourceCodeLinks)
    assert loaded[0].need == sample_source_code_links.need


def test_load_invalid_json_type(tmp_path: Path):
    test_file = tmp_path / "invalid.json"
    test_file.write_text('{"not_a_list": true}', encoding="utf-8")

    with pytest.raises(AssertionError, match="should be a list of SourceCodeLinks"):
        _ = load_source_code_links_combined_json(test_file)


def test_load_invalid_json_items(tmp_path: Path):
    test_file = tmp_path / "bad_items.json"
    # This is a list but doesn't contain SourceCodeLinks
    test_file.write_text('[{"some": "thing"}]', encoding="utf-8")

    with pytest.raises(AssertionError, match="should be SourceCodeLinks objects"):
        _ = load_source_code_links_combined_json(test_file)
