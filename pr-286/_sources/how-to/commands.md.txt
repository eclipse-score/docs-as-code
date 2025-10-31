# Commands

⚠️ Only valid for docs-as-code v1.x.x.

| Target                      | What it does                                                           |
| --------------------------- | ---------------------------------------------------------------------- |
| `bazel build //:html`       | Builds documentation in Bazel sandbox                                  |
| `bazel run //:docs`         | Builds documentation outside of Bazel                                  |
| `bazel run //:live_preview` | Creates a live_preview of the documentation viewable in a local server |
| `bazel run //:ide_support`  | Sets up a Python venv for esbonio (Remember to restart VS Code!)       |

## Internal targets (do not use directly)

| Target                        | What it does                |
| ----------------------------- | --------------------------- |
| `bazel build //:needs_json`   | Creates a 'needs.json' file |
| `bazel build //:docs_sources` | Sources like rst files      |
