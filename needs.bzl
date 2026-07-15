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

"""
Standalone Bazel macro for generating needs.json from RST/MD sources.

Usage example in BUILD:

    load("@score_docs_as_code//:needs.bzl", "needs_json")

    needs_json(
        name = "my_needs",
        srcs = glob(["docs/**/*.rst", "docs/**/*.md"]),
        conf = "docs/conf.py",
    )

The above creates:
  - //:my_needs          -- needs.json file (primary output)
  - //:my_needs_sphinx   -- raw Sphinx TreeArtifact (needs builder output dir)

Optionally pass generate_html = True to also render HTML:

    needs_json(
        name = "my_needs",
        srcs = glob(["docs/**/*.rst", "docs/**/*.md"]),
        conf = "docs/conf.py",
        generate_html = True,
    )

This additionally creates:
  - //:my_needs_html     -- Sphinx HTML output directory

A minimal conf.py template is provided at:
    @score_docs_as_code//src/templates:minimal_needs_conf_py
"""

load("@aspect_rules_py//py:defs.bzl", "py_binary")
load("@docs_as_code_hub_env//:requirements.bzl", "all_requirements")
load("@rules_python//sphinxdocs:sphinx.bzl", "sphinx_build_binary", "sphinx_docs")

def _sourcelinks_json_for_needs(name, srcs):
    """Generate a sourcelinks JSON from optional source files (can be empty list)."""
    generate_sourcelinks_tool = Label("//scripts_bazel:generate_sourcelinks")
    native.genrule(
        name = name,
        srcs = srcs,
        outs = [name + ".json"],
        cmd = """
        $(location {tool}) \
            --output $@ \
            $(SRCS)
        """.format(tool = generate_sourcelinks_tool),
        tools = [generate_sourcelinks_tool],
        visibility = ["//visibility:private"],
    )

def _doc_entry(src):
    """Best-effort conversion of a same-package src label/path to a toctree entry.

    Returns None for files that aren't RST/MD docs, or whose path can't be
    reliably resolved relative to the auto-generated index (e.g. cross-package
    labels like "//other/pkg:file.rst" or "@repo//pkg:file.rst").
    """
    s = str(src)
    if s.startswith("//") or s.startswith("@"):
        return None
    if s.startswith(":"):
        s = s[1:]
    for ext in (".rst", ".md"):
        if s.endswith(ext):
            return s[:-len(ext)]
    return None

def _canonicalize_local_label(label):
    """Turn a same-package relative label (":foo" or "foo") into an absolute
    "//pkg:foo" label. Absolute ("//...") and repository ("@...") labels are
    returned unchanged.

    This is needed because external_needs entries end up as plain strings in
    a Sphinx --define option, parsed on the Python side where there is no
    notion of "current package" -- so any same-repo reference must already be
    package-qualified by the time it gets there.
    """
    s = str(label)
    if s.startswith("//") or s.startswith("@"):
        return s
    if s.startswith(":"):
        s = s[1:]
    return "//" + native.package_name() + ":" + s

def _generate_conf_py(name, project, project_url):
    """Auto-generate a minimal conf.py so callers don't need to hand-write one.

    Sphinx hard-codes the config file name to "conf.py" (it uses the source
    directory as the config directory unless told otherwise), so the genrule
    output must be named exactly "conf.py". Callers are responsible for only
    invoking this once per package (see needs_json()'s use of
    native.existing_rule() to enforce this).
    """
    lines = ["project = \"" + project + "\""]
    lines.append("project_url = \"" + (project_url if project_url else "") + "\"")
    # Sphinx-Needs stamps its needs.json export with "current_version", taken
    # from this "version" config value. An empty/missing version results in
    # an empty "current_version", which sphinx_needs.external_needs then
    # rejects when another needs_json() target consumes this file via
    # `external_needs` (see load_external_needs()'s "No version defined"
    # check). So always set a non-empty placeholder here.
    lines.append("version = \"1\"")
    lines.append("")
    lines.append("extensions = [")
    lines.append("    \"score_sphinx_bundle\",")
    lines.append("]")
    content = "\n".join(lines) + "\n"

    native.genrule(
        name = name,
        outs = ["conf.py"],
        cmd = "cat > $@ << 'EOF'\n" + content + "EOF\n",
        visibility = ["//visibility:private"],
    )

def _generate_index_rst(name, project, srcs):
    """Auto-generate a minimal index.rst with a toctree covering all doc srcs."""
    entries = [e for e in [_doc_entry(s) for s in srcs] if e]
    lines = [project, "#" * len(project), "", ".. toctree::", ""]
    for e in entries:
        lines.append("   " + e)
    content = "\n".join(lines) + "\n"

    native.genrule(
        name = name,
        outs = [name + ".rst"],
        cmd = "cat > $@ << 'EOF'\n" + content + "EOF\n",
        visibility = ["//visibility:private"],
    )

