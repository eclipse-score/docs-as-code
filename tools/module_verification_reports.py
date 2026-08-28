# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License, Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
"""Build disposable module-verification report galleries for SCORE modules.

The command in this file deliberately owns no downstream source.  It keeps a
shallow checkout in the shared repository cache, overlays the local
``score_docs_as_code`` checkout for one build, and restores the checkout in a
``finally`` block.  Keeping the orchestration here (rather than in a Bazel
rule) is important: the downstream repository is the workspace for the docs
build and must remain a normal, independently configured Bzlmod workspace.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import fcntl
import html
import json
import os
import re
import shutil
import subprocess
import sys
import time
import tomllib
from collections.abc import Callable, Iterator, Mapping, Sequence
from pathlib import Path
from urllib.parse import urlparse

GITHUB_ORG = "eclipse-score"
TEMPLATE_NAME = "mod_ver_report_tiny"
REPORT_WORKPRODUCT = "wp__verification_module_ver_report"
DOCS_COMMAND = ("bazel", "run", "--lockfile_mode=off", "//:docs")
REPORT_DIRECTORY = "module_verification_reports"
REPORT_GOLDEN_DIRECTORY = "module_verification_reports_goldens"
REF_NAMESPACE = "refs/score-docs-as-code"
FULL_SHA = re.compile(r"^[0-9a-fA-F]{40}$")


def _progress(message: str) -> None:
    """Report a step to stderr so long git/bazel operations do not look stuck."""

    print(message, file=sys.stderr, flush=True)


class ReportToolError(RuntimeError):
    """A user-actionable failure while preparing or rendering a report."""


@dataclasses.dataclass(frozen=True)
class RepositorySpec:
    """One repository entry from a gallery profile."""

    name: str
    revision: str
    remote: str = ""

    @property
    def git_remote(self) -> str:
        return self.remote or f"https://github.com/{GITHUB_ORG}/{self.name}.git"


@dataclasses.dataclass(frozen=True)
class Profile:
    name: str
    repositories: tuple[RepositorySpec, ...]


@dataclasses.dataclass
class PreparedCheckout:
    """The synchronized checkout and the revisions associated with a run."""

    spec: RepositorySpec
    path: Path
    default_revision: str
    resolved_revision: str


@dataclasses.dataclass
class RepositoryResult:
    repository: str
    requested_revision: str
    resolved_sha: str | None
    status: str
    report_path: str | None = None
    details: str = ""

    def manifest_entry(self) -> dict[str, str | None]:
        return {
            "repository": self.repository,
            "revision": self.requested_revision,
            "resolved_sha": self.resolved_sha,
            "report_path": self.report_path,
            "command": " ".join(DOCS_COMMAND),
            "status": self.status,
            "details": self.details,
        }


def resolve_cache_dir(
    cache_dir: Path | str | None = None,
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    """Resolve the cache root using the repo-cache contract.

    ``XDG_CACHE_HOME`` is used only when it is non-empty.  An explicit command
    line path always wins, which makes the command straightforward to use in
    tests and CI jobs.
    """

    if cache_dir is not None:
        return Path(cache_dir).expanduser()
    env = os.environ if environ is None else environ
    xdg_cache_home = env.get("XDG_CACHE_HOME", "")
    if xdg_cache_home:
        return Path(xdg_cache_home).expanduser() / "repo-cache"
    return (Path.home() if home is None else home) / ".cache" / "repo-cache"


def _repositories_toml_path(config_dir: Path | None = None) -> Path:
    if config_dir is not None:
        return Path(config_dir) / "module_verification_reports.toml"
    tools = Path(__file__).resolve().parent
    return tools / "module_verification_reports.toml"


def _parse_repository_entry(
    entry: Mapping[str, object], profile_name: str, path: Path, seen: set[str]
) -> RepositorySpec:
    name = entry.get("name")
    remote = entry.get("remote", "")
    if not isinstance(name, str) or not name:
        raise ReportToolError(f"repository entry is missing a name in {path}: {name!r}")
    if name in seen:
        raise ReportToolError(f"duplicate repository in {path}: {name}")
    if not isinstance(remote, str):
        raise ReportToolError(f"remote for {name} must be a string")
    if profile_name == "main":
        revision = "main"
    else:
        pinned = entry.get("pinned")
        if not isinstance(pinned, str) or not FULL_SHA.fullmatch(pinned):
            raise ReportToolError(
                f"pinned profile revision for {name} is not a full SHA: {pinned!r}"
            )
        revision = pinned
    seen.add(name)
    return RepositorySpec(name, revision, remote)


def load_profile(profile_name: str, config_dir: Path | None = None) -> Profile:
    """Load and validate a named profile from the shared repositories file."""

    if profile_name not in {"main", "pinned"}:
        raise ReportToolError(f"unknown profile {profile_name!r}; use main or pinned")
    path = _repositories_toml_path(config_dir)
    try:
        raw_data = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ReportToolError(f"profile file does not exist: {path}") from exc
    except tomllib.TOMLDecodeError as exc:
        raise ReportToolError(f"invalid profile {path}: {exc}") from exc

    raw_repositories = raw_data.get("repositories")
    if not isinstance(raw_repositories, list) or not all(
        isinstance(item, dict) for item in raw_repositories
    ):
        raise ReportToolError(
            f"repositories file must define repository tables: {path}"
        )

    repositories: list[RepositorySpec] = []
    seen: set[str] = set()
    repositories.extend(
        _parse_repository_entry(entry, profile_name, path, seen)
        for entry in raw_repositories
    )

    if not repositories:
        raise ReportToolError(f"repositories file contains no repositories: {path}")
    return Profile(profile_name, tuple(repositories))


def select_repositories(
    profile: Profile, names: Sequence[str] | None
) -> tuple[RepositorySpec, ...]:
    """Apply repeated ``--repo`` filters, bounded by the profile's repository count."""

    limit = len(profile.repositories)
    requested = list(names or ())
    if len(requested) > limit:
        raise ReportToolError(f"at most {limit} --repo filters may be supplied")
    if not requested:
        selected = list(profile.repositories)
    else:
        by_name = {repository.name: repository for repository in profile.repositories}
        unknown = [name for name in requested if name not in by_name]
        if unknown:
            raise ReportToolError(
                "repository is not in the selected profile: " + ", ".join(unknown)
            )
        if len(set(requested)) != len(requested):
            raise ReportToolError("a repository may be requested only once")
        selected = [by_name[name] for name in requested]
    if not 1 <= len(selected) <= limit:
        raise ReportToolError(f"select between 1 and {limit} repositories")
    return tuple(selected)


