from dataclasses import dataclass
from pathlib import Path
from typing import Any

import json

LOCAL_REPO = "local_repo"


@dataclass
class RepoInfo:
    name: str
    hash: str
    url: str


def DefaultRepoInfo() -> RepoInfo:
    return RepoInfo(name=LOCAL_REPO, hash="", url="")


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

    # COMBO BUILD

    if str(path).startswith("external/"):
        # This allows for files / folders etc. to have `external` in their name too.
        module_raw = str(path).removeprefix("external/")
        filepath_split = str(module_raw).split("/", maxsplit=1)
        return str(filepath_split[0].removesuffix("+"))
    # We return this when we are in a local build `//:docs` the rest of DaC knows
    return LOCAL_REPO


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
