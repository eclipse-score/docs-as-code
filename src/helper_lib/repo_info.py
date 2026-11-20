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

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

LOCAL_REPO = "local_repo"

# Keys of the 'flat' form, in the order they appear in the JSON files.
REPO_FLAT_KEYS = ("repo_name", "hash", "url")


# order + unsafe_hash: the link dataclasses that hold a RepoInfo are
# ordered and hashed field by field, so RepoInfo has to support both.
@dataclass(order=True, unsafe_hash=True)
class RepoInfo:
    name: str
    hash: str
    url: str

    # The 'flat' form is how repo info appears on disk and on the link
    # dataclasses: the sourcelinks file header, the inline fields of
    # NeedLink / DataForTestLink / DataOfTestCase. There the name is
    # called 'repo_name'.
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
    return RepoInfo(name=LOCAL_REPO, hash="", url="")


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


def split_external_path(path: Path) -> tuple[str, Path]:
    """
    Split a Bazel exec path into the repo it belongs to and the path inside
    that repo.

    Combo build:
        external/score_docs_as_code+/src/helper_lib/test_helper_lib.py
        => ("score_docs_as_code", Path("src/helper_lib/test_helper_lib.py"))
    Local build (`//:docs`):
        src/helper_lib/test_helper_lib.py
        => (LOCAL_REPO, Path("src/helper_lib/test_helper_lib.py"))  # path unchanged
    """
    # Only a leading `external/` counts, so files / folders may still have
    # `external` somewhere else in their name.
    if not str(path).startswith("external/"):
        return LOCAL_REPO, path
    repo_dir, _, rest = str(path).removeprefix("external/").partition("/")
    # Bzlmod appends `+` to the canonical repo directory name.
    return repo_dir.removesuffix("+"), Path(rest)


def parse_repo_name_from_path(path: Path) -> str:
    """
    Parse out the Module-Name from the filename:
    Combo Example:
        Path: external/score_docs_as_code+/src/helper_lib/test_helper_lib.py
        => score_docs_as_code
    Local:
        Path: src/helper_lib/test_helper_lib.py
        => LOCAL_REPO (whatever the vars value is)

    """
    return split_external_path(path)[0]


def parse_info_from_known_good(
    known_good_json: Path, repo_name: str
) -> tuple[str, str]:
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
