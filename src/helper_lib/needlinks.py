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
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.helper_lib import Environment
from src.helper_lib.repo_info import (
    DefaultRepoInfo,
    RepoInfo,
    flatten_repo_field,
    split_repo_fields,
)

env = Environment()


# unsafe_hash: the dataclass is not frozen, so it is not hashable by default.
# Hashing & equality are needed to compare links (mainly in tests).
# The generated __eq__ / __hash__ cover every field, including 'repo'.
@dataclass(order=True, unsafe_hash=True)
class NeedLink:
    """Represents a single template string finding in a file."""

    file: Path
    line: int
    tag: str
    need: str
    full_line: str
    repo: RepoInfo = field(default_factory=DefaultRepoInfo)

    # 'Dictionary conversion' in the on-disk form: repo flattened into
    # repo_name, hash, url
    def to_dict_full(self) -> dict[str, Any]:
        return flatten_repo_field(asdict(self), self.repo)

    @classmethod
    def from_flat_dict(cls, d: dict[str, Any]) -> "NeedLink":
        """Build a NeedLink from its on-disk form. Missing repo keys => default repo."""
        rest, repo = split_repo_fields(d)
        return cls(**rest, repo=repo if repo is not None else DefaultRepoInfo())


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
        # repo defaults to DefaultRepoInfo()
    )


class NeedLinkEncoder(json.JSONEncoder):
    def default(self, o: object):
        if isinstance(o, NeedLink):
            return o.to_dict_full()
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
            repo=RepoInfo(
                name=d.get("repo_name", ""),
                hash=d.get("hash", ""),
                url=d.get("url", ""),
            ),
        )
    # It's something else, pass it on to other decoders
    return d


def store_source_code_links_json(file: Path, needlist: list[NeedLink]) -> None:
    """
    Writes a JSON array:
      [ needlink1, needlink2, ... ]
    """

    # After `rm -rf _build` or on clean builds the directory does not exist,
    # so we need to create it. We create any folder that might be missing
    file.parent.mkdir(exist_ok=True, parents=True)
    with open(file, "w", encoding="utf-8") as f:
        json.dump(needlist, f, cls=NeedLinkEncoder, indent=2, ensure_ascii=False)


def load_source_code_links_json(file: Path) -> list[NeedLink]:
    """
    Expects the JSON array with needlinks, each with its own repo_name, hash
    and url:
      [ needlink1, needlink2, ... ]
    Returns:
      [NeedLink, NeedLink, ...]
    """
    if not file.is_absolute():
        # use env variable set by Bazel
        ws_root = env.optional_path("BUILD_WORKSPACE_DIRECTORY")
        if ws_root:
            file = ws_root / file

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
