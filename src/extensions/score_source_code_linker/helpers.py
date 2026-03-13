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

from src.extensions.score_source_code_linker.module_source_links import ModuleInfo

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


def get_github_link(
    metadata: ModuleInfo,
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
    metadata: ModuleInfo,
    link: NeedLink | DataForTestLink | DataOfTestCase | None = None,
):
    if link is None:
        link = DefaultNeedLink()
    base_url = metadata.url
    current_hash = metadata.hash
    return f"{base_url}/blob/{current_hash}/{link.file}#L{link.line}"


def parse_module_name_from_path(path: Path) -> str:
    """
    Parse out the Module-Name from the filename gotten
    /home/user/.cache/bazel/aksj37981712/external/score_docs_as_code+/src/tests/testfile.py
    => score_docs_as_code
    """

    # COMBO BUILD
    # If external is in the filepath that gets parsed =>
    # file is in an external module => combo build
    # Example Path:
    #   PosixPath('external/score_docs_as_code+/src/helper_lib/test_helper_lib.py'

    if str(path).startswith("external/"):
        # This allows for files / folders etc. to have `external` in their name too.
        module_raw = str(path).removeprefix("external/")
        filepath_split = str(module_raw).split("/", maxsplit=1)
        return str(filepath_split[0].removesuffix("+"))
    # We return this when we are in a local build `//:docs` the rest of DaC knows
    # What to do then if it encounters this module_name
    return "local_module"


def parse_info_from_known_good(
    known_good_json: Path, module_name: str
) -> tuple[str, str]:
    with open(known_good_json) as f:
        kg_json = json.load(f)
    for category in kg_json["modules"].values():
        if module_name in category:
            m = category[module_name]
            return (m["hash"], m["repo"].removesuffix(".git"))
    raise KeyError(f"Module {module_name!r} not found in known_good_json.")
