# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
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

import functools
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.helper_lib import (
    find_git_root,
    get_current_git_hash,
    get_github_base_url,
    ws_root_in_git_root,
)

# Keys of the 'flat' form, in the order they appear in the JSON files.
REPO_FLAT_KEYS = ("repo_name", "hash", "url")


# The link dataclasses that hold a RepoInfo are
# ordered and hashed field by field, so RepoInfo has to support both.
@dataclass(order=True, frozen=True)
class RepoInfo:
    name: str
    hash: str
    url: str

    # On-disk form, as used in the JSON files. The name is stored as 'repo_name'.
    def to_flat_dict(self) -> dict[str, str]:
        return {"repo_name": self.name, "hash": self.hash, "url": self.url}

    @staticmethod
    def is_flat_dict(x: object) -> bool:
        return isinstance(x, dict) and set(REPO_FLAT_KEYS) <= x.keys()

    @classmethod
    def from_flat_dict(cls, d: dict[str, Any]) -> "RepoInfo":
        if not cls.is_flat_dict(d):
            raise TypeError(
                f"Expected a dict with 'repo_name', 'hash' and 'url' keys, got: {d!r}"
            )
        return cls(name=d["repo_name"], hash=d["hash"], url=d["url"])


def DefaultRepoInfo() -> RepoInfo:
    return RepoInfo(name="", hash="", url="")


def flatten_repo_field(d: dict[str, Any], repo: RepoInfo | None) -> dict[str, Any]:
    """
    Replace the 'repo' entry of a dataclass dict with the flat repo keys.

    The flat keys take the place of 'repo', so the key order in the JSON
    stays the same as when the links had three loose fields.
    A missing repo (None) becomes three None values.
    """
    flat: dict[str, Any] = (
        repo.to_flat_dict() if repo is not None else dict.fromkeys(REPO_FLAT_KEYS)
    )
    result: dict[str, Any] = {}
    for key, value in d.items():
        if key == "repo":
            result.update(flat)
        else:
            result[key] = value
    return result


def split_repo_fields(d: dict[str, Any]) -> tuple[dict[str, Any], RepoInfo | None]:
    """
    Inverse of flatten_repo_field: take the flat repo keys out of a dict.

    Returns the remaining keys and the RepoInfo, or None if one of the
    three keys is missing or None.
    """
    rest = {key: value for key, value in d.items() if key not in REPO_FLAT_KEYS}
    name, hash_, url = (d.get(key) for key in REPO_FLAT_KEYS)
    if name is None or hash_ is None or url is None:
        return rest, None
    return rest, RepoInfo(name=name, hash=hash_, url=url)


def split_external_path(path: Path, *, local_module: str) -> tuple[str, Path]:
    """
    Split a Bazel exec path into the repo it belongs to and the path inside
    that repo.

    Combo build:
        external/score_docs_as_code+/src/helper_lib/test_helper_lib.py
        => ("score_docs_as_code", Path("src/helper_lib/test_helper_lib.py"))
    Local build (`//:docs`):
        src/helper_lib/test_helper_lib.py
        => (local_module, Path("src/helper_lib/test_helper_lib.py"))
    """
    # Only a leading `external/` counts, so files / folders may still have
    # `external` somewhere else in their name.
    if not str(path).startswith("external/"):
        return local_module, path
    repo_dir, _, rest = str(path).removeprefix("external/").partition("/")
    # Bzlmod appends `+` to the canonical repo directory name.
    return repo_dir.removesuffix("+"), Path(rest)


def load_known_good(known_good_json: Path) -> dict[str, Any]:
    """
    Read and check known_good.json. Load it once and pass the result to
    resolve_repo for every repo that needs a lookup.
    """
    with open(known_good_json) as f:
        kg_json: dict[str, Any] = json.load(f)

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
    return kg_json


