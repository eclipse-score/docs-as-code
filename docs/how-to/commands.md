# Commands

| Target                                         | What it does                                                                                      |
| ---------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| `bazel run //:docs`                            | Builds documentation                                                                              |
| `bazel run //:docs_check`                      | Verifies documentation correctness                                                                |
| `bazel run //:docs_combo_experimental`         | Builds combined documentation with all external dependencies included                             |
| `bazel run //:live_preview`                    | Creates a live_preview of the documentation viewable in a local server                            |
| `bazel run //:live_preview_combo_experimental` | Creates a live_preview of the full documentation with all dependencies viewable in a local server |
| `bazel run //:ide_support`                     | Sets up a Python venv for esbonio (Remember to restart VS Code!)                                  |
| `bazel run //:html.serve`                      | Serves the generated HTML documentation on a local web server                                     |

## Internal targets (do not use directly)

| Target                        | What it does                                |
| ----------------------------- | ------------------------------------------- |
| `bazel build //:needs_json`   | Creates a 'needs.json' file                 |
| `bazel build //:docs_sources` | Provides all the documentation source files |
| `bazel build //:html`         | Builds the documentation                    |
