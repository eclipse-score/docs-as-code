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
# req-Id: tool_req__docs_dd_link_source_code_link

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, order=True)
class NeedLink:
    """Represents a single template string finding in a file."""

    file: Path
    line: int
    tag: str
    need: str
    full_line: str


def DefaultNeedLink() -> NeedLink:
    """
    Return a default NeedLinks to be used as 'default args' or so
    Like this better than adding defaults to the dataclass, as it is deliberate
    """
    return NeedLink(
        file=Path("."),
        line=0,
        tag="",
        need="",
        full_line="",
    )


class NeedLinkEncoder(json.JSONEncoder):
    def default(self, o: object):
        if isinstance(o, NeedLink):
            return asdict(o)
        if isinstance(o, Path):
            return str(o)
        return super().default(o)


def needlink_decoder(d: dict[str, Any]) -> NeedLink | dict[str, Any]:
    if {"file", "line", "tag", "need", "full_line"} <= d.keys():
        return NeedLink(
            file=Path(d["file"]),
            line=d["line"],
            tag=d["tag"],
            need=d["need"],
            full_line=d["full_line"],
        )
    # It's something else, pass it on to other decoders
    return d


def store_source_code_links_json(file: Path, needlist: list[NeedLink]):
    # After `rm -rf _build` or on clean builds the directory does not exist,
    # so we need to create it
    file.parent.mkdir(exist_ok=True)
    with open(file, "w") as f:
        json.dump(
            needlist,
            f,
            cls=NeedLinkEncoder,  # use your custom encoder
            indent=2,
            ensure_ascii=False,
        )


def load_source_code_links_json(file: Path) -> list[NeedLink]:
    if not file.is_absolute():
        # use env variable set by Bazel
        ws_root = os.environ.get("BUILD_WORKSPACE_DIRECTORY")
        if ws_root:
            file = Path(ws_root) / file

    links: list[NeedLink] = json.loads(
        file.read_text(encoding="utf-8"),
        object_hook=needlink_decoder,
    )
    assert isinstance(links, list), (
        "The source code links should be a list of NeedLink objects."
    )
    assert all(isinstance(link, NeedLink) for link in links), (
        "All items in source_code_links should be NeedLink objects."
    )
    return links
