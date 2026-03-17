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
class ModuleInfo:
    name: str
    hash: str
    url: str


@dataclass
class ModuleSourceLinks:
    module: ModuleInfo
    needs: list[SourceCodeLinks] = field(default_factory=list)


class ModuleSourceLinks_TEST_JSON_Encoder(json.JSONEncoder):
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
        if isinstance(o, ModuleSourceLinks):
            return {
                "module": asdict(o.module),
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


def ModuleSourceLinks_JSON_Decoder(
    d: dict[str, Any],
) -> ModuleSourceLinks | dict[str, Any]:
    if "module" in d and "needs" in d:
        module = d["module"]
        needs = d["needs"]
        return ModuleSourceLinks(
            module=ModuleInfo(
                name=module.get("name"),
                hash=module.get("hash"),
                url=module.get("url"),
            ),
            # We know this can only be list[SourceCodeLinks] and nothing else
            # Therefore => we ignore the type error here
            needs=[SourceCodeLinks_JSON_Decoder(need) for need in needs],  # type: ignore
        )
    return d


def store_module_source_links_json(
    file: Path, source_code_links: list[ModuleSourceLinks]
):
    # After `rm -rf _build` or on clean builds the directory does not exist,
    # so we need to create it. We create any folder that might be missing
    file.parent.mkdir(exist_ok=True, parents=True)
    with open(file, "w") as f:
        json.dump(
            source_code_links,
            f,
            cls=ModuleSourceLinks_TEST_JSON_Encoder,
            indent=2,
            ensure_ascii=False,
        )


def load_module_source_links_json(file: Path) -> list[ModuleSourceLinks]:
    links: list[ModuleSourceLinks] = json.loads(
        file.read_text(encoding="utf-8"),
        object_hook=ModuleSourceLinks_JSON_Decoder,
    )
    assert isinstance(links, list), (
        "The ModuleSourceLink json should be a list of ModuleSourceLink objects."
    )
    assert all(isinstance(link, ModuleSourceLinks) for link in links), (
        "All items in module source link cache should be ModuleSourceLink objects."
    )
    return links


def group_needs_by_module(links: list[SourceCodeLinks]) -> list[ModuleSourceLinks]:
    module_groups: dict[str, ModuleSourceLinks] = {}

    for source_link in links:
        # Check if we can take moduleInfo from code or testlinks
        if source_link.links.CodeLinks:
            first_link = source_link.links.CodeLinks[0]
        elif source_link.links.TestLinks:
            first_link = source_link.links.TestLinks[0]
        else:
            # This should not happen?
            continue
        module_key = first_link.module_name

        if module_key not in module_groups:
            module_groups[module_key] = ModuleSourceLinks(
                module=ModuleInfo(
                    name=module_key, hash=first_link.hash, url=first_link.url
                )
            )

        # TODO: Add an assert that checks if needs only are
        # in a singular module (not allowed to be in multiple)
        module_groups[module_key].needs.append(source_link)

    return [
        ModuleSourceLinks(module=group.module, needs=group.needs)
        for group in module_groups.values()
    ]


# # Pouplate Metadata
# # Since all metadata inside the Codelinks is the same
# # we can just arbitrarily grab the first one
# module_name=need_links.CodeLinks[0].module_name,
# hash=need_links.CodeLinks[0].hash,
# url=need_links.CodeLinks[0].url,
