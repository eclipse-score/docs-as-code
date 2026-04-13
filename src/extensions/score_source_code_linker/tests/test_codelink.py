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

# ╓                                                          ╖
# ║ Some portions created by Co-Pilot                        ║
# ╙                                                          ╜

import json
import os
import subprocess
import tempfile
from collections.abc import Generator
from dataclasses import asdict
from pathlib import Path
from typing import Any

import pytest

# S-CORE plugin to allow for properties/attributes in xml
# Enables Testlinking
from sphinx_needs.data import NeedsInfoType, NeedsMutable
from sphinx_needs.need_item import (
    NeedItem,
    NeedItemSourceUnknown,
    NeedsContent,
)

from src.extensions.score_source_code_linker import (
    find_need,
    get_cache_filename,
    group_by_need,
)
from src.extensions.score_source_code_linker.helpers import (
    get_github_link,
)
from src.extensions.score_source_code_linker.needlinks import (
    MetaData,
    NeedLink,
    NeedLinkEncoder,
    is_metadata,
    load_source_code_links_json,
    load_source_code_links_with_metadata_json,
    needlink_decoder,
    store_source_code_links_json,
    store_source_code_links_with_metadata_json,
)
from src.extensions.score_source_code_linker.repo_source_links import RepoInfo
from src.helper_lib import (
    get_current_git_hash,
)


