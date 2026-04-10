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
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from src.extensions.score_source_code_linker.need_source_links import (
    NeedSourceLinks,
    SourceCodeLinks,
    SourceCodeLinks_JSON_Decoder,
)
from src.extensions.score_source_code_linker.needlinks import NeedLink
from src.extensions.score_source_code_linker.testlink import DataForTestLink


@dataclass
class RepoInfo:
    name: str
    hash: str
    url: str


def DefaultRepoInfo() -> RepoInfo:
    return RepoInfo(name="local_repo", hash="", url="")


@dataclass
class RepoSourceLinks:
    repo: RepoInfo
    needs: list[SourceCodeLinks] = field(default_factory=list)


class RepoSourceLinks_TEST_JSON_Encoder(json.JSONEncoder):
    def default(self, o: object) -> str | dict[str, Any]:
        if isinstance(o, Path):
            return str(o)
        # We do not want to save the metadata inside the codelink or testlink
        # As we save this already in a structure above it
        # (hash, module_name, url)
        if isinstance(o, NeedLink | DataForTestLink):
            return o.to_dict_without_metadata()
        # We need to split this up, otherwise the nested
        # dictionaries won't get split up and we will not
        # run into the 'to_dict_without_metadata' as
        # everything will be converted to a normal dictionary
        if isinstance(o, RepoSourceLinks):
            return {
                "repo": asdict(o.repo),
                "needs": o.needs,  # Let the encoder handle the list
            }
        if isinstance(o, SourceCodeLinks):
            return {
                "need": o.need,
                "links": o.links,
            }
        if isinstance(o, NeedSourceLinks):
            return {
                "CodeLinks": o.CodeLinks,
                "TestLinks": o.TestLinks,
            }
        return super().default(o)


def RepoSourceLinks_JSON_Decoder(
    d: dict[str, Any],
) -> RepoSourceLinks | dict[str, Any]:
    if "repo" in d and "needs" in d:
        repo = d["repo"]
        needs = d["needs"]
        return RepoSourceLinks(
            repo=RepoInfo(
                name=repo.get("name"),
                hash=repo.get("hash"),
                url=repo.get("url"),
            ),
            # We know this can only be list[SourceCodeLinks] and nothing else
            # Therefore => we ignore the type error here
            needs=[SourceCodeLinks_JSON_Decoder(need) for need in needs],  # type: ignore
        )
    return d


def store_repo_source_links_json(file: Path, source_code_links: list[RepoSourceLinks]):
    # After `rm -rf _build` or on clean builds the directory does not exist,
    # so we need to create it. We create any folder that might be missing
    file.parent.mkdir(exist_ok=True, parents=True)
    with open(file, "w") as f:
        json.dump(
            source_code_links,
            f,
            cls=RepoSourceLinks_TEST_JSON_Encoder,
            indent=2,
            ensure_ascii=False,
        )


def load_repo_source_links_json(file: Path) -> list[RepoSourceLinks]:
    links: list[RepoSourceLinks] = json.loads(
        file.read_text(encoding="utf-8"),
        object_hook=RepoSourceLinks_JSON_Decoder,
    )
    assert isinstance(links, list), (
        "The RepoSourceLink json should be a list of RepoSourceLink objects."
    )
    assert all(isinstance(link, RepoSourceLinks) for link in links), (
        "All items in repo source link cache should be RepoSourceLink objects."
    )
    return links


def group_needs_by_repo(links: list[SourceCodeLinks]) -> list[RepoSourceLinks]:
    repo_groups: dict[str, RepoSourceLinks] = {}

    for source_link in links:
        # Check if we can take repoInfo from code or testlinks
        if source_link.links.CodeLinks:
            first_link = source_link.links.CodeLinks[0]
        elif source_link.links.TestLinks:
            first_link = source_link.links.TestLinks[0]
        else:
            # This should not happen?
            continue
        repo_key = first_link.repo_name

        if repo_key not in repo_groups:
            repo_groups[repo_key] = RepoSourceLinks(
                repo=RepoInfo(name=repo_key, hash=first_link.hash, url=first_link.url)
            )

        # TODO: Add an assert that checks if needs only are
        # in a singular repo (not allowed to be in multiple)
        repo_groups[repo_key].needs.append(source_link)

    return [
        RepoSourceLinks(repo=group.repo, needs=group.needs)
        for group in repo_groups.values()
    ]
