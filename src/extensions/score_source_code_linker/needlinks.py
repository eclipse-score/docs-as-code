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
from typing import Any, TypeGuard, TypedDict


class MetaData(TypedDict):
    module_name: str
    hash: str
    url: str

def is_metadata(x: object) -> TypeGuard[MetaData]:
    # Make this as strict/loose as you want; at minimum, it must be a dict.
    return isinstance(x, dict) and {"module_name", "hash", "url"} <= x.keys()


@dataclass(order=True)
class NeedLink:
    """Represents a single template string finding in a file."""

    file: Path
    line: int
    tag: str
    need: str
    full_line: str
    module_name: str = ""
    hash: str = ""
    url: str = ""

    def to_dict_full(self) -> dict[str, str | Path]:
        return asdict(self)

    def to_dict_without_metadata(self) -> dict[str, str | Path]:
        d = asdict(self)
        d.pop("module_name", None)
        d.pop("hash", None)
        d.pop("url", None)
        return d


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
        # Module_name, hash, url are defaulted to ""
        # therefore not needed to be listed
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
            module_name=d.get("module_name", ""),
            hash=d.get("hash", ""),
            url=d.get("url", ""),
        )
    # It's something else, pass it on to other decoders
    return d


def store_source_code_links_with_metadata_json(
    file: Path, metadata: MetaData, needlist: list[NeedLink]
) -> None:
    """
    Writes a JSON array:
      [ meta_dict, needlink1, needlink2, ... ]

    meta_dict must include:
      module_name, hash, url
    """
    payload: list[object] = [metadata, *needlist]

    file.parent.mkdir(exist_ok=True)
    with open(file, "w", encoding="utf-8") as f:
        json.dump(payload, f, cls=NeedLinkEncoder, indent=2, ensure_ascii=False)


def store_source_code_links_json(file: Path, needlist: list[NeedLink]) -> None:
    """
    Writes a JSON array:
      [ meta_dict, needlink1, needlink2, ... ]

    meta_dict must include:
      module_name, hash, url
    """

    file.parent.mkdir(exist_ok=True)
    with open(file, "w", encoding="utf-8") as f:
        json.dump(needlist, f, cls=NeedLinkEncoder, indent=2, ensure_ascii=False)


def _is_needlink_list(xs: list[object]) -> TypeGuard[list[NeedLink]]:
    return all(isinstance(link, NeedLink) for link in xs)


def load_source_code_links_with_metadata_json(file: Path) -> list[NeedLink]:
    """
    Expects the JSON array where first is a meta_dict:
      [ meta_dict, needlink1, needlink2, ... ]
    Returns:
      [NeedLink, NeedLink, ...]

    This normally should be the one called 'locally' => :docs target
    """
    if not file.is_absolute():
        ws_root = os.environ.get("BUILD_WORKSPACE_DIRECTORY")
        if ws_root:
            file = Path(ws_root) / file

    data: list[object] = json.loads(
        file.read_text(encoding="utf-8"),
        object_hook=needlink_decoder,
    )
    links: list[object] = []
    if not is_metadata(data[0]):
        raise TypeError(
            "If you do not have a 'metadata' dict as the first one in the json "
            "you might wanted to call the load without metadata named: "
            "'load_source_code_links_json'"
        )
    metadata: MetaData = data[0]
    links = data[1:]
    if not _is_needlink_list(links):
        raise TypeError(
            "In local build context all items after"
            f"metadata must decode to NeedLink objects. File: {file}"
        )
    for d in links:
        d.module_name = metadata["module_name"]
        d.hash = metadata["hash"]
        d.url = metadata["url"]
    return links


def load_source_code_links_json(file: Path) -> list[NeedLink]:
    """
    Expects the JSON array with needlinks
    *that already have extra info in them* (module_name, hash, url):
      [ needlink1, needlink2, ... ]
    Returns:
      [NeedLink, NeedLink, ...]

    This normally should be the one called in combo builds
    => :docs_combo_experimental target
    """
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
