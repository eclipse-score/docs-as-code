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
This file defines NeedSourceLinks as well as SourceCodeLinks. Both datatypes are used in
the 'grouped cache' JSON that contains 'CodeLinks' and 'TestLinks' It also defines a
decoder and encoder for SourceCodeLinks to enable JSON read/write
"""

# req-Id: tool_req__docs_test_link_testcase
# req-Id: tool_req__docs_dd_link_source_code_link

import json
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.extensions.score_source_code_linker.needlinks import (
    NeedLink,
)
from src.extensions.score_source_code_linker.testlink import (
    DataForTestLink,
)


@dataclass
class NeedSourceLinks:
    CodeLinks: list[NeedLink] = field(default_factory=list)
    TestLinks: list[DataForTestLink] = field(default_factory=list)


@dataclass
class SourceCodeLinks:
    # TODO: Find a good key name for this
    need: str
    links: NeedSourceLinks
    # Example:
    #
    # need: <str>
    # links:
    #   {
    #   "CodeLinks:
    #       [{needlink},{needlink}...],
    #   "TestLinks":
    #       [{testlink},{testlink},...]


class SourceCodeLinks_JSON_Encoder(json.JSONEncoder):
    def default(self, o: object):
        if isinstance(o, SourceCodeLinks | NeedSourceLinks):
            return asdict(o)
        if isinstance(o, NeedLink | DataForTestLink):
            return asdict(o)
        if isinstance(o, Path):
            return str(o)
        return super().default(o)


def SourceCodeLinks_JSON_Decoder(d: dict[str, Any]) -> SourceCodeLinks | dict[str, Any]:
    if "need" in d and "links" in d:
        links = d["links"]
        return SourceCodeLinks(
            need=d["need"],
            links=NeedSourceLinks(
                CodeLinks=[NeedLink(**cl) for cl in links.get("CodeLinks", [])],
                TestLinks=[DataForTestLink(**tl) for tl in links.get("TestLinks", [])],
            ),
        )
    return d


def store_source_code_links_combined_json(
    file: Path, source_code_links: list[SourceCodeLinks]
):
    # After `rm -rf _build` or on clean builds the directory does not exist,
    # so we need to create it. We create any folder that might be missing
    file.parent.mkdir(exist_ok=True, parents=True)
    with open(file, "w") as f:
        json.dump(
            source_code_links,
            f,
            cls=SourceCodeLinks_JSON_Encoder,
            indent=2,
            ensure_ascii=False,
        )


def load_source_code_links_combined_json(file: Path) -> list[SourceCodeLinks]:
    links: list[SourceCodeLinks] = json.loads(
        file.read_text(encoding="utf-8"),
        object_hook=SourceCodeLinks_JSON_Decoder,
    )
    assert isinstance(links, list), (
        "The combined source code linker links should be "
        "a list of SourceCodeLinks objects."
    )
    assert all(isinstance(link, SourceCodeLinks) for link in links), (
        "All items in combined_source_code_linker_cache should be "
        "SourceCodeLinks objects."
    )
    return links


def group_by_need(
    source_code_links: list[NeedLink],
    test_case_links: list[DataForTestLink] | None = None,
) -> list[SourceCodeLinks]:
    """
    Groups the given need links and test case links by their need ID.
    Returns a nested dictionary structure with 'CodeLink' and 'TestLink' categories.
    Example output:


      {
        "need": "<need_id>",
        "links": {
          "CodeLinks": [NeedLink, NeedLink, ...],
          "TestLinks": [testlink, testlink, ...]
        }
      }
    """
    # TODO: I wonder if there is a more efficent way to do this
    grouped_by_need: dict[str, NeedSourceLinks] = defaultdict(
        lambda: NeedSourceLinks(TestLinks=[], CodeLinks=[])
    )

    # Group source code links
    for needlink in source_code_links:
        grouped_by_need[needlink.need].CodeLinks.append(needlink)

    # Group test case links
    if test_case_links is not None:
        for testlink in test_case_links:
            grouped_by_need[testlink.need].TestLinks.append(testlink)

    # Build final list of SourceCodeLinks
    result: list[SourceCodeLinks] = [
        SourceCodeLinks(
            need=need,
            links=NeedSourceLinks(
                CodeLinks=need_links.CodeLinks,
                TestLinks=need_links.TestLinks,
            ),
        )
        for need, need_links in grouped_by_need.items()
    ]

    return result
