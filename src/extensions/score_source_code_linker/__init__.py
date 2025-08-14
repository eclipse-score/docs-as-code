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

"""In this file the actual sphinx extension is defined. It will read pre-generated
source code links from a JSON file and add them to the needs.
"""

import subprocess
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import cast

from sphinx.application import Sphinx
from sphinx.config import Config
from sphinx.environment import BuildEnvironment
from sphinx_needs.data import NeedsInfoType, NeedsMutable, SphinxNeedsData
from sphinx_needs.logging import get_logger

from src.extensions.score_source_code_linker.generate_source_code_links_json import (
    find_git_root,
    find_ws_root,
    generate_source_code_links_json,
)
from src.extensions.score_source_code_linker.needlinks import (
    DefaultNeedLink,
    NeedLink,
    load_source_code_links_json,
)

LOGGER = get_logger(__name__)
# Outcomment this to enable more verbose logging
# LOGGER.setLevel("DEBUG")


def get_cache_filename(build_dir: Path) -> Path:
    """
    Returns the path to the cache file for the source code linker.
    This is used to store the generated source code links.
    """
    return build_dir / "score_source_code_linker_cache.json"


def setup_once(app: Sphinx, config: Config):
    # might be the only way to solve this?
    if "skip_rescanning_via_source_code_linker" in app.config:
        return
    LOGGER.debug(f"DEBUG: Workspace root is {find_ws_root()}")
    LOGGER.debug(
        f"DEBUG: Current working directory is {Path('.')} = {Path('.').resolve()}"
    )
    LOGGER.debug(f"DEBUG: Git root is {find_git_root()}")

    # Run only for local files!
    # ws_root is not set when running on external repositories (dependencies).
    ws_root = find_ws_root()
    if not ws_root:
        return

    # When BUILD_WORKSPACE_DIRECTORY is set, we are inside a git repository.
    assert find_git_root(ws_root)

    # Extension: score_source_code_linker
    app.add_config_value(
        "skip_rescanning_via_source_code_linker",
        False,
        rebuild="env",
        types=bool,
        description="Skip rescanning source code files via the source code linker.",
    )

    # Define need_string_links here to not have it in conf.py
    app.config.needs_string_links = {
        "source_code_linker": {
            "regex": r"(?P<url>.+)<>(?P<name>.+)",
            "link_url": "{{url}}",
            "link_name": "{{name}}",
            "options": ["source_code_link"],
        },
    }

    cache_json = get_cache_filename(Path(app.outdir))

    if not cache_json.exists() or not app.config.skip_rescanning_via_source_code_linker:
        LOGGER.debug(
            "INFO: Generating source code links JSON file.",
            type="score_source_code_linker",
        )

        generate_source_code_links_json(ws_root, cache_json)

    app.connect("env-updated", inject_links_into_needs)


def setup(app: Sphinx) -> dict[str, str | bool]:
    # Esbonio will execute setup() on every iteration.
    # setup_once will only be called once.
    setup_once(app, app.config)

    return {
        "version": "0.1",
        "parallel_read_safe": True,
        "parallel_write_safe": True,
    }


def find_need(
    all_needs: NeedsMutable, id: str, prefixes: list[str]
) -> NeedsInfoType | None:
    """
    Checks all possible external 'prefixes' for an ID
    So that the linker can add the link to the correct NeedsInfoType object.
    """
    if id in all_needs:
        return all_needs[id]

    # Try all possible prefixes
    for prefix in prefixes:
        prefixed_id = f"{prefix}{id}"
        if prefixed_id in all_needs:
            return all_needs[prefixed_id]

    return None


def group_by_need(source_code_links: list[NeedLink]) -> dict[str, list[NeedLink]]:
    """
    Groups the given need links by their need ID.
    """
    source_code_links_by_need: dict[str, list[NeedLink]] = defaultdict(list)
    for needlink in source_code_links:
        source_code_links_by_need[needlink.need].append(needlink)
    return source_code_links_by_need


def parse_git_output(str_line: str) -> str:
    if len(str_line.split()) < 2:
        LOGGER.warning(
            "Got wrong input line from 'get_github_repo_info'. "
            f"Input: {str_line}."
            "Expected example: 'origin git@github.com:user/repo.git'"
        )
        return ""
    url = str_line.split()[1]  # Get the URL part
    # Handle SSH format (git@github.com:user/repo.git)
    if url.startswith("git@"):
        path = url.split(":")[1]
    else:
        path = "/".join(url.split("/")[3:])  # Get part after github.com/
    return path.replace(".git", "")


