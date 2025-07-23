#!/usr/bin/env bash
set -euo pipefail

# ---
# DR1: Tests are executed via Bazel rather than running pytest directly.
#
# Con: this is rather slow compared to running pytest directly.
# Con: Each test target produces its own test result file, so they must be merged into a
#      single report after the tests are run. See `merge_junit.py` for the merging logic.
# Pro: it allows for the usual Bazel caching magic (per test target).
# ---

# ---
# DR2: ide_support is not executed from this script, as it just kills iteration time. It
# must be run manually before running this script to ensure the environment is prepared.
# This can easily result into quite a mess, but it is not a problem for CI.
#
# echo "🧩 Preparing environment..."
# bazel run //src:ide_support
# ---

echo "🧪 Running all tests with Bazel..."
bazel test //src/...

echo "🔍 Finding test.xml files from Bazel test logs..."
find bazel-testlogs/src -name 'test.xml' > .junit_files.txt

if [ ! -s .junit_files.txt ]; then
  echo "❌ No JUnit XML files found (bazel-testlogs/**/test.xml)"
  exit 1
fi

echo "📦 Merging test.xml files..."
.venv/bin/python3 merge_junit.py $(cat .junit_files.txt | tr '\n' ' ') .junit_merged.xml

echo "✅ Merged JUnit XML is available at: .junit_merged.xml"