def _canonical_remote(remote: str) -> str:
    value = remote.strip().rstrip("/")
    if value.startswith("git@") and ":" in value:
        host, path = value.split(":", 1)
        value = f"https://{host.removeprefix('git@')}/{path}"
    elif value.startswith("ssh://"):
        parsed = urlparse(value)
        value = f"https://{parsed.hostname}/{parsed.path.lstrip('/')}"
    elif value.startswith("http://"):
        value = "https://" + value.removeprefix("http://")
    return value.removesuffix(".git").rstrip("/")


def _remote_matches(actual: str, expected: str) -> bool:
    return _canonical_remote(actual) == _canonical_remote(expected)


def _command_text(result: subprocess.CompletedProcess[str]) -> str:
    output = (result.stderr or result.stdout or "").strip()
    output = re.sub(r"\s+", " ", output)
    return output[-900:]


class CheckoutManager:
    """Prepare and restore synchronized disposable downstream checkouts."""

    def __init__(
        self,
        cache_dir: Path,
        source_root: Path,
        *,
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
    ) -> None:
        self.cache_dir = Path(cache_dir)
        self.source_root = Path(source_root).resolve()
        self.runner = runner

    def repository_path(self, repository: str) -> Path:
        return self.cache_dir / GITHUB_ORG / repository

    def lock_path(self, repository: str) -> Path:
        # The namespace intentionally differs from repo_policy_sync's lock
        # namespace.  The lock is outside the checkout so git clean cannot
        # remove it, and it is also outside the local override symlink.
        return self.cache_dir / ".locks" / "score-docs-as-code" / f"{repository}.lock"

    @contextlib.contextmanager
    def _lock(self, repository: str) -> Iterator[None]:
        lock_path = self.lock_path(repository)
        lock_path.parent.mkdir(parents=True, exist_ok=True)
        with lock_path.open("a+", encoding="utf-8") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _run_git(
        self, path: Path, arguments: Sequence[str]
    ) -> subprocess.CompletedProcess[str]:
        result = self.runner(
            ["git", *arguments],
            cwd=path,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode:
            command = "git " + " ".join(arguments)
            detail = _command_text(result)
            raise ReportToolError(
                f"{command} failed in {path}" + (f": {detail}" if detail else "")
            )
        return result

    def _revision(self, path: Path) -> str:
        result = self._run_git(path, ["rev-parse", "--verify", "HEAD^{commit}"])
        return result.stdout.strip()

    def _record_default_ref(self, path: Path, repository: str, revision: str) -> None:
        self._run_git(
            path,
            ["update-ref", f"{REF_NAMESPACE}/{repository}/default", revision],
        )

    def _synchronize_default(
        self, spec: RepositorySpec, path: Path, *, clone: bool
    ) -> str:
        if clone:
            _progress(f"{spec.name}: cloning {spec.git_remote}")
            path.parent.mkdir(parents=True, exist_ok=True)
            result = self.runner(
                [
                    "gh",
                    "repo",
                    "clone",
                    spec.git_remote,
                    str(path),
                    "--",
                    "--depth",
                    "1",
                    "--branch",
                    "main",
                ],
                text=True,
                capture_output=True,
                check=False,
            )
            if result.returncode:
                detail = _command_text(result)
                raise ReportToolError(
                    f"initial clone failed for {spec.name}"
                    + (f": {detail}" if detail else "")
                )
        else:
            origin = self._run_git(path, ["remote", "get-url", "origin"]).stdout.strip()
            if not _remote_matches(origin, spec.git_remote):
                raise ReportToolError(
                    f"origin mismatch for {spec.name}: expected {spec.git_remote}, got {origin}"
                )
            _progress(f"{spec.name}: fetching origin/main")

        self._run_git(path, ["fetch", "--depth=1", "origin", "main"])
        self._run_git(path, ["checkout", "--detach", "--force", "FETCH_HEAD"])
        self._run_git(path, ["clean", "-fdx"])
        revision = self._revision(path)
        self._record_default_ref(path, spec.name, revision)
        _progress(f"{spec.name}: default checkout at {revision[:12]}")
        return revision

    def _select_pinned(self, spec: RepositorySpec, path: Path) -> str:
        _progress(f"{spec.name}: checking out pinned {spec.revision[:12]}")
        self._run_git(path, ["fetch", "--depth=1", "origin", spec.revision])
        self._run_git(path, ["checkout", "--detach", "--force", spec.revision])
        resolved = self._revision(path)
        if resolved.lower() != spec.revision.lower():
            raise ReportToolError(
                f"pinned checkout for {spec.name} resolved to {resolved}, "
                f"expected {spec.revision}"
            )
        self._run_git(path, ["clean", "-fdx"])
        return resolved

    @contextlib.contextmanager
    def checkout(self, spec: RepositorySpec) -> Iterator[PreparedCheckout]:
        path = self.repository_path(spec.name)
        default_revision: str | None = None
        active_error: BaseException | None = None
        with self._lock(spec.name):
            try:
                if path.exists() and not path.is_dir():
                    raise ReportToolError(f"checkout path is not a directory: {path}")
                default_revision = self._synchronize_default(
                    spec, path, clone=not path.exists()
                )
                resolved = (
                    self._select_pinned(spec, path)
                    if spec.revision != "main"
                    else default_revision
                )
                yield PreparedCheckout(spec, path, default_revision, resolved)
            except BaseException as exc:
                active_error = exc
                raise
            finally:
                if default_revision is not None and path.is_dir():
                    try:
                        self._run_git(
                            path,
                            ["checkout", "--detach", "--force", default_revision],
                        )
                        self._run_git(path, ["clean", "-fdx"])
                        self._record_default_ref(path, spec.name, default_revision)
                    except ReportToolError as restore_error:
                        if active_error is None:
                            raise
                        raise ReportToolError(
                            f"could not restore checkout {path}: {restore_error}"
                        ) from active_error


def _strip_score_docs_overrides(content: str) -> str:
    """Remove existing score_docs_as_code override blocks from MODULE.bazel."""

    lines = content.splitlines(keepends=True)
    result: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        if re.match(r"^\s*\w+_override\s*\(", line):
            start = index
            depth = line.count("(") - line.count(")")
            index += 1
            while index < len(lines) and depth > 0:
                depth += lines[index].count("(") - lines[index].count(")")
                index += 1
            block = "".join(lines[start:index])
            if 'module_name = "score_docs_as_code"' in block or (
                "module_name = 'score_docs_as_code'" in block
            ):
                continue
            result.extend(lines[start:index])
            continue
        result.append(line)
        index += 1
    return "".join(result)


_SCORE_DEP = re.compile(
    r"(?ms)^[ \t]*bazel_dep\s*\(\s*name\s*=\s*['\"]score_docs_as_code['\"][^)]*\)[ \t]*$"
)


def local_module_override(
    module_bazel: str, override_path: str = "../docs_as_code"
) -> str:
    """Return MODULE.bazel with the local docs-as-code override installed."""

    base = _strip_score_docs_overrides(module_bazel)
    replacement = (
        'bazel_dep(name = "score_docs_as_code")\n'
        "local_path_override(\n"
        '    module_name = "score_docs_as_code",\n'
        f'    path = "{override_path}"\n'
        ")"
    )
    updated, count = _SCORE_DEP.subn(replacement, base, count=1)
    if count != 1:
        raise ReportToolError(
            "MODULE.bazel does not contain a bazel_dep for score_docs_as_code"
        )
    return updated


def report_need(repository: str) -> str:
    """Return the exact temporary Need page injected into a checkout.

    The report is a ``document`` that realizes the module-verification-report
    workproduct rather than linking ``belongs_to`` the module directly — the
    ``document`` type does not support that link. ``mod_ver_report_tiny``
    recovers the module id from this need's own id instead.
    """

    display_name = repository.replace("_", " ").title()
    return (
        f".. document:: {display_name} Module Verification Report\n"
        f"   :id: doc__{repository}_verification_report\n"
        f"   :post_template: {TEMPLATE_NAME}\n"
        f"   :status: valid\n"
        f"   :safety: QM\n"
        f"   :security: NO\n"
        f"   :realizes: {REPORT_WORKPRODUCT}\n"
        f"   :version: 1\n"
    )


def _docs_source_dir(checkout: Path) -> Path:
    build_file = next(
        (
            candidate
            for candidate in (checkout / "BUILD", checkout / "BUILD.bazel")
            if candidate.is_file()
        ),
        None,
    )
    if build_file is None:
        raise ReportToolError(f"root BUILD file is missing in {checkout}")
    contents = build_file.read_text(encoding="utf-8")
    docs_call = re.search(r"\bdocs\s*\((?P<body>.*?)\n?\)", contents, re.DOTALL)
    source_dir = "docs"
    if docs_call:
        match = re.search(
            r"\bsource_dir\s*=\s*['\"]([^'\"]+)['\"]", docs_call.group("body")
        )
        if match:
            source_dir = match.group(1)
    source = checkout / source_dir
    if not (source / "index.rst").is_file():
        raise ReportToolError(
            f"root documentation index is missing: {source / 'index.rst'}"
        )
    return source


class DownstreamInjection:
    """Apply and exactly restore the temporary downstream documentation edits."""

    def __init__(self, checkout: Path, repository: str, source_root: Path) -> None:
        self.checkout = checkout
        self.repository = repository
        self.source_root = source_root.resolve()
        self.module_path = checkout / "MODULE.bazel"
        self.docs_source: Path | None = None
        self.index_path: Path | None = None
        self.page_path: Path | None = None
        self._module_original: bytes | None = None
        self._index_original: bytes | None = None
        self._created_page_dir = False

    def _ensure_override_link(self) -> None:
        # Keep the sibling name used by the existing downstream consumer
        # compatibility tests.  The git ref/lock namespace remains separate
        # from that test suite's namespace.
        link = self.checkout.parent / "docs_as_code"
        if link.is_symlink():
            if link.resolve() != self.source_root:
                raise ReportToolError(f"local override link points elsewhere: {link}")
        elif link.exists():
            raise ReportToolError(f"local override path is not a symlink: {link}")
        else:
            link.symlink_to(self.source_root, target_is_directory=True)

    def _toctree_block(self) -> str:
        docname = f"{REPORT_DIRECTORY}/{self.repository}"
        return (
            f".. score-docs-as-code: module-verification-report begin\n\n"
            ".. toctree::\n"
            "   :hidden:\n\n"
            f"   {docname}\n\n"
            f".. score-docs-as-code: module-verification-report end\n"
        )

    def apply(self) -> None:
        if not self.module_path.is_file():
            raise ReportToolError(f"MODULE.bazel is missing in {self.checkout}")
        self.docs_source = _docs_source_dir(self.checkout)
        self.index_path = self.docs_source / "index.rst"
        index_text = self.index_path.read_text(encoding="utf-8")
        if ".. toctree::" not in index_text:
            raise ReportToolError(f"root index has no toctree: {self.index_path}")

        self._ensure_override_link()
        original_module = self.module_path.read_bytes()
        original_index = self.index_path.read_bytes()
        self._module_original = original_module
        self._index_original = original_index

        newline = "\r\n" if b"\r\n" in original_index else "\n"
        page_dir = self.docs_source / REPORT_DIRECTORY
        if (page_dir / f"{self.repository}.rst").exists():
            raise ReportToolError(f"temporary report page already exists: {page_dir}")
        self._created_page_dir = not page_dir.exists()
        page_dir.mkdir(parents=True, exist_ok=True)
        self.page_path = page_dir / f"{self.repository}.rst"
        self.page_path.write_text(
            report_need(self.repository), encoding="utf-8", newline=newline
        )
        self.module_path.write_text(
            local_module_override(original_module.decode("utf-8")), encoding="utf-8"
        )
        self.index_path.write_text(
            index_text.rstrip() + newline + newline + self._toctree_block(),
            encoding="utf-8",
            newline=newline,
        )

    def restore(self) -> None:
        errors: list[str] = []
        if self._module_original is not None:
            try:
                self.module_path.write_bytes(self._module_original)
            except OSError as exc:
                errors.append(f"MODULE.bazel: {exc}")
        if self._index_original is not None and self.index_path is not None:
            try:
                self.index_path.write_bytes(self._index_original)
            except OSError as exc:
                errors.append(f"index.rst: {exc}")
        if self.page_path is not None:
            try:
                self.page_path.unlink(missing_ok=True)
                if self._created_page_dir:
                    self.page_path.parent.rmdir()
            except OSError as exc:
                errors.append(f"generated report page: {exc}")
        if errors:
            raise ReportToolError(
                "could not restore downstream injection: " + "; ".join(errors)
            )

    def __enter__(self) -> DownstreamInjection:
        try:
            self.apply()
        except Exception:
            self.restore()
            raise
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        self.restore()
        return False


def _flatten_needs(needs_json: Path) -> dict[str, dict[str, object]]:
    try:
        payload = json.loads(needs_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReportToolError(
            f"cannot read generated needs JSON {needs_json}: {exc}"
        ) from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("versions"), dict):
        raise ReportToolError(f"generated needs JSON has no versions map: {needs_json}")
    result: dict[str, dict[str, object]] = {}
    for version in payload["versions"].values():
        if not isinstance(version, dict) or not isinstance(version.get("needs"), dict):
            continue
        for need_id, need in version["needs"].items():
            if isinstance(need_id, str) and isinstance(need, dict):
                result[need_id] = need
    return result


def _link_ids(need: Mapping[str, object], field: str) -> list[str]:
    raw = need.get(field, [])
    if isinstance(raw, str):
        return [raw]
    if not isinstance(raw, list):
        return []
    result: list[str] = []
    for value in raw:
        if isinstance(value, str):
            result.append(value.split("[", 1)[0])
        elif isinstance(value, dict) and isinstance(value.get("id"), str):
            result.append(value["id"])
    return result


def validate_module_graph(
    needs: Mapping[str, Mapping[str, object]], repository: str
) -> None:
    """Reject an empty module/component/feature graph before gallery collection.

    Sphinx-needs already rejects a dangling ``includes``/``belongs_to`` link as
    part of the docs build itself (``needs.link_outgoing``), including links
    resolved through ``external_needs`` (e.g. features maintained centrally in
    ``score_platform`` rather than in the module's own repository). Reaching
    this function therefore means every linked Need already resolves
    *somewhere*, so this only needs to catch what Sphinx-needs does not flag:
    an ``includes`` or ``belongs_to`` link list that is simply empty, which the
    ``mod_ver_report_tiny`` template would otherwise render as a silently
    empty section.
    """

    module_id = f"mod__{repository}"
    component_ids = _link_ids(needs.get(module_id, {}), "includes")
    if not component_ids:
        raise ReportToolError(
            f"structural failure: Need {module_id} has no includes graph"
        )
    for component_id in component_ids:
        component = needs.get(component_id)
        if component is None:
            # Not present in this repository's own needs.json, e.g. resolved
            # through external_needs. Sphinx-needs already validated the link.
            continue
        if not _link_ids(component, "belongs_to"):
            raise ReportToolError(
                f"structural failure: component {component_id} has no belongs_to feature"
            )


def _copy_report_and_assets(
    checkout: PreparedCheckout, repository: str, output_dir: Path
) -> str:
    relative_html = Path(REPORT_DIRECTORY) / f"{repository}.html"
    source_html = checkout.path / "_build" / relative_html
    if not source_html.is_file():
        raise ReportToolError(f"rendered report page is missing: {source_html}")

    destination_repo = output_dir / repository
    shutil.rmtree(destination_repo, ignore_errors=True)
    destination_repo.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_html, destination_repo / "report.html")

    build_dir = checkout.path / "_build"
    # Sphinx pages keep their original depth, so copying these directories to
    # the gallery root preserves every relative asset URL in report.html.
    for child in build_dir.iterdir():
        if child.name.startswith("_") and child.is_dir():
            shutil.copytree(child, output_dir / child.name, dirs_exist_ok=True)
    return f"{repository}/report.html"


