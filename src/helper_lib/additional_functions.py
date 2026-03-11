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
from pathlib import Path

# Import types that depend on score_source_code_linker
from src.extensions.score_source_code_linker.needlinks import DefaultNeedLink, NeedLink
from src.extensions.score_source_code_linker.module_source_links import moduleInfo
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
    metadata: moduleInfo,
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
    metadata: moduleInfo,
    link: NeedLink | DataForTestLink | DataOfTestCase | None = None,
):
    if link is None:
        link = DefaultNeedLink()
    base_url = metadata.url
    current_hash = metadata.hash
    return f"{base_url}/blob/{current_hash}/{link.file}#L{link.line}"
