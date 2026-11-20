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

# Used when there is no real URL: Bazel sandbox builds (plain links) and
# testcases without repo metadata.
PLACEHOLDER_URL = "https://github.com/placeholder/placeholder/blob/unknown"

Link = NeedLink | DataForTestLink | DataOfTestCase


def get_github_link(
    repo: RepoInfo | None,
    link: Link | None = None,
    git_root: Path | None = None,
    plain_links: bool = False,
) -> str | None:
    """
    The one place that decides the GitHub URL of a link.

    Outcomes, in order:
      1. plain_links (Bazel sandbox, no git) or repo is None (metadata
         incomplete): placeholder URL.
      2. repo.hash is set (combo build, filled from known_good): URL from repo.
      3. Otherwise (local build): URL from the local git checkout.
      4. The local git checkout has no remote: None. The caller decides the
         fallback.

    The label part ('<>name<>result' etc.) belongs to the callers.
    """
    if link is None:
        link = DefaultNeedLink()
    if plain_links or repo is None:
        file = link.file if link.file is not None else "<placeholder_file>"
        line = link.line if link.line is not None else 1
        return f"{PLACEHOLDER_URL}/{file}#L{line}"
    if repo.hash:
        # Reference-integration path (mounted external documentation)
        return get_github_link_from_json(repo, link)
    # Local path (//:docs)
    try:
        return get_github_link_from_git(git_root or find_git_root() or Path(), link)
    except AssertionError:
        return None


def get_github_link_from_git(
    git_root: Path,
    link: Link | None = None,
) -> str:
    if link is None:
        link = DefaultNeedLink()
    base_url = get_github_base_url(git_root)
    current_hash = get_current_git_hash(git_root)
    return f"{base_url}/blob/{current_hash}/{link.file}#L{link.line}"


def get_github_link_from_json(
    metadata: RepoInfo,
    link: Link | None = None,
) -> str:
    if link is None:
        link = DefaultNeedLink()
    base_url = metadata.url
    current_hash = metadata.hash
    return f"{base_url}/blob/{current_hash}/{link.file}#L{link.line}"
