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
from typing import TypedDict


# Import types that depend on score_source_code_linker
from src.extensions.score_source_code_linker.needlinks import DefaultNeedLink, NeedLink
from src.extensions.score_source_code_linker.testlink import (
    DataForTestLink,
    DataOfTestCase,
)
from src.helper_lib import (
    find_git_root,
    get_current_git_hash,
    get_github_base_url,
)


class ModuleInfo(TypedDict):
    hash: str
    repo: str


def get_github_link(
    link: NeedLink | DataForTestLink | DataOfTestCase | None = None,
    known_json: dict[str, ModuleInfo] | None = None,
) -> str:
    if link is None:
        link = DefaultNeedLink()
    
    if known_json is not None and link.module is not None:
        # Using the parsed know_good json file as source of truth
        # We also have to check for link.module being not none as for example 'ref-int' could have links. 
        # And then we would not find them in the known_json and have to go the normal route
        module_info = known_json[link.module]
        current_hash = module_info["hash"]
        base_url = module_info["repo"].removesuffix('.git')
    else:
        # Fall back to git discovery for local links
        passed_git_root = find_git_root()
        if passed_git_root is None:
            passed_git_root = Path()
        base_url = get_github_base_url()
        current_hash = get_current_git_hash(passed_git_root)
    
    return f"{base_url}/blob/{current_hash}/{link.path}/{link.file}#L{link.line}"



def get_module_has_from_known_good_json(known_good_path: Path) -> dict[str, ModuleInfo]:
    with open(known_good_path) as f:
        known_good_json = json.load(f)  # pyright: ignore[reportAny] It's a nested json we do not know the final struct of
    modules: dict[str, ModuleInfo] = {}
    for category in known_good_json["modules"].values():  # pyright: ignore[reportAny] These should only be strings
        for module_name, module_data in category.items():  # pyright: ignore[reportAny] These should only be strings
            modules[module_name] = {
                "hash": module_data["hash"],
                "repo": module_data["repo"],
            }
    return modules
