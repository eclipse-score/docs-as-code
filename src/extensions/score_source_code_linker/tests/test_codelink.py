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
import os
import subprocess
import tempfile
from collections.abc import Generator
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest
from attribute_plugin import add_test_properties  # type: ignore[import-untyped]
from sphinx_needs.data import NeedsMutable

from src.extensions.score_metamodel.tests import need as test_need

# Import the module under test
# Note: You'll need to adjust these imports based on your actual module structure
from src.extensions.score_source_code_linker import (
    find_need,
    get_cache_filename,
    group_by_need,
)
from src.extensions.score_source_code_linker.needlinks import (
    NeedLink,
    load_source_code_links_json,
    store_source_code_links_json,
)
from src.helper_lib import (
    get_current_git_hash,
)
from src.helper_lib.additional_functions import get_github_link

"""
#          ────────────────ATTENTION───────────────

#          ╭──────────────────────────────────────╮
#          │                !!!!!                 │
#          │      BOILERPLATE TEST MADE VIA       │
#          │   GENERATION. NOT YET FULLY LOOKED   │
#          │               THROUGH                │
#          │                 !!!!                 │
#          ╰──────────────────────────────────────╯

"""


def encode_comment(s: str) -> str:
    return s.replace(" ", "-----", 1)


def decode_comment(s: str) -> str:
    return s.replace("-----", " ", 1)


class NeedLinkTestEncoder(json.JSONEncoder):
    def default(self, o: object):
        if isinstance(o, NeedLink):
            d = asdict(o)
            d["tag"] = encode_comment(d.get("tag", ""))
            d["full_line"] = encode_comment(d.get("full_line", ""))
            return d
        if isinstance(o, Path):
            return str(o)
        return super().default(o)


def needlink_test_decoder(d: dict[str, Any]) -> NeedLink | dict[str, Any]:
    if {"file", "line", "tag", "need", "full_line"} <= d.keys():
        return NeedLink(
            file=Path(d["file"]),
            line=d["line"],
            tag=decode_comment(d["tag"]),
            need=d["need"],
            full_line=decode_comment(d["full_line"]),
        )
    # It's something else, pass it on to other decoders
    return d


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def git_repo(temp_dir: Path) -> Path:
    """Create a real git repository for testing."""
    git_dir: Path = temp_dir / "test_repo"
    git_dir.mkdir()

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=git_dir, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"], cwd=git_dir, check=True
    )
    subprocess.run(["git", "config", "user.name", "Test User"], cwd=git_dir, check=True)

    # Create a test file and commit
    test_file: Path = git_dir / "test_file.py"
    test_file.write_text("# Test file\nprint('hello')\n")
    subprocess.run(["git", "add", "."], cwd=git_dir, check=True)
    subprocess.run(["git", "commit", "-m", "Initial commit"], cwd=git_dir, check=True)

    # Add a remote
    subprocess.run(
        ["git", "remote", "add", "origin", "git@github.com:test-user/test-repo.git"],
        cwd=git_dir,
        check=True,
    )
    return git_dir


@pytest.fixture
def sample_needlinks() -> list[NeedLink]:
    """Create sample NeedLink objects for testing."""
    return [
        NeedLink(
            file=Path("src/implementation1.py"),
            line=3,
            tag="#" + " req-Id:",
            need="TREQ_ID_1",
            full_line="#" + " req-Id: TREQ_ID_1",
        ),
        NeedLink(
            file=Path("src/implementation2.py"),
            line=3,
            tag="#" + " req-Id:",
            need="TREQ_ID_1",
            full_line="#" + " req-Id: TREQ_ID_1",
        ),
        NeedLink(
            file=Path("src/implementation1.py"),
            line=9,
            tag="#" + " req-Id:",
            need="TREQ_ID_2",
            full_line="#" + " req-Id: TREQ_ID_2",
        ),
        NeedLink(
            file=Path("src/bad_implementation.py"),
            line=2,
            tag="#" + " req-Id:",
            need="TREQ_ID_200",
            full_line="#" + " req-Id: TREQ_ID_200",
        ),
    ]


