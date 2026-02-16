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
"""
This file defines the TestLink and TestCaseNeed.
It also defines encoding & decoding for JSON write/reading of TestLinks

TestCaseNeed => The datatype that testcases from the test.xml get parsed into
TestLink => The datatype that is ultimately saved inside of the JSON
"""

# req-Id: tool_req__docs_test_link_testcase

import html
import json
import re
from dataclasses import asdict, dataclass
from itertools import chain
from pathlib import Path
from typing import Any

from sphinx_needs import logging

LOGGER = logging.get_logger(__name__)


@dataclass(frozen=True, order=True)
class DataForTestLink:
    name: str
    file: Path
    line: int
    need: str
    verify_type: str
    result: str
    result_text: str = ""


class DataForTestLink_JSON_Encoder(json.JSONEncoder):
    def default(self, o: object):
        if isinstance(o, DataForTestLink):
            return asdict(o)
        if isinstance(o, Path):
            return str(o)
        return super().default(o)


def DataForTestLink_JSON_Decoder(d: dict[str, Any]) -> DataForTestLink | dict[str, Any]:
    if {
        "name",
        "file",
        "line",
        "need",
        "verify_type",
        "result",
        "result_text",
    } <= d.keys():
        return DataForTestLink(
            name=d["name"],
            file=Path(d["file"]),
            line=d["line"],
            need=d["need"],
            verify_type=d["verify_type"],
            result=d["result"],
            result_text=d["result_text"],
        )
    # It's something else, pass it on to other decoders
    return d


# We will have everything as string here as that mirrors the xml file
@dataclass
class DataOfTestCase:
    name: str
    file: str
    line: str
    result: str  # passed | falied | skipped | disabled
    # Intentionally not snakecase to make dict parsing simple
    TestType: str
    DerivationTechnique: str
    result_text: str = ""  # Can be None on anything but failed
    # Either or HAVE to be filled.
    PartiallyVerifies: str | None = None
    FullyVerifies: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]):  # type-ignore
        return cls(
            name=data["name"],
            file=data["file"],
            line=data["line"],
            result=data["result"],
            TestType=data["TestType"],
            DerivationTechnique=data["DerivationTechnique"],
            result_text=data["result_text"],
            PartiallyVerifies=data.get("PartiallyVerifies"),
            FullyVerifies=data.get("FullyVerifies"),
        )

    @classmethod
    def clean_text(cls, text: str):
        # This might not be the right thing in all circumstances

        # Designed to find ansi terminal codes (formatting&color) and santize the text
        # '\x1b[0m' => '' # Reset formatting code
        # '\x1b[31m' => '' # Red text
        ansi_regex = re.compile(r"\x1b\[[0-9;]*m")
        ansi_clean = ansi_regex.sub("", text)
        # Will turn HTML things back into 'symbols'. E.g. '&lt;' => '<'
        decoded = html.unescape(ansi_clean)
        return str(decoded.replace("\n", " ")).strip()

    def __post_init__(self):
        # Cleaning text
        if self.result_text:
            self.result_text = self.clean_text(self.result_text)
        # Self assertion to double check some mandatory options
        # For now this is disabled

        # It's mandatory that the test either partially or fully verifies a requirement
        # if self.PartiallyVerifies is None and self.FullyVerifies is None:
        #     raise ValueError(
        #         f"TestCase: {self.id} Error. Either 'PartiallyVerifies' or "
        #         "'FullyVerifies' must be provided."
        #     )
        # Skipped tests should always have a reason associated with them
        # if "skipped" in self.result.keys() and not list(self.result.values())[0]:
        #     raise ValueError(
        #         f"TestCase: {self.id} Error. Test was skipped without provided "
        #         "reason, reason is mandatory for skipped tests."
        #     )

    def get_test_links(self) -> list[DataForTestLink]:
        """Convert TestCaseNeed to list of TestLink objects."""

        def parse_attributes(verify_field: str | None, verify_type: str):
            """Process a verification field and yield TestLink objects."""
            if not verify_field:
                return

            LOGGER.debug(
                f"{verify_type.upper()} VERIFIES: {verify_field}",
                type="score_source_code_linker",
            )

            for need in verify_field.split(","):
                yield DataForTestLink(
                    name=self.name,
                    file=Path(self.file),
                    line=int(self.line),
                    need=need.strip(),
                    verify_type=verify_type,
                    result=self.result,
                    result_text=self.result_text,
                )

        return list(
            chain(
                parse_attributes(self.PartiallyVerifies, "partially"),
                parse_attributes(self.FullyVerifies, "fully"),
            )
        )


class DataOfTestCase_JSON_Encoder(json.JSONEncoder):
    def default(self, o: object):
        if isinstance(o, DataOfTestCase):
            return asdict(o)
        return super().default(o)


def DataOfTestCase_JSON_Decoder(d: dict[str, Any]) -> DataOfTestCase | dict[str, Any]:
    if {
        "name",
        "file",
        "line",
        "result",
        "TestType",
        "DerivationTechnique",
        "result_text",
        "PartiallyVerifies",
        "FullyVerifies",
    } <= d.keys():
        return DataOfTestCase(
            name=d["name"],
            file=d["file"],
            line=d["line"],
            result=d["result"],
            TestType=d["TestType"],
            DerivationTechnique=d["DerivationTechnique"],
            result_text=d["result_text"],
            PartiallyVerifies=d["PartiallyVerifies"],
            FullyVerifies=d["FullyVerifies"],
        )
    # It's something else, pass it on to other decoders
    return d


def store_test_xml_parsed_json(file: Path, testlist: list[DataForTestLink]):
    """
    TestCases that are 'skipped' do not have properties, therefore they will NOT be
    saved/transformed to TestLinks.
    """
    # After `rm -rf _build` or on clean builds the directory does not exist, so we need
    # to create it
    file.parent.mkdir(exist_ok=True)
    with open(file, "w") as f:
        json.dump(
            testlist,
            f,
            cls=DataForTestLink_JSON_Encoder,
            indent=2,
            ensure_ascii=False,
        )


def load_test_xml_parsed_json(file: Path) -> list[DataForTestLink]:
    links: list[DataForTestLink] = json.loads(
        file.read_text(encoding="utf-8"),
        object_hook=DataForTestLink_JSON_Decoder,
    )
    assert isinstance(links, list), (
        "The source xml parser links should be a list of TestLink objects."
    )
    assert all(isinstance(link, DataForTestLink) for link in links), (
        "All items in source_xml_parser should be TestLink objects."
    )
    return links


def store_data_of_test_case_json(file: Path, testneeds: list[DataOfTestCase]):
    # After `rm -rf _build` or on clean builds the directory does not exist, so we need
    # to create it
    file.parent.mkdir(exist_ok=True)
    with open(file, "w") as f:
        json.dump(
            testneeds,
            f,
            cls=DataOfTestCase_JSON_Encoder,
            indent=2,
            ensure_ascii=False,
        )


def load_data_of_test_case_json(file: Path) -> list[DataOfTestCase]:
    links: list[DataOfTestCase] = json.loads(
        file.read_text(encoding="utf-8"),
        object_hook=DataOfTestCase_JSON_Decoder,
    )
    assert isinstance(links, list), (
        "The test_case_need json should be a list of TestCaseNeed objects."
    )
    assert all(isinstance(link, DataOfTestCase) for link in links), (
        "All items in source_xml_parser should be TestCaseNeed objects."
    )
    return links