def parse_info_from_known_good(
    known_good: dict[str, Any], repo_name: str
) -> tuple[str, str]:
    """Return (hash or version, url) of one repo from a loaded known_good.json."""
    for category in known_good["modules"].values():
        if repo_name in category:
            m = category[repo_name]
            hash_or_version = m.get("hash") or m.get("version")
            if hash_or_version is None:
                raise KeyError(
                    f"Module {repo_name} has neither 'hash' nor 'version' key."
                )
            return (hash_or_version, m["repo"].removesuffix(".git"))
    raise KeyError(f"Module {repo_name} not found in known_good_json.")


def resolve_repo(
    repo_name: str, known_good: dict[str, Any] | None, *, local_module: str
) -> RepoInfo | None:
    """Resolve the Git pin of a source link's or JUnit report's module.

    `repo_name` identifies the declaring module and `local_module` names the
    root module of the documentation build. `known_good` holds the loaded
    known_good.json, or None when the build has no such file.

    Return None when the build has no known-good file, the module name is
    empty, or the module is the root module. In those cases the caller keeps
    its existing repository metadata.
    A supplied known-good file must contain the external module's revision and
    repository URL. A missing entry or field raises KeyError.
    """
    # Without a known-good file there is no Git pin. The root module and
    # direct Sphinx builds (empty module name) use the checkout at render time.
    if not known_good or not repo_name or repo_name == local_module:
        return None

    # The consuming build supplies the Git pin for an external module.
    hash_or_version, url = parse_info_from_known_good(known_good, repo_name)
    return RepoInfo(name=repo_name, hash=hash_or_version, url=url)


#   ───────────────────────[ GitHub links ]───────────────────────

# Used when there is no real URL. Bazel sandbox builds and testcase Needs
# without a Git link use this placeholder.
PLACEHOLDER_URL = "https://github.com/placeholder/placeholder/blob/unknown"


def get_placeholder_github_link(file: Path | str | None, line: int | str | None) -> str:
    file = file if file is not None else "<placeholder_file>"
    line = line if line is not None else 1
    return f"{PLACEHOLDER_URL}/{file}#L{line}"


def get_github_link(
    repo: RepoInfo | None,
    file: Path | str | None,
    line: int | str | None,
    plain_links: bool = False,
    git_root: Path | None = None,
    *,
    local_module: str = "",
) -> str | None:
    """
    GitHub URL of a file, with a line anchor when a line is available.
    Checked in this order:
      1. plain_links (Bazel sandbox, no git) or repo is None (metadata
         incomplete): placeholder URL. A missing file / line becomes
         '<placeholder_file>' / 1.
      2. repo has a hash and URL (filled from known_good): URL from repo.
      3. Return None for an unpinned external module.
      4. Use the local git checkout for the root module or an empty repo name.
         Return None if the checkout has no remote.
    """
    if plain_links or repo is None:
        return get_placeholder_github_link(file, line)
    file_location = str(file) if line in (None, "") else f"{file}#L{line}"
    if repo.hash and repo.url:
        # Reference-integration path (mounted external documentation)
        return f"{repo.url}/blob/{repo.hash}/{file_location}"
    if repo.name and repo.name != local_module:
        # A link to an unpinned external module would point into the wrong
        # repository if it used the local checkout.
        return None

    # Local path (//:docs). The file is relative to the Bazel workspace, which
    # can sit below the Git root.
    try:
        blob_url = _git_blob_url(git_root or find_git_root() or Path())
    except AssertionError:
        return None
    return f"{blob_url}/{(ws_root_in_git_root() / file_location).as_posix()}"


@functools.cache
def _git_blob_url(git_root: Path) -> str:
    """
    '<github url>/blob/<HEAD hash>' of a local checkout, cached per git root.

    A failure (no remote) is not cached. clear_git_cache resets it every build.
    """
    return f"{get_github_base_url(git_root)}/blob/{get_current_git_hash(git_root)}"


def clear_git_cache() -> None:
    _git_blob_url.cache_clear()