def test_need(**kwargs: Any) -> NeedItem:
    """Convenience function to create a NeedItem object with some defaults."""

    kwargs.setdefault("id", "test_need")
    kwargs.setdefault("type", "requirement")
    kwargs.setdefault("title", "")
    kwargs.setdefault("status", None)
    kwargs.setdefault("tags", [])
    kwargs.setdefault("collapse", False)
    kwargs.setdefault("hide", False)
    kwargs.setdefault("layout", None)
    kwargs.setdefault("style", None)
    kwargs.setdefault("external_css", "")
    kwargs.setdefault("type_name", "")
    kwargs.setdefault("type_prefix", "")
    kwargs.setdefault("type_color", "")
    kwargs.setdefault("type_style", "")
    kwargs.setdefault("constraints", [])
    kwargs.setdefault("arch", {})
    kwargs.setdefault("sections", ())
    kwargs.setdefault("signature", None)
    kwargs.setdefault("has_dead_links", False)
    kwargs.setdefault("has_forbidden_dead_links", False)

    # Create source
    source = NeedItemSourceUnknown(
        docname=kwargs.get("docname", "docname"),
        lineno=kwargs.get("lineno", 42),
        lineno_content=kwargs.get("lineno_content"),
    )

    # Create content
    content = NeedsContent(
        doctype=kwargs.get("doctype", ".rst"),
        content=kwargs.get("content", ""),
        pre_content=kwargs.get("pre_content"),
        post_content=kwargs.get("post_content"),
    )
    return NeedItem(
        source=source,
        content=content,
        core=NeedsInfoType(**kwargs),
        extras={},
        links={},
    )


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
    """
    Since we have our own decoder, we have to ensure it works as expected
    """
    if {
        "file",
        "line",
        "tag",
        "need",
        "full_line",
        "repo_name",
        "hash",
        "url",
    } <= d.keys():
        return NeedLink(
            file=Path(d["file"]),
            line=d["line"],
            tag=decode_comment(d["tag"]),
            need=d["need"],
            full_line=decode_comment(d["full_line"]),
            repo_name=d.get("repo_name", ""),
            hash=d.get("hash", ""),
            url=d.get("url", ""),
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
            repo_name="local_repo",
            hash="",
            url="",
        ),
        NeedLink(
            file=Path("src/implementation2.py"),
            line=3,
            tag="#" + " req-Id:",
            need="TREQ_ID_1",
            full_line="#" + " req-Id: TREQ_ID_1",
            repo_name="local_repo",
            hash="",
            url="",
        ),
        NeedLink(
            file=Path("src/implementation1.py"),
            line=9,
            tag="#" + " req-Id:",
            need="TREQ_ID_2",
            full_line="#" + " req-Id: TREQ_ID_2",
            repo_name="local_repo",
            hash="",
            url="",
        ),
        NeedLink(
            file=Path("src/bad_implementation.py"),
            line=2,
            tag="#" + " req-Id:",
            need="TREQ_ID_200",
            full_line="#" + " req-Id: TREQ_ID_200",
            repo_name="local_repo",
            hash="",
            url="",
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


def test_get_cache_filename():
    """Test cache filename generation."""
    build_dir = Path("/tmp/build")
    expected = build_dir / "score_source_code_linker_cache.json"
    result = get_cache_filename(build_dir, "score_source_code_linker_cache.json")
    assert result == expected


# Done to appease the LSP Gods
def make_needs(needs_dict: dict[str, dict[str, Any]]) -> NeedsMutable:
    return NeedsMutable(
        {need_id: test_need(**params) for need_id, params in needs_dict.items()}
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


def test_find_need_not_found():
    """Test finding a need that doesn't exist."""
    all_needs = make_needs(
        {
            "REQ_001": {"id": "REQ_001", "title": "Test requirement"},
        }
    )

    result = find_need(all_needs, "REQ_999")
    assert result is None


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


def test_group_by_need_empty_list():
    """Test grouping empty list of needlinks."""
    result = group_by_need([], [])
    assert len(result) == 0


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
            repo_name="local_repo",
            hash="",
            url="",
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


def test_source_linker_end_to_end_with_real_files(
    temp_dir: Path, git_repo: Path
) -> None:
    """Test end-to-end workflow with real files and git repo."""
    # Create source files with requirement IDs
    src_dir: Path = git_repo / "src"
    src_dir.mkdir()

    _ = (src_dir / "implementation1.py").write_text(
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

    _ = (src_dir / "implementation2.py").write_text(
        """
# Another implementation
#"""
        + """ req-Id: TREQ_ID_1
def another_function():
    pass
"""
    )

    # Commit the changes
    _ = subprocess.run(["git", "add", "."], cwd=git_repo, check=True)
    _ = subprocess.run(
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
            repo_name="local_repo",
            hash="",
            url="",
        ),
        NeedLink(
            file=Path("src/implementation1.py"),
            line=8,
            tag="#" + " req-Id:",
            need="TREQ_ID_2",
            full_line="#" + " req-Id: TREQ_ID_2",
            repo_name="local_repo",
            hash="",
            url="",
        ),
        NeedLink(
            file=Path("src/implementation2.py"),
            line=3,
            tag="#" + " req-Id:",
            need="TREQ_ID_1",
            full_line="#" + " req-Id: TREQ_ID_1",
            repo_name="local_repo",
            hash="",
            url="",
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
    metadata = RepoInfo(name="local_repo", hash="", url="")
    for needlink in loaded_links:
        github_link = get_github_link(metadata, needlink)
        assert "https://github.com/test-user/test-repo/blob/" in github_link
        assert f"src/{needlink.file.name}#L{needlink.line}" in github_link


def test_multiple_commits_hash_consistency(git_repo: Path) -> None:
    """Test that git hash remains consistent and links update properly."""
    # Get initial hash
    initial_hash = get_current_git_hash(git_repo)

    # Create and commit a new file
    new_file: Path = git_repo / "new_file.py"
    _ = new_file.write_text("# New file\nprint('new')")
    _ = subprocess.run(["git", "add", "."], cwd=git_repo, check=True)
    _ = subprocess.run(
        ["git", "commit", "-m", "Add new file"], cwd=git_repo, check=True
    )

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

    metadata = RepoInfo(name="local_repo", hash="", url="")
    os.chdir(Path(git_repo).absolute())
    github_link = get_github_link(metadata, needlink)
    assert new_hash in github_link


def test_is_metadata_missing_keys():
    """Bad path: Dict missing required keys returns False"""
    incomplete = {"repo_name": "test", "hash": "abc"}
    assert is_metadata(incomplete) is False


#            ─────────────────[ NeedLink Dataclass Tests ]─────────────────


def test_needlink_to_dict_without_metadata():
    """to_dict_without_metadata should return NeedLink without metadata"""
    needlink = NeedLink(
        file=Path("src/test.py"),
        line=10,
        tag="#" + " req-Id:",
        need="REQ_1",
        full_line="#" + " req-Id: REQ_1",
        repo_name="test_repo",
        url="https://github.com/test/repo",
        hash="abc123",
    )
    result = needlink.to_dict_without_metadata()

    assert "repo_name" not in result
    assert "hash" not in result
    assert "url" not in result
    assert result["need"] == "REQ_1"
    assert result["line"] == 10


def test_needlink_to_dict_full():
    """to_dict_full includes all fields"""
    needlink = NeedLink(
        file=Path("src/test.py"),
        line=10,
        tag="#" + " req-Id:",
        need="REQ_1",
        full_line="#" + " req-Id: REQ_1",
        repo_name="test_repo",
        url="https://github.com/test/repo",
        hash="abc123",
    )
    result = needlink.to_dict_full()

    assert result["repo_name"] == "test_repo"
    assert result["hash"] == "abc123"
    assert result["url"] == "https://github.com/test/repo"
    assert result["need"] == "REQ_1"


#            ────────────────────[ JSON Encoder Tests ]────────────────────


def test_needlink_encoder_includes_metadata():
    """Encoder includes all fields"""
    encoder = NeedLinkEncoder()
    needlink = NeedLink(
        file=Path("src/test.py"),
        line=10,
        tag="#" + " req-Id:",
        need="REQ_1",
        full_line="#" + " req-Id: REQ_1",
        repo_name="test_repo",
        url="https://github.com/test/repo",
        hash="abc123",
    )
    result = encoder.default(needlink)

    assert isinstance(result, dict)
    assert result["repo_name"] == "test_repo"
    assert result["hash"] == "abc123"
    assert result["url"] == "https://github.com/test/repo"


# ============================================================================
# JSON Decoder Tests
# ============================================================================


def test_needlink_decoder_with_all_fields():
    """Decoder reconstructs NeedLink with all fields"""
    json_data: dict[str, Any] = {
        "file": "src/test.py",
        "line": 10,
        "tag": "#" + " req-Id:",
        "need": "REQ_1",
        "full_line": "#" + " req-Id: REQ_1",
        "repo_name": "test_repo",
        "hash": "abc123",
        "url": "https://github.com/test/repo",
    }
    result = needlink_decoder(json_data)

    assert isinstance(result, NeedLink)
    assert result.file == Path("src/test.py")
    assert result.line == 10
    assert result.repo_name == "test_repo"


def test_needlink_decoder_non_needlink_dict():
    """Edge case: Non-NeedLink dict is returned unchanged"""
    json_data = {"some": "other", "data": "structure"}
    result = needlink_decoder(json_data)
    assert result == json_data


#            ───────────────[ Testing Encoding / Decoding ]─────────────


def test_load_validates_list_type(tmp_path: Path):
    """Bad path: Non-list JSON fails validation"""
    test_file = tmp_path / "not_list.json"
    _ = test_file.write_text('{"file": "src/test.py", "line": 1}')

    with pytest.raises(AssertionError, match="should be a list"):
        load_source_code_links_json(test_file)


def test_load_validates_all_items_are_needlinks(tmp_path: Path):
    """Bad path: List with invalid items fails validation"""
    test_file = tmp_path / "invalid_items.json"
    _ = test_file.write_text('[{"invalid": "item"}]')

    with pytest.raises(AssertionError, match="should be NeedLink objects"):
        load_source_code_links_json(test_file)


# Adding additional tests to test the metadata stuff (excluding it if wanted)


def test_store_and_load_with_metadata(tmp_path: Path):
    """Happy path: Store with metadata dict and load correctly"""
    metadata: MetaData = {
        "repo_name": "external_repo",
        "hash": "commit_xyz",
        "url": "https://github.com/external/repo",
    }
    needlinks = [
        NeedLink(
            file=Path("src/impl.py"),
            line=10,
            tag="#" + " req-Id:",
            need="REQ_1",
            full_line="#" + " req-Id: REQ_1",
            repo_name="",  # Will be filled from metadata
            url="",
            hash="",
        ),
        NeedLink(
            file=Path("src/impl2.py"),
            line=20,
            tag="#" + " req-Id:",
            need="REQ_2",
            full_line="#" + " req-Id: REQ_2",
            repo_name="",
            url="",
            hash="",
        ),
    ]

    test_file = tmp_path / "with_metadata.json"
    store_source_code_links_with_metadata_json(test_file, metadata, needlinks)
    loaded = load_source_code_links_with_metadata_json(test_file)

    assert len(loaded) == 2
    # Verify metadata was applied to all links
    for nl in loaded:
        assert nl.repo_name == "external_repo"
        assert nl.url == "https://github.com/external/repo"
        assert nl.hash == "commit_xyz"


def test_load_with_metadata_missing_metadata_dict(tmp_path: Path):
    """
    Test if loading file without metadata dict via
    the scl_with_metadata loader raises TypeError
    """
    # Store without metadata (just needlinks)
    needlinks = [
        NeedLink(
            file=Path("src/test.py"),
            line=1,
            tag="#" + " req-Id:",
            need="REQ_1",
            full_line="#" + " req-Id: REQ_1",
        )
    ]

    test_file = tmp_path / "no_metadata.json"
    store_source_code_links_json(test_file, needlinks)

    # Try to load as if it has metadata
    with pytest.raises(TypeError, match="you might wanted to call"):
        load_source_code_links_with_metadata_json(test_file)


def test_load_with_metadata_invalid_items_after_metadata(tmp_path: Path):
    """Test wrong JSON structure"""
    test_file = tmp_path / "bad_items.json"
    # Manually create invalid JSON
    _ = test_file.write_text(
        json.dumps(
            [{"repo_name": "mod", "hash": "h", "url": "u"}, {"invalid": "structure"}]
        )
    )

    with pytest.raises(TypeError, match="must decode to NeedLink objects"):
        load_source_code_links_with_metadata_json(test_file)


#            ────────────────[ File Path Resolution Tests ]────────────────


def test_load_resolves_relative_path_with_env_var(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Test if relative path is resolved using BUILD_WORKSPACE_DIRECTORY"""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    needlinks = [
        NeedLink(
            file=Path("src/test.py"),
            line=1,
            tag="#" + " req-Id:",
            need="REQ_1",
            full_line="#" + " req-Id: REQ_1",
        )
    ]

    # Store in workspace
    cache_file = workspace / "cache.json"
    store_source_code_links_json(cache_file, needlinks)

    # Set env var and load with relative path
    monkeypatch.setenv("BUILD_WORKSPACE_DIRECTORY", str(workspace))
    loaded = load_source_code_links_json(Path("cache.json"))

    assert len(loaded) == 1
    assert loaded[0].need == "REQ_1"


def test_load_with_metadata_resolves_relative_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Edge case: load_with_metadata resolves relative paths using env var"""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    metadata: MetaData = {
        "repo_name": "mod",
        "hash": "h",
        "url": "u",
    }
    needlinks = [
        NeedLink(
            file=Path("src/test.py"),
            line=1,
            tag="#" + "  req-Id:",
            need="REQ_1",
            full_line="#" + " req-Id: REQ_1",
        )
    ]

    cache_file = workspace / "metadata_cache.json"
    store_source_code_links_with_metadata_json(cache_file, metadata, needlinks)

    monkeypatch.setenv("BUILD_WORKSPACE_DIRECTORY", str(workspace))
    loaded = load_source_code_links_with_metadata_json(Path("metadata_cache.json"))

    assert len(loaded) == 1
    assert loaded[0].repo_name == "mod"


#            ─────────────────────[ Roundtrip Tests ]───────────────────


def test_roundtrip_standard_format(tmp_path: Path):
    """Happy path: Standard format preserves all data"""
    needlinks = [
        NeedLink(
            file=Path("src/file1.py"),
            line=10,
            tag="#" + " req-Id:",
            need="REQ_A",
            full_line="#" + " req-Id: REQ_A",
            repo_name="mod_a",
            url="url_a",
            hash="hash_a",
        ),
        NeedLink(
            file=Path("src/file2.py"),
            line=20,
            tag="#" + " req-Id:",
            need="REQ_B",
            full_line="#" + " req-Id: REQ_B",
            repo_name="mod_b",
            url="url_b",
            hash="hash_b",
        ),
    ]

    test_file = tmp_path / "standard.json"
    store_source_code_links_json(test_file, needlinks)
    loaded = load_source_code_links_json(test_file)

    assert len(loaded) == 2
    assert needlinks == loaded
    assert loaded[0].repo_name == "mod_a"
    assert loaded[1].repo_name == "mod_b"


def test_roundtrip_metadata_format_applies_metadata(tmp_path: Path):
    """Happy path: Metadata format applies metadata to all links"""
    metadata: MetaData = {
        "repo_name": "shared_repo",
        "hash": "shared_hash",
        "url": "https://github.com/shared/repo",
    }
    needlinks = [
        NeedLink(
            file=Path("src/f1.py"),
            line=5,
            tag="#" + " req-Id:",
            need="R1",
            full_line="#" + " req-Id: R1",
        ),
        NeedLink(
            file=Path("src/f2.py"),
            line=15,
            tag="#" + " req-Id:",
            need="R2",
            full_line="#" + " req-Id: R2",
        ),
    ]

    test_file = tmp_path / "with_metadata.json"
    store_source_code_links_with_metadata_json(test_file, metadata, needlinks)
    loaded = load_source_code_links_with_metadata_json(test_file)

    assert len(loaded) == 2
    # Both should have the same metadata applied
    for link in loaded:
        assert link.repo_name == "shared_repo"
        assert link.hash == "shared_hash"
        assert link.url == "https://github.com/shared/repo"


def test_roundtrip_empty_lists(tmp_path: Path):
    """Edge case: Empty list can be stored and loaded"""
    test_file = tmp_path / "empty.json"
    store_source_code_links_json(test_file, [])
    loaded = load_source_code_links_json(test_file)

    assert loaded == []


#            ──────────────[ JSON Format Verification Tests ]──────────────


def test_json_format_with_metadata_has_separate_dict(tmp_path: Path):
    """Edge case: Verify metadata format has metadata as first element"""
    metadata: MetaData = {
        "repo_name": "test_mod",
        "hash": "test_hash",
        "url": "test_url",
    }
    needlink = NeedLink(
        file=Path("src/test.py"),
        line=1,
        tag="#" + " req-Id:",
        need="REQ_1",
        full_line="#" + " req-Id: REQ_1",
    )

    test_file = tmp_path / "metadata_format.json"
    store_source_code_links_with_metadata_json(test_file, metadata, [needlink])

    with open(test_file) as f:
        raw_json = json.load(f)

    assert isinstance(raw_json, list)
    assert len(raw_json) == 2  # metadata + 1 needlink
    # First element should be metadata dict
    assert raw_json[0]["repo_name"] == "test_mod"
    assert raw_json[0]["hash"] == "test_hash"
    assert raw_json[0]["url"] == "test_url"


#            ───────────[ NeedLink Equality and Hashing Tests ]─────────


def test_needlink_equality_same_values():
    """Happy path: Two NeedLinks with same values are equal"""
    link1 = NeedLink(
        file=Path("src/test.py"),
        line=10,
        tag="#" + " req-Id:",
        need="REQ_1",
        full_line="#" + " req-Id: REQ_1",
        repo_name="mod",
        url="url",
        hash="hash",
    )
    link2 = NeedLink(
        file=Path("src/test.py"),
        line=10,
        tag="#" + " req-Id:",
        need="REQ_1",
        full_line="#" + " req-Id: REQ_1",
        repo_name="mod",
        url="url",
        hash="hash",
    )

    assert link1 == link2
    assert hash(link1) == hash(link2)


def test_needlink_inequality_different_values():
    """Edge case: NeedLinks with different values are not equal"""
    link1 = NeedLink(
        file=Path("src/test.py"),
        line=10,
        tag="#" + " req-Id:",
        need="REQ_1",
        full_line="#" + " req-Id: REQ_1",
    )
    link2 = NeedLink(
        file=Path("src/test.py"),
        line=20,  # Different line
        tag="#" + " req-Id:",
        need="REQ_1",
        full_line="#" + " req-Id: REQ_1",
    )

    assert link1 != link2
    assert hash(link1) != hash(link2)