def _missing_requirements_for_needs(deps):
    """Add Python hub dependencies if they are missing."""
    found = []
    missing = []

    def _target_to_packagename(target):
        return str(target).split("/")[-1].split(":")[0]

    all_packages = [_target_to_packagename(pkg) for pkg in all_requirements]

    def _find(pkg):
        for dep in deps:
            dep_pkg = _target_to_packagename(dep)
            if dep_pkg == pkg:
                return True
        return False

    for pkg in all_packages:
        if _find(pkg):
            found.append(pkg)
        else:
            missing.append(pkg)

    if len(missing) == len(all_requirements):
        return all_requirements
    if len(missing) == 0:
        return []
    if len(found) > 0:
        msg = (
            "Some docs-as-code dependencies are in deps: " + ", ".join(found) +
            "\n   ... but others are missing: " + ", ".join(missing) +
            "\nInconsistent deps for needs_json(): either include all dependencies or none of them."
        )
        fail(msg)
    fail("This case should be unreachable?!")

def needs_json(
        name,
        srcs,
        conf = None,
        root_doc = None,
        deps = [],
        data = [],
        external_needs = [],
        extra_opts = [],
        metamodel = None,
        generate_html = False,
        scan_code = [],
        visibility = ["//visibility:public"]):
    """Generates a needs.json file from RST/MD sources using Sphinx-Needs.

    This macro is standalone and can be used independently of the docs() macro.
    By default, only the Sphinx-Needs builder is invoked — no HTML is rendered.

    conf.py and the Sphinx root document (index.rst) are optional: if omitted,
    a minimal conf.py and an index.rst with a toctree of all srcs are generated
    on the fly, so a package doesn't need to hand-write this boilerplate.

    Since Sphinx requires the config file to be named exactly "conf.py" and to
    live in the same directory as the sources, only one auto-generated conf.py
    can exist per package. If multiple needs_json() targets in the same package
    all omit `conf`, only the first one (in BUILD file order) actually creates
    it (using its `name` as the project name); the others simply reuse it. Pass
    `conf` explicitly to opt out of this sharing.

    Args:
        name:           Name of the target. Creates <name> (needs.json output file)
                        and <name>_sphinx (raw Sphinx output directory). Also used
                        as the project name (and to derive project_url) whenever
                        `conf` is auto-generated -- see note above about sharing
                        when multiple targets in a package do this.
        srcs:           List of RST/MD source files to process.
        conf:           Optional label or path to a Sphinx conf.py file. If not
                        given, a minimal conf.py is generated automatically.
        root_doc:       Optional name (without extension) of an existing doc in
                        `srcs` to use as the Sphinx root/master document. If not
                        given, an index.rst with a toctree of all srcs is
                        generated automatically and used as root document
                        (via `-D root_doc=...`), regardless of what conf.py
                        itself declares. Note: only srcs given as plain,
                        same-package relative paths (e.g. "foo.rst") are added
                        to the generated toctree — srcs referenced via `//` or
                        `@` labels are silently skipped since a relative path
                        can't be reliably derived for them; use `root_doc` and
                        a hand-written index in that case.
        deps:           Additional Python dependencies for the Sphinx build.
        data:           Additional data files made available to the Sphinx build.
        external_needs: List of needs.json targets from other packages or repos.
                        These are passed to Sphinx-Needs via external_needs_source
                        so that cross-repository traceability links are resolved.
                        Two forms are supported:
                          - Cross-repo: "@other_repo//:needs_json" -- must be a
                            repo-root target literally named "needs_json".
                          - Same-repo (sibling needs_json() targets): any
                            package path and target name, e.g.
                            "//some/component:needs_json" or, within the same
                            package, the shorthand ":needs_json" -- both are
                            resolved (via native.package_name()) to an absolute
                            label before being passed along.
                        Example:
                            external_needs = [
                                "@other_repo//:needs_json",
                                "//some/component:needs_json",
                                ":sibling_needs_json",
                            ]
        extra_opts:     Additional Sphinx command-line options passed verbatim.
        metamodel:      Optional label to a metamodel.yaml override file.
                        Use to relax or extend the default metamodel checks.
                        A template without mandatory version check is available at:
                        @score_docs_as_code//src/templates:metamodel_no_version_check.yaml
                        Example:
                            metamodel = "@score_docs_as_code//src/templates:metamodel_no_version_check.yaml"
        generate_html:  If True, also generate HTML output in a separate target
                        named <name>_html. Defaults to False.
        scan_code:      List of source code targets (e.g. filegroups or plain
                        source files) to scan for `req-Id: <need_id>` comments
                        via the source-code-linker. Matching needs get a
                        `source_code_link` pointing back to that location.
                        Defaults to an empty list (no source-code scanning).
        visibility:     Visibility of the generated targets.
    """

    external_needs = [_canonicalize_local_label(e) for e in external_needs]

    generated_root_opts = []
    all_srcs = srcs

    if conf == None:
        # Fixed, package-scoped rule name so that multiple needs_json() targets
        # in the same package share a single generated conf.py instead of each
        # trying to declare their own "conf.py" output (which would collide).
        conf_rule_name = "_needs_json_generated_conf"
        if native.existing_rule(conf_rule_name) == None:
            project_url = "https://example.com/" + name.replace("_", "-")
            _generate_conf_py(conf_rule_name, name, project_url)
        conf = ":conf.py"

    if root_doc == None:
        _generate_index_rst(name + "_index", name, srcs)
        all_srcs = srcs + [":" + name + "_index.rst"]
        generated_root_opts = ["-D", "root_doc=" + name + "_index"]

    extra_opts = generated_root_opts + extra_opts

    all_deps = deps + _missing_requirements_for_needs(deps)
    all_deps = all_deps + [
        Label("//src:plantuml_for_python"),
        Label("//src/extensions/score_sphinx_bundle:score_sphinx_bundle"),
    ]

    metamodel_data = []
    metamodel_opts = []
    if metamodel != None:
        metamodel_data = [metamodel]
        metamodel_opts = ["--define=score_metamodel_yaml=$(location " + str(metamodel) + ")"]

    sphinx_build_binary(
        name = name + "_sphinx_build",
        visibility = ["//visibility:private"],
        data = external_needs + data + metamodel_data,
        deps = all_deps,
    )

    # Generate a sourcelinks JSON from `scan_code` (empty by default, meaning
    # no source-code scanning happens).
    _sourcelinks_json_for_needs(name = name + "_sourcelinks", srcs = scan_code)

    # Base Sphinx options — no HTML builder flags, only needs builder
    base_opts = [
        "-W",
        "--keep-going",
        "-T",
        "--jobs",
        "auto",
        # Skip source-code-linker: not needed for needs.json generation
        "--define=skip_rescanning_via_source_code_linker=1",
        "--define=score_sourcelinks_json=$(location :" + name + "_sourcelinks)",
        # Bazel (sandboxed) builds have no git metadata available, so a real
        # GitHub URL can't be constructed for source_code_link/testlink --
        # render placeholder GitHub-style links instead (still matches the
        # metamodel's "^https://github.com/.*" pattern check). See docs.bzl's
        # needs_json target, which does the same.
        "--define=score_source_code_linker_plain_links=1",
    ]

    # Combine data and external_needs for tools (file availability in sandbox)
    all_tools = data + external_needs + metamodel_data

    # Pass external needs.json files to Sphinx-Needs via define
    if external_needs:
        base_opts.append("--define=external_needs_source=" + str(external_needs))
    elif data:
        # Fallback: legacy behaviour when data contains needs.json targets
        base_opts.append("--define=external_needs_source=" + str(data))

    base_opts = base_opts + metamodel_opts + extra_opts

    # Primary target: needs builder only (no HTML)
    sphinx_docs(
        name = name + "_sphinx",
        srcs = all_srcs,
        config = conf,
        extra_opts = base_opts,
        formats = ["needs"],
        sphinx = ":" + name + "_sphinx_build",
        tools = all_tools + [":" + name + "_sourcelinks"],
        visibility = ["//visibility:private"],
        allow_persistent_workers = False,
    )

    # Extract needs.json to a standalone file.
    # The sphinx_docs output dir for format "needs" contains needs.json at its root.
    native.genrule(
        name = name,
        srcs = [":" + name + "_sphinx"],
        outs = [name + ".json"],
        cmd = "cp $(location :" + name + "_sphinx)/needs.json $@",
        visibility = visibility,
    )

    # Optional: also generate HTML output in a separate target
    if generate_html:
        sphinx_docs(
            name = name + "_html",
            srcs = all_srcs,
            config = conf,
            extra_opts = base_opts,
            formats = ["html"],
            sphinx = ":" + name + "_sphinx_build",
            tools = all_tools + [":" + name + "_sourcelinks"],
            visibility = visibility,
            allow_persistent_workers = False,
        )
