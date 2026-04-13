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

# Import types that depend on score_source_code_linker
from src.extensions.score_source_code_linker.needlinks import DefaultNeedLink, NeedLink
from src.extensions.score_source_code_linker.repo_source_links import RepoInfo
from src.extensions.score_source_code_linker.testlink import (
    DataForTestLink,
    DataOfTestCase,
)
from src.helper_lib import (
    find_git_root,
    get_current_git_hash,
    get_github_base_url,
)


def get_github_link(
    metadata: RepoInfo,
    link: NeedLink | DataForTestLink | DataOfTestCase | None = None,
) -> str:
    if link is None:
        link = DefaultNeedLink()
    if not metadata.hash:
        # Local path (//:docs)
        return get_github_link_from_git(link)
    # Ref-Integration path (//:docs_combo..)
    return get_github_link_from_json(metadata, link)


def get_github_link_from_git(
    link: NeedLink | DataForTestLink | DataOfTestCase | None = None,
) -> str:
    if link is None:
        link = DefaultNeedLink()
    passed_git_root = find_git_root()
    if passed_git_root is None:
        passed_git_root = Path()
    base_url = get_github_base_url()
    current_hash = get_current_git_hash(passed_git_root)
    return f"{base_url}/blob/{current_hash}/{link.file}#L{link.line}"


def get_github_link_from_json(
    metadata: RepoInfo,
    link: NeedLink | DataForTestLink | DataOfTestCase | None = None,
) -> str:
    if link is None:
        link = DefaultNeedLink()
    base_url = metadata.url
    current_hash = metadata.hash
    return f"{base_url}/blob/{current_hash}/{link.file}#L{link.line}"


def parse_repo_name_from_path(path: Path) -> str:
    """
    Parse out the Module-Name from the filename:
    Combo Example:
        Path: external/score_docs_as_code+/src/helper_lib/test_helper_lib.py
        => score_docs_as_code
    Local:
        Path: src/helper_lib/test_helper_lib.py
        => local_repo

    """

    # COMBO BUILD

    if str(path).startswith("external/"):
        # This allows for files / folders etc. to have `external` in their name too.
        module_raw = str(path).removeprefix("external/")
        filepath_split = str(module_raw).split("/", maxsplit=1)
        return str(filepath_split[0].removesuffix("+"))
    # We return this when we are in a local build `//:docs` the rest of DaC knows
    return "local_repo"


def parse_info_from_known_good(
    known_good_json: Path, repo_name: str
) -> tuple[str, str]:
    with open(known_good_json) as f:
        kg_json = json.load(f)

    #   ───────[ Assert our worldview that has to exist here ]─────
    assert kg_json, (
        f"Known good json at: {known_good_json} is empty. This is not allowed"
    )
    assert "modules" in kg_json, (
        f"Known good json at: {known_good_json} is missing the 'modules' key"
    )
    assert kg_json["modules"], (
        f"Known good json at: {known_good_json} has an empty 'modules' dictionary"
    )

    for category in kg_json["modules"].values():
        if repo_name in category:
            m = category[repo_name]
            hash_or_version = m.get("hash") or m.get("version")
            if hash_or_version is None:
                raise KeyError(
                    f"Module {repo_name} has neither 'hash' nor 'version' key."
                )
            return (hash_or_version, m["repo"].removesuffix(".git"))
    raise KeyError(f"Module {repo_name} not found in known_good_json.")
