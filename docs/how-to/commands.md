# Docs-As-Code Commands

## Commands Overview

| Target                      | What it does                                                           |
| --------------------------- | ---------------------------------------------------------------------- |
| `bazel run //:docs`         | Builds documentation                                                   |
| `bazel run //:live_preview` | Creates a live_preview of the documentation viewable in a local server |
| `bazel run //:ide_support`  | Creates virtual environment under '.venv_docs'                         |

### Internal targets (do not use directly)

| Target                      | What it does                |
| --------------------------- | --------------------------- |
| `bazel build //:needs_json` | Creates a 'needs.json' file |
