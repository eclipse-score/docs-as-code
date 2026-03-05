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
import os
from collections.abc import Callable, Generator
from contextlib import suppress
from pathlib import Path

import pytest
from sphinx.testing.util import SphinxTestApp


def _make_app(srcdir: Path, outdir: Path) -> SphinxTestApp:
    original_cwd = None
    with suppress(FileNotFoundError):
        original_cwd = os.getcwd()
    os.chdir(srcdir)
    try:
        return SphinxTestApp(
            freshenv=True,
            srcdir=srcdir,
            confdir=srcdir,
            outdir=outdir,
            buildername="html",
        )
    finally:
        if original_cwd is not None:
            with suppress(FileNotFoundError, OSError):
                os.chdir(original_cwd)


@pytest.fixture
def docs_dir(tmp_path: Path) -> Path:
    d = tmp_path / "docs"
    d.mkdir()
    return d


@pytest.fixture
def make_sphinx_app(
    docs_dir: Path, tmp_path: Path
) -> Generator[Callable[[dict[str, str]], SphinxTestApp], None, None]:
    """Factory: writes conf + index, returns a SphinxTestApp, cleans up on teardown."""
    apps: list[SphinxTestApp] = []

    def _factory(mapping: dict[str, str]) -> SphinxTestApp:
        (docs_dir / "conf.py").write_text(
            'extensions = ["score_any_folder"]\n'
            f"score_any_folder_mapping = {mapping!r}\n"
        )
        (docs_dir / "index.rst").write_text("Root\n====\n")
        app = _make_app(docs_dir, tmp_path / "out")
        apps.append(app)
        return app

    yield _factory

    for app in apps:
        app.cleanup()


def test_symlink_exposes_files_at_target_path(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
    tmp_path: Path,
) -> None:
    """Files in the source directory are readable via the symlinked target path."""
    src_docs = tmp_path / "src" / "module_docs"
    src_docs.mkdir(parents=True)
    content = "Remote Page\n===========\n\nContent here.\n"
    (src_docs / "page.rst").write_text(content)

    make_sphinx_app({"../src/module_docs": "module"})

    assert (docs_dir / "module" / "page.rst").read_text() == content


def test_symlink_is_idempotent(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
    tmp_path: Path,
) -> None:
    """Build cleanup removes temporary links and a second build still succeeds."""
    src_docs = tmp_path / "external"
    src_docs.mkdir()

    make_sphinx_app({"../external": "notes"}).build()
    link = docs_dir / "notes"
    assert not link.exists()

    make_sphinx_app({"../external": "notes"}).build()

    assert not link.exists()


def test_stale_symlink_is_replaced(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
    tmp_path: Path,
) -> None:
    """A symlink pointing to a stale target is replaced with the correct one."""
    correct_src = tmp_path / "correct"
    correct_src.mkdir()
    wrong_target = tmp_path / "wrong"
    wrong_target.mkdir()
    (docs_dir / "module").symlink_to(wrong_target)

    make_sphinx_app({"../correct": "module"})

    assert (docs_dir / "module").resolve() == correct_src.resolve()


def test_existing_non_symlink_logs_error_and_skips(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
    tmp_path: Path,
) -> None:
    """A real directory at the target path is left untouched and an error is logged."""
    (tmp_path / "external").mkdir()
    real_dir = docs_dir / "module"
    real_dir.mkdir()

    app: SphinxTestApp = make_sphinx_app({"../external": "module"})

    assert real_dir.is_dir() and not real_dir.is_symlink()
    assert "not a symlink" in app.warning.getvalue()


def test_empty_mapping_is_a_no_op(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp], docs_dir: Path
) -> None:
    """An empty mapping produces no symlinks and no errors."""
    make_sphinx_app({}).build()

    assert [p for p in docs_dir.iterdir() if p.is_symlink()] == []


def test_multiple_mappings(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
    tmp_path: Path,
) -> None:
    """Multiple mapping entries each produce their own symlink."""
    for name in ("alpha", "beta"):
        (tmp_path / name).mkdir()

    make_sphinx_app({"../alpha": "alpha", "../beta": "beta"})

    for name in ("alpha", "beta"):
        link = docs_dir / name
        assert link.is_symlink(), f"symlink for {name!r} was not created"
        assert link.resolve() == (tmp_path / name).resolve()


def test_target_in_subfolder(
    make_sphinx_app: Callable[[dict[str, str]], SphinxTestApp],
    docs_dir: Path,
    tmp_path: Path,
) -> None:
    """A target path with intermediate directories creates the parent dirs."""
    src_docs = tmp_path / "external"
    src_docs.mkdir()

    make_sphinx_app({"../external": "foo/other"})

    link = docs_dir / "foo" / "other"
    assert link.is_symlink()
    assert link.resolve() == src_docs.resolve()