def get_github_repo_info(git_root_cwd: Path) -> str:
    process = subprocess.run(
        ["git", "remote", "-v"], capture_output=True, text=True, cwd=git_root_cwd
    )
    repo = ""
    for line in process.stdout.split("\n"):
        if "origin" in line and "(fetch)" in line:
            repo = parse_git_output(line)
            break
    else:
        # If we do not find 'origin' we just take the first line
        LOGGER.info(
            "Did not find origin remote name. "
            "Will now take first result from: 'git remote -v'"
        )
        repo = parse_git_output(process.stdout.split("\n")[0])
    assert repo != "", (
        "Remote repository is not defined. Make sure you have a remote set. "
        "Check this via 'git remote -v'"
    )
    return repo


def get_git_root(git_root: Path = Path()) -> Path:
    # This is kinda ugly, doing this to reduce type errors.
    # There might be a nicer way to do this
    if git_root == Path():
        passed_git_root = find_git_root()
        if passed_git_root is None:
            return Path()
    else:
        passed_git_root = git_root
    return passed_git_root


def get_github_base_url(git_root: Path = Path()) -> str:
    passed_git_root = get_git_root(git_root)
    repo_info = get_github_repo_info(passed_git_root)
    return f"https://github.com/{repo_info}"


def get_github_link(
    git_root: Path = Path(), needlink: NeedLink = DefaultNeedLink()
) -> str:
    passed_git_root = get_git_root(git_root)
    base_url = get_github_base_url(
        passed_git_root
    )  # Pass git_root to avoid double lookup
    current_hash = get_current_git_hash(passed_git_root)
    return f"{base_url}/blob/{current_hash}/{needlink.file}#L{needlink.line}"


def get_current_git_hash(ws_root: Path) -> str:
    try:
        result = subprocess.run(
            ["git", "log", "-n", "1", "--pretty=format:%H"],
            cwd=ws_root,
            capture_output=True,
            check=True,
        )
        decoded_result = result.stdout.strip().decode()

        assert all(c in "0123456789abcdef" for c in decoded_result)
        return decoded_result
    except Exception as e:
        LOGGER.warning(f"Unexpected error: {ws_root}", exc_info=e)
        raise


# req-Id: tool_req__docs_dd_link_source_code_link
def inject_links_into_needs(app: Sphinx, env: BuildEnvironment) -> None:
    """
    'Main' function that facilitates the running of all other functions
    in correct order.
    This function is also 'connected' to the message Sphinx emits,
    therefore the one that's called directly.
    Args:
        env: Buildenvironment, this is filled automatically
        app: Sphinx app application, this is filled automatically
    """

    ws_root = find_ws_root()
    assert ws_root

    Needs_Data = SphinxNeedsData(env)
    needs = Needs_Data.get_needs_mutable()
    needs_copy = deepcopy(
        needs
    )  # TODO: why do we create a copy? Can we also needs_copy = needs[:]? copy(needs)?

    for _, need in needs.items():
        if need.get("source_code_link"):
            LOGGER.debug(
                f"?? Need {need['id']} already has source_code_link: "
                f"{need.get('source_code_link')}"
            )

    source_code_links = load_source_code_links_json(get_cache_filename(app.outdir))

    # group source_code_links by need
    # groupby requires the input to be sorted by the key

    source_code_links_by_need = group_by_need(source_code_links)

    # For some reason the prefix 'sphinx_needs internally' is CAPSLOCKED.
    # So we have to make sure we uppercase the prefixes
    prefixes = [x["id_prefix"].upper() for x in app.config.needs_external_needs]
    for need_id, needlinks in source_code_links_by_need.items():
        need = find_need(needs_copy, need_id, prefixes)
        if need is None:
            # TODO: print github annotations as in https://github.com/eclipse-score/bazel_registry/blob/7423b9996a45dd0a9ec868e06a970330ee71cf4f/tools/verify_semver_compatibility_level.py#L126-L129
            for n in needlinks:
                LOGGER.warning(
                    f"{n.file}:{n.line}: Could not find {need_id} in documentation",
                    type="score_source_code_linker",
                )
        else:
            need_as_dict = cast(dict[str, object], need)

            need_as_dict["source_code_link"] = ", ".join(
                f"{get_github_link(ws_root, n)}<>{n.file}:{n.line}" for n in needlinks
            )

            # NOTE: Removing & adding the need is important to make sure
            # the needs gets 're-evaluated'.
            Needs_Data.remove_need(need["id"])
            Needs_Data.add_need(need)

    # source_code_link of affected needs was overwritten.
    # Make sure it's empty in all others!
    for need in needs.values():
        if need["id"] not in source_code_links_by_need:
            need["source_code_link"] = ""