def _failure_detail(exc: BaseException) -> str:
    detail = re.sub(r"\s+", " ", str(exc)).strip()
    return detail[-1000:] or type(exc).__name__


def _golden_path(golden_root: Path, profile: str, repository: str) -> Path:
    return golden_root / profile / repository / "report.html"


def _check_golden(
    report_file: Path, golden_root: Path, profile: str, repository: str
) -> None:
    golden = _golden_path(golden_root, profile, repository)
    if not golden.is_file():
        raise ReportToolError(f"golden file is missing: {golden}")
    if report_file.read_bytes() != golden.read_bytes():
        raise ReportToolError(f"golden mismatch: {golden}")


def _status_badge(status: str) -> str:
    icon, label = ("✓", "Success") if status == "success" else ("✗", "Failure")
    return f'<span class="badge {html.escape(status)}">{icon} {label}</span>'


def _report_cell(result: RepositoryResult) -> str:
    if result.status == "success" and result.report_path:
        href = html.escape(result.report_path, quote=True)
        return f'<a href="{href}">View report</a>'
    reason = html.escape(result.details or "Verification failed")
    return f"<details><summary>Why did it fail?</summary><pre>{reason}</pre></details>"


def _write_gallery_index(
    output_dir: Path, profile: Profile, results: Sequence[RepositoryResult]
) -> None:
    succeeded = sum(1 for result in results if result.status == "success")
    total = len(results)
    rows: list[str] = []
    for result in results:
        row_class = "failed-row" if result.status != "success" else ""
        rows.append(
            f'<tr class="{row_class}">'
            f"<td>{html.escape(result.repository)}</td>"
            f"<td>{_status_badge(result.status)}</td>"
            f"<td>{_report_cell(result)}</td>"
            "<td class='meta'>"
            f"requested <code>{html.escape(result.requested_revision)}</code>"
            f"<br>resolved <code>{html.escape(result.resolved_sha or 'unknown')}</code>"
            "</td>"
            "</tr>"
        )
    document = (
        """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Module Verification Reports</title>
<style>
body{font-family:sans-serif;margin:2rem;color:#222}
h1{margin-bottom:.2rem}
.summary{font-size:1.1rem;margin:0 0 1.2rem}
table{border-collapse:collapse;width:100%}
th,td{border:1px solid #ddd;padding:.6rem .8rem;text-align:left;vertical-align:top}
th{background:#f5f5f5}
tr.failed-row{background:#fdecea}
.badge{display:inline-block;padding:.15rem .6rem;border-radius:1rem;font-weight:bold;white-space:nowrap}
.badge.success{background:#e6f4ea;color:#1e7e34}
.badge.failure{background:#fbe7e6;color:#a00}
.meta{color:#777;font-size:.85rem}
.meta code{font-family:monospace}
details summary{cursor:pointer;color:#a00}
details pre{white-space:pre-wrap;word-break:break-word;background:#fff6f6;padding:.5rem;border-radius:.3rem}
</style>
</head><body>
<h1>Module Verification Reports</h1>
<p class="summary">SUCCEEDED of TOTAL modules verified successfully for profile <code>PROFILE</code>.</p>
<table><thead><tr><th>Repository</th><th>Status</th><th>Report</th><th>Revision</th></tr></thead>
<tbody>ROWS</tbody></table></body></html>
""".replace("PROFILE", html.escape(profile.name))
        .replace("ROWS", "\n".join(rows))
        .replace("SUCCEEDED", str(succeeded))
        .replace("TOTAL", str(total))
    )
    (output_dir / "index.html").write_text(document, encoding="utf-8")


