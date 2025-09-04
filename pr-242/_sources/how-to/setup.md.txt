(getting_started)=
# Setup

⚠️ Only valid for docs-as-code v1.x.x.

## Overview

docs-as-code allows you to easily integrate Sphinx documentation generation into your
Bazel build system. It provides a collection of utilities and extensions specifically
designed to enhance documentation capabilities in S-CORE.

## Features

- Seamless integration with Bazel build system
- S-CORE process compliance
- Support for PlantUML diagrams
- Source code linking capabilities
- S-CORE layouts and themes

## Installation

### 1. /MODULE.bazel file

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

### 2. /BUILD file


```starlark
load("@score_docs_as_code//docs.bzl", "docs")

docs(
    source_dir = "<your sphinx source dir>",
    data = [
        "@other_repo:needs_json",  # Optional, if you have dependencies
    ],
)
```


#### Configuration Options

The `docs()` macro accepts the following arguments:

| Parameter | Description | Required |
|-----------|-------------|----------|
| `source_dir` | Directory of documentation source files (RST, MD) | Yes |
| `data` | List of `needs_json` targets that should be included in the documentation| No |


### 3. Copy conf.py

Copy the `conf.py` file from the `docs-as-code` module to your `source_dir`.


#### 4. Run a documentation build:


```bash
bazel run //:docs
```

#### 5. Access your documentation at

`/_build/index.html`
