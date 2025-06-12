(getting_started)=
# Using Docs-As-Code


A Bazel module providing tools and extensions to enable and simplify documentation building via Sphinx

## Overview

This module allows you to easily integrate Sphinx documentation generation into your Bazel build system. It provides a collection of utilities and extensions specifically designed to enhance documentation capabilities.

## Features

- Seamless integration with Bazel build system
- Custom Sphinx extensions for enhanced documentation
- Support for PlantUML diagrams
- Source code linking capabilities
- Metamodel validation and checks
- Custom layouts and themes
- Header service for consistent documentation styling

## Getting Started

### Installation

Add the module to your `MODULE.bazel` file:

```starlark
bazel_dep(name = "score_docs_as_code", version = "0.2.7")
```

And make sure to also add the S-core Bazel registry to your `.bazelrc` file

```starlark
common --registry=https://raw.githubusercontent.com/eclipse-score/bazel_registry/main/
common --registry=https://bcr.bazel.build
```

______________________________________________________________________

### Basic Usage

#### 1. Import the `docs()` macro in your BUILD file:

```python
load("@score_docs_as_code//docs.bzl", "docs")

docs(
    conf_dir = "<your sphinc conf dir>",
    source_dir = "<your sphinx source dir>",
    docs_targets = [
        {
            # For more detailed explanation look at the 'docs_targets' section
            "suffix": "",  # This creates the normal 'incremental' and 'docs' target
        },
    ],
    source_files_to_scan_for_needs_links = [
        # Note: you can add file groups, globs, or entire targets here.
        "<your targets that the source code linker should scan>"
    ],
)
```

#### 2. Adapt your conf.py if needed

```python
# ...
extensions = [
    "sphinx_design",
    "sphinx_needs",
    "sphinxcontrib.plantuml",
    "score_plantuml",
    "score_metamodel",
    "score_draw_uml_funcs",
    "score_source_code_linker",
    "score_layout",
]
# ...
```

Make sure that your conf.py imports all of the extensions you want to enable.


#### 3. Run a documentation build:

```bash
bazel run //path/to/BUILD-file:incremental_latest # documentation at '_build/'
bazel build //path/to/BUILD-file:docs_latest # documentation at 'bazel-bin/
```

#### 4. Access your documentation at

- `_build/` for incremental
- `bazel-bin/bazel-bin/<BUILD FILE FOLDER NAME>/docs/_build/html`

<br>
<br>

> ### *For the full example as well as more complex ones, check out the {doc}`example <example/index>`

---

### Available Targets

Using the `docs` macro enables multiple targets which are now useable.

| Target Name | What it does | How to execute |
|---------------|-----------------------------------------------------------|-----------------|
| docs | Builds documentation in sandbox | `bazel build` |
| incremental | Builds documentation incrementally (faster) | `bazel run` |
| live_preview | Creates a live_preview of the documentation viewable in a local server | `bazel run` |
| ide_support | Creates virtual environment under '.venv_docs' | `bazel run` |
| `html`             | Filegroup that exposes the generated HTML files                              | `bazel build //docs:html`         |
| `html_files`       | Prepares a flattened version of the HTML output for packaging                | `bazel build //docs:html_files`   |
| `github_pages`     | Creates a `.tar` archive from the HTML output (ready for deployment)         | `bazel build //docs:github_pages` |


> For each entry in `docs_targets`, these targets are suffixed accordingly (e.g. `docs_api`, `html_api`, `github_pages_api`).
______________________________________________________________________

## Configuration Options

The `docs()` macro accepts the following arguments:

| Parameter | Description | Required | Default |
|-----------|-------------|----------|---------|
| `conf_dir` | Path to the 'conf.py' containing folder | No | 'docs' |
| `source_dir` | Documentation source files (RST, MD) | No | 'docs' |
| `build_dir_for_incremental` | Output folder for the incremental build | No | '\_build' |
| `docs_targets` | List of dictionaries which allows multi-repo setup | Yes | - |
| `source_files_to_scan_for_needs_links` | List of targets,globs,filegroups that the 'source_code_linker' should parse | No | `[]` |
| `visibility` | Bazel visibility | No | `None` |
