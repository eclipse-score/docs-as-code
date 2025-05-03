# Bazel Sphinx Documentation Builder

A Bazel module providing comprehensive tools and extensions for building Sphinx documentation within Bazel projects.

## Overview

This module allows you to easily integrate Sphinx documentation generation into your Bazel build system. It provides a collection of utilities, extensions, and themes specifically designed to enhance documentation capabilities while maintaining Bazel's reproducible build environment.

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
bazel_dep(name = "docs-as-code", version = "0.1.0")
```

And make sure to also add the S-core bazel registry to your `.bazelrc` file

```starlark
common --registry=https://raw.githubusercontent.com/eclipse-score/bazel_registry/main/  
common --registry=https://bcr.bazel.build
```

______________________________________________________________________

### Basic Usage

#### 1. Import the `docs()` macro in your BUILD file:

```python
load("@docs-as-code//docs.bzl", "docs")

docs(
    conf_dir = "<your sphinc conf dir>",
    source_dir = "<your sphinx source dir>",
    docs_targets = [
        {
            # For more detailed explenation look at the 'docs_targets' section
            "suffix": "",  # This creates the normal 'incremental' and 'docs' target
        },
    ],
    source_files_to_scan_for_needs_links = [
        # Note: you can add filegroups, globs, or entire targets here.
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

Make sure that your conf.py imports all of the extensions you want to enable.\
For a full example look at [This repos conf.py](process-docs/conf.py)

#### 3. Run a documentation build:

```bash
bazel run //path/to/BUILD-file:incremental # documentation at '_build/'
bazel build //path/to/BUILD-file:docs # documentation at 'bazel-bin/
```

#### 4. Access your documentation at

- `_build/` for incremental
- `bazel-bin/bazel-bin/<BUILD FILE FOLDER NAME>/docs/_build/html`

______________________________________________________________________

### Available Targets

Using the `docs` macro enables multiple targets which are now useable.

| Target Name | What it does | How to execute |
|---------------|-----------------------------------------------------------|-----------------|
| docs | Builds documentation in sandbox | `bazel build` |
| incremental | Builds documentation incrementally (faster) | `bazel run` |
| live_preview | Creates a live_preview of the documentation viewable in a local server | `bazel run` |
| ide_support | Creates virtual environment under '.venv_docs' | `bazel run` |

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

## Advanced Usage

### Custom Configuration

#### Docs-targets

!! TODO !!
This should be filled out after the local mutli-repo tests are integrated and we have examples of different configurations

## Available Extensions

This module includes several custom Sphinx extensions to enhance your documentation:

### Score Layout Extension

Custom layout options for Sphinx HTML output.
[Learn more](src/extensions/score_layout/README.md)

### Score Header Service

Consistent header styling across documentation pages.
[Learn more](src/extensions/score_header_service/README.md)

### Score Metamodel

Validation and checking of documentation structure against a defined metamodel.
[Learn more](src/extensions/score_metamodel/README.md)

### Score Source Code Linker

Links between requirements documentation and source code implementations.
[Learn more](src/extensions/score_source_code_linker/README.md)

### Score PlantUML

Integration with PlantUML for generating diagrams.
[Learn more](src/extensions/README.md)

### Score Draw UML Functions

Helper functions for creating UML diagrams.
[Learn more](src/extensions/score_draw_uml_funcs/README.md)
