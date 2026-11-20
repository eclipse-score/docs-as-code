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

from src.extensions.score_source_code_linker.testlink import (
    DataForTestLink,
    DataOfTestCase,
)
from src.helper_lib import (
    find_git_root,
    get_current_git_hash,
    get_github_base_url,
)

# Import types that depend on score_source_code_linker
from src.helper_lib.needlinks import DefaultNeedLink, NeedLink
from src.helper_lib.repo_info import RepoInfo


def get_github_link(
    metadata: RepoInfo,
    link: NeedLink | DataForTestLink | DataOfTestCase | None = None,
    git_root: Path | None = None,
) -> str:
    """
    Get GitHub link for a file and line number using git information from the local repository.

    Args:
        git_root: Optional path to the git repository root. If not provided, it will be auto-detected.
    """
    if link is None:
        link = DefaultNeedLink()
    if not metadata.hash:
        if not git_root:
            git_root = find_git_root() or Path()
        # Local path (//:docs)
        return get_github_link_from_git(git_root, link)
    # Reference-integration path (mounted external documentation)
    return get_github_link_from_json(metadata, link)


def get_github_link_from_git(
    git_root: Path,
    link: NeedLink | DataForTestLink | DataOfTestCase | None = None,
) -> str:
    if link is None:
        link = DefaultNeedLink()
    base_url = get_github_base_url(git_root)
    current_hash = get_current_git_hash(git_root)
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
