#!/usr/bin/env bash
set -e
bazel run //:docs_link_check > linkcheck_output.txt || true
