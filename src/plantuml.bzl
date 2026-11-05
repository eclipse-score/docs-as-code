"""Bazel executable wrapper for platform-specific PlantUML native releases."""


def _plantuml_impl(ctx):
    toolchain = ctx.toolchains["//src:plantuml_toolchain_type"]
    launcher = ctx.actions.declare_file(ctx.label.name)
    binary = toolchain.binary
    relative_path = binary.short_path
    if relative_path.startswith("../"):
        relative_path = relative_path[3:]

    if toolchain.windows:
        content = """@echo off\r
setlocal\r
if not defined RUNFILES_DIR (\r
  echo Cannot locate PlantUML runfiles directory 1>&2\r
  exit /b 1\r
)\r
\"%RUNFILES_DIR%\\{binary}\" %*\r
exit /b %ERRORLEVEL%\r
""".format(binary = relative_path.replace("/", "\\"))
    else:
        content = """#!/usr/bin/env bash
set -euo pipefail
if [[ -n \"${{RUNFILES_DIR:-}}\" ]]; then
  runfiles=\"$RUNFILES_DIR\"
elif [[ -d \"$0.runfiles\" ]]; then
  runfiles=\"$0.runfiles\"
else
  echo \"Cannot locate PlantUML runfiles directory\" >&2
  exit 1
fi
exec \"$runfiles/{binary}\" \"$@\"
""".format(binary = relative_path)

    ctx.actions.write(output = launcher, is_executable = True, content = content)
    return DefaultInfo(
        executable = launcher,
        runfiles = ctx.runfiles(
            files = [binary],
            transitive_files = toolchain.runtime,
        ),
    )


plantuml_binary = rule(
    implementation = _plantuml_impl,
    executable = True,
    toolchains = ["//src:plantuml_toolchain_type"],
)