def _write_manifest(
    output_dir: Path, profile: Profile, results: Sequence[RepositoryResult]
) -> None:
    manifest = {
        "profile": profile.name,
        "repositories": [result.manifest_entry() for result in results],
    }
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def build_gallery(
    profile: Profile,
    selected: Sequence[RepositorySpec],
    *,
    source_root: Path,
    output_dir: Path,
    cache_dir: Path,
    golden_root: Path | None = None,
    check_goldens: bool = False,
    update_goldens: bool = False,
    checkout_factory: Callable[
        [RepositorySpec], contextlib.AbstractContextManager[PreparedCheckout]
    ]
    | None = None,
    command_runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> tuple[list[RepositoryResult], bool]:
    """Render all selected repositories and write the independent gallery."""

    if update_goldens and profile.name != "pinned":
        raise ReportToolError("--update-goldens is allowed only for the pinned profile")
    source_root = Path(source_root).resolve()
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    golden_root = (
        source_root / "scripts_bazel" / REPORT_GOLDEN_DIRECTORY
        if golden_root is None
        else Path(golden_root)
    )
    manager = CheckoutManager(cache_dir, source_root, runner=command_runner)
    results: list[RepositoryResult] = []
    total = len(selected)

    for index, spec in enumerate(selected, start=1):
        prefix = f"[{index}/{total}] {spec.name}"
        result = RepositoryResult(spec.name, spec.revision, None, "failure")
        try:
            _progress(f"{prefix}: preparing checkout")
            session = (
                checkout_factory(spec)
                if checkout_factory is not None
                else manager.checkout(spec)
            )
            with session as checkout:
                result.resolved_sha = checkout.resolved_revision
                with DownstreamInjection(checkout.path, spec.name, source_root):
                    _progress(
                        f"{prefix}: running {' '.join(DOCS_COMMAND)} "
                        "(a Bazel/Sphinx build; this can take several minutes)"
                    )
                    started = time.monotonic()
                    completed = command_runner(
                        list(DOCS_COMMAND),
                        cwd=checkout.path,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    _progress(
                        f"{prefix}: docs build finished in "
                        f"{time.monotonic() - started:.0f}s"
                    )
                    if completed.returncode:
                        output = _command_text(completed)
                        raise ReportToolError(
                            f"docs build failed with exit code {completed.returncode}"
                            + (f": {output}" if output else "")
                        )
                    needs = _flatten_needs(checkout.path / "_build" / "needs.json")
                    validate_module_graph(needs, spec.name)
                    report_path = _copy_report_and_assets(
                        checkout, spec.name, output_dir
                    )
                    result.report_path = report_path
                    result.status = "success"
                    if check_goldens:
                        _check_golden(
                            output_dir / report_path,
                            golden_root,
                            profile.name,
                            spec.name,
                        )
        except Exception as exc:
            result.status = "failure"
            result.report_path = None
            result.details = _failure_detail(exc)
            shutil.rmtree(output_dir / spec.name, ignore_errors=True)
        _progress(
            f"{prefix}: {result.status}"
            + (f" — {result.details}" if result.details else "")
        )
        results.append(result)

    _write_gallery_index(output_dir, profile, results)
    _write_manifest(output_dir, profile, results)

    if update_goldens:
        failures = [result for result in results if result.status != "success"]
        if failures:
            raise ReportToolError(
                "cannot update goldens while repositories failed: "
                + ", ".join(result.repository for result in failures)
            )
        for result in results:
            assert result.report_path is not None
            golden = _golden_path(golden_root, profile.name, result.repository)
            golden.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(output_dir / result.report_path, golden)

    strict_failure = profile.name == "pinned" and any(
        result.status != "success" for result in results
    )
    return results, strict_failure


def _workspace_root() -> Path:
    workspace = os.environ.get("BUILD_WORKSPACE_DIRECTORY")
    if workspace:
        return Path(workspace).resolve()
    return Path(__file__).resolve().parents[1]


def argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", choices=("main", "pinned"), default="main")
    parser.add_argument("--repo", action="append", dest="repositories", metavar="NAME")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--check-goldens", action="store_true")
    parser.add_argument("--update-goldens", action="store_true")
    parser.add_argument("--cache-dir", type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = argument_parser()
    args = parser.parse_args(argv)
    if args.check_goldens and args.update_goldens:
        parser.error("--check-goldens and --update-goldens are mutually exclusive")
    try:
        source_root = _workspace_root()
        profile = load_profile(args.profile)
        selected = select_repositories(profile, args.repositories)
        output_dir = args.output_dir or (
            source_root / "_build" / "module-verification-reports" / profile.name
        )
        results, strict_failure = build_gallery(
            profile,
            selected,
            source_root=source_root,
            output_dir=output_dir,
            cache_dir=resolve_cache_dir(args.cache_dir),
            check_goldens=args.check_goldens,
            update_goldens=args.update_goldens,
        )
    except ReportToolError as exc:
        parser.exit(2, f"module-verification-reports: {exc}\n")

    for result in results:
        suffix = f" — {result.details}" if result.details else ""
        print(f"{result.repository}: {result.status}{suffix}")
    return 1 if strict_failure else 0


if __name__ == "__main__":
    sys.exit(main())
