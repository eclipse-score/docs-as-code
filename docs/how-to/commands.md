# Docs-As-Code Commands

## Commands Overview

| Target Name | What it does | How to execute |
|---------------|-----------------------------------------------------------|-----------------|
| docs | Builds documentation | `bazel run //:docs`  |
| live_preview | Creates a live_preview of the documentation viewable in a local server | `bazel run //:live_preview` |
| ide_support | Creates virtual environment under '.venv_docs' | `bazel run //:ide_support` |

### Internal targets (do not use directly)

| Target Name | What it does | How to execute |
|---------------|-----------------------------------------------------------|-----------------|
| needs_json | Creates a 'needs.json' file | `bazel build //:needs_json` |