@pytest.fixture
def cache_file_with_links(temp_dir: Path, sample_needlinks: list[NeedLink]) -> Path:
    """Create a cache file with sample needlinks."""
    cache_file: Path = temp_dir / "cache.json"
    store_source_code_links_json(cache_file, sample_needlinks)
    return cache_file


@pytest.fixture
def sample_needs() -> dict[str, dict[str, str]]:
    """Create sample needs data for testing."""
    return {
        "TREQ_ID_1": {
            "id": "TREQ_ID_1",
            "source_code_link": "",
            "title": "Test requirement 1",
        },
        "TREQ_ID_2": {
            "id": "TREQ_ID_2",
            "source_code_link": "",
            "title": "Test requirement 2",
        },
        "TREQ_ID_3": {
            "id": "TREQ_ID_3",
            "source_code_link": "",
            "title": "Test requirement 3",
        },
    }


# Test utility functions
@add_test_properties(
    partially_verifies=["tool_req__docs_dd_link_source_code_link"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_get_cache_filename():
    """Test cache filename generation."""
    build_dir = Path("/tmp/build")
    expected = build_dir / "score_source_code_linker_cache.json"
    result = get_cache_filename(build_dir, "score_source_code_linker_cache.json")
    assert result == expected


def make_needs(needs_dict: dict[str, dict[str, Any]]) -> NeedsMutable:
    return NeedsMutable(
        {need_id: test_need(**params) for need_id, params in needs_dict.items()}
    )


@add_test_properties(
    partially_verifies=["tool_req__docs_dd_link_source_code_link"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_find_need_direct_match():
    """Test finding a need with direct ID match."""
    all_needs = make_needs(
        {
            "REQ_001": {"id": "REQ_001", "title": "Test requirement"},
            "REQ_002": {"id": "REQ_002", "title": "Another requirement"},
        }
    )
    result = find_need(all_needs, "REQ_001")
    assert result is not None
    assert result["id"] == "REQ_001"


@add_test_properties(
    partially_verifies=["tool_req__docs_dd_link_source_code_link"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_find_need_not_found():
    """Test finding a need that doesn't exist."""
    all_needs = make_needs(
        {
            "REQ_001": {"id": "REQ_001", "title": "Test requirement"},
        }
    )

    result = find_need(all_needs, "REQ_999")
    assert result is None


@add_test_properties(
    partially_verifies=["tool_req__docs_dd_link_source_code_link"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_group_by_need(sample_needlinks: list[NeedLink]) -> None:
    """Test grouping source code links by need ID."""
    result = group_by_need(sample_needlinks)

    # Check that the grouping is correct
    assert len(result) == 3
    for found_link in result:
        if found_link.need == "TREQ_ID_1":
            assert len(found_link.links.CodeLinks) == 2
            assert found_link.links.CodeLinks[0].file == Path("src/implementation1.py")
            assert found_link.links.CodeLinks[1].file == Path("src/implementation2.py")
        elif found_link.need == "TREQ_ID_2":
            assert len(found_link.links.CodeLinks) == 1
            assert found_link.links.CodeLinks[0].file == Path("src/implementation1.py")
            assert found_link.links.CodeLinks[0].line == 9
        elif found_link.need == "TREQ_ID_200":
            assert len(found_link.links.CodeLinks) == 1


@add_test_properties(
    partially_verifies=["tool_req__docs_dd_link_source_code_link"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_group_by_need_empty_list():
    """Test grouping empty list of needlinks."""
    result = group_by_need([], [])
    assert len(result) == 0


@add_test_properties(
    partially_verifies=["tool_req__docs_dd_link_source_code_link"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_get_github_link_with_real_repo(git_repo: Path) -> None:
    """Test generating GitHub link with real repository."""
    # Create a needlink
    needlink = NeedLink(
        file=Path("src/test.py"),
        line=42,
        tag="#" + " req-Id:",
        need="REQ_001",
        full_line="#" + " req-Id: REQ_001",
    )

    # Have to change directories in order to ensure that we get the right/any .git file
    os.chdir(Path(git_repo).absolute())
    result = get_github_link(needlink)

    # Should contain the base URL, hash, file path, and line number
    assert "https://github.com/test-user/test-repo/blob/" in result
    assert "src/test.py#L42" in result
    assert len(result.split("/")) >= 7  # Should have proper URL structure

    # Verify the hash is actually from the repo
    hash_from_link = result.split("/blob/")[1].split("/")[0]
    actual_hash = get_current_git_hash(git_repo)
    assert hash_from_link == actual_hash


# Test cache file operations
@add_test_properties(
    partially_verifies=["tool_req__docs_dd_link_source_code_link"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_cache_file_operations(
    temp_dir: Path, sample_needlinks: list[NeedLink]
) -> None:
    """Test storing and loading cache files."""
    cache_file: Path = temp_dir / "test_cache.json"

    # Store links
    store_source_code_links_json(cache_file, sample_needlinks)

    # Verify file was created
    assert cache_file.exists()

    # Load and verify links
    loaded_links = load_source_code_links_json(cache_file)

    assert len(loaded_links) == 4
    assert loaded_links[0].need == "TREQ_ID_1"
    assert loaded_links[1].need == "TREQ_ID_1"
    assert loaded_links[2].need == "TREQ_ID_2"
    assert loaded_links[3].need == "TREQ_ID_200"
    assert loaded_links[0].line == 3
    assert loaded_links[1].line == 3
    assert loaded_links[2].line == 9
    assert loaded_links[3].line == 2


@add_test_properties(
    partially_verifies=["tool_req__docs_dd_link_source_code_link"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_cache_file_with_encoded_comments(temp_dir: Path) -> None:
    """Test that cache file properly handles encoded comments."""
    # Create needlinks with spaces in tags and full_line
    needlinks = [
        NeedLink(
            file=Path("src/test.py"),
            line=1,
            tag="#" + " req-Id:",
            need="TEST_001",
            full_line="#" + " req-Id: TEST_001",
        )
    ]

    cache_file: Path = temp_dir / "encoded_cache.json"
    store_source_code_links_json(cache_file, needlinks)

    # Check the raw JSON to verify encoding
    with open(cache_file) as f:
        raw_content = f.read()
        assert "#" + " req-Id:" in raw_content  # Should be encoded
        assert "#-----req-Id:" not in raw_content  # Original should not be present

    # Load and verify decoding
    loaded_links = load_source_code_links_json(cache_file)
    assert len(loaded_links) == 1
    assert loaded_links[0].tag == "#" + " req-Id:"  # Should be decoded back
    assert loaded_links[0].full_line == "#" + " req-Id: TEST_001"


# Integration tests


@add_test_properties(
    partially_verifies=["tool_req__docs_dd_link_source_code_link"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_group_by_need_and_find_need_integration(
    sample_needlinks: list[NeedLink],
) -> None:
    """Test grouping links and finding needs together."""
    # Group the test links
    grouped = group_by_need(sample_needlinks)

    # Create mock needs
    all_needs = make_needs(
        {
            "TREQ_ID_1": {"id": "TREQ_ID_1", "title": "Test requirement 1"},
            "TREQ_ID_2": {"id": "TREQ_ID_2", "title": "Test requirement 2"},
        }
    )

    # Test finding needs for each group
    for found_link in grouped:
        found_need = find_need(all_needs, found_link.need)
        if found_link.need in ["TREQ_ID_1", "TREQ_ID_2"]:
            assert found_need is not None
            assert found_need["id"] == found_link.need


@add_test_properties(
    partially_verifies=["tool_req__docs_dd_link_source_code_link"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_source_linker_end_to_end_with_real_files(
    temp_dir: Path, git_repo: Path
) -> None:
    """Test end-to-end workflow with real files and git repo."""
    # Create source files with requirement IDs
    src_dir: Path = git_repo / "src"
    src_dir.mkdir()

    (src_dir / "implementation1.py").write_text(
        """
# Some implementation
#"""
        + """ req-Id: TREQ_ID_1
def function1():
    pass

# Another function
#"""
        + """ req-Id: TREQ_ID_2
def function2():
    pass
"""
    )

    (src_dir / "implementation2.py").write_text(
        """
# Another implementation
#"""
        + """ req-Id: TREQ_ID_1
def another_function():
    pass
"""
    )

    # Commit the changes
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True)
    subprocess.run(
        ["git", "commit", "-m", "Add implementation files"], cwd=git_repo, check=True
    )

    # Create needlinks manually
    # (simulating what generate_source_code_links_json would do)
    needlinks = [
        NeedLink(
            file=Path("src/implementation1.py"),
            line=3,
            tag="#" + " req-Id:",
            need="TREQ_ID_1",
            full_line="#" + " req-Id: TREQ_ID_1",
        ),
        NeedLink(
            file=Path("src/implementation1.py"),
            line=8,
            tag="#" + " req-Id:",
            need="TREQ_ID_2",
            full_line="#" + " req-Id: TREQ_ID_2",
        ),
        NeedLink(
            file=Path("src/implementation2.py"),
            line=3,
            tag="#" + " req-Id:",
            need="TREQ_ID_1",
            full_line="#" + " req-Id: TREQ_ID_1",
        ),
    ]

    # Test cache operations
    cache_file: Path = temp_dir / "cache.json"
    store_source_code_links_json(cache_file, needlinks)
    loaded_links = load_source_code_links_json(cache_file)

    assert len(loaded_links) == 3

    # Test grouping
    grouped = group_by_need(loaded_links)
    for found_links in grouped:
        if found_links.need == "TREQ_ID_1":
            assert len(found_links.links.CodeLinks) == 2
            assert len(found_links.links.TestLinks) == 0
        if found_links.need == "TREQ_ID_2":
            assert len(found_links.links.CodeLinks) == 1
            assert len(found_links.links.TestLinks) == 0

    # Test GitHub link generation
    # Have to change directories in order to ensure that we get the right/any .git file
    os.chdir(Path(git_repo).absolute())
    for needlink in loaded_links:
        github_link = get_github_link(needlink)
        assert "https://github.com/test-user/test-repo/blob/" in github_link
        assert f"src/{needlink.file.name}#L{needlink.line}" in github_link


@add_test_properties(
    partially_verifies=["tool_req__docs_dd_link_source_code_link"],
    test_type="requirements-based",
    derivation_technique="requirements-analysis",
)
def test_multiple_commits_hash_consistency(git_repo: Path) -> None:
    """Test that git hash remains consistent and links update properly."""
    # Get initial hash
    initial_hash = get_current_git_hash(git_repo)

    # Create and commit a new file
    new_file: Path = git_repo / "new_file.py"
    new_file.write_text("# New file\nprint('new')")
    subprocess.run(["git", "add", "."], cwd=git_repo, check=True)
    subprocess.run(["git", "commit", "-m", "Add new file"], cwd=git_repo, check=True)

    # Get new hash
    new_hash = get_current_git_hash(git_repo)

    # Hashes should be different
    assert initial_hash != new_hash
    assert len(new_hash) == 40

    # Test that links use the current hash
    needlink = NeedLink(
        file=Path("new_file.py"),
        line=1,
        tag="#" + " req-Id:",
        need="TEST_001",
        full_line="#" + " req-Id: TREQ_ID_1",
    )

    os.chdir(Path(git_repo).absolute())
    github_link = get_github_link(needlink)
    assert new_hash in github_link
