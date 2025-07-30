import os
import sys
import subprocess
from pathlib import Path
from test_xml_parser.testrstwriter import build_rst_file


# TESTED
def find_xml_files(dir: str) -> dict[str, str]:
    """
    Recoursively goes through all directories inside `bazel-testlogs` and finds
    any of the files that is named `test.xml`.
    It then creates a dictionary with original fielpath as well as new filename
    It replaces all '/' inside the original filepath with '_'.
    If there is a '_' inside the filename it will be replaced with '__' to showcase that the original directory had
    underscore naming.

    input:
    ======
        dir (str): Path to 'bazel-testlogs' directory

    output:
    ======
        dict:
            {"bazel-testlogs/tools/sphinx_extensions/test/requirements/checks/test_checks/test.xml":
                    "tools_sphinx_extensions_test_requirements_checks_test__checks_test.xml"}
    """
    test_file_name = "test.xml"

    xml_paths = {}
    for root, _, files in os.walk(dir):
        if test_file_name in files:
            xml_path = Path(os.path.join(root, test_file_name))
            print(xml_path)
            # folder = Path(root).name
            # file_renamed_raw = str(xml_path).split(str(dir) + "/")[1]
            xml_paths[str(xml_path)] = xml_path
    return xml_paths


# Finding the right workspace path from bazel ──────────────
if __name__ == "__main__":
    workspace = os.getenv("BUILD_WORKSPACE_DIRECTORY")
    if not workspace:
        sys.exit(
            "This script must be run from Bazel via `bazel run //docs:docs_with_testing_info`."
        )

    # sphinx will print relative paths to the current directory.
    # Change to the workspacke root so that the paths are readable.
    os.chdir(workspace)

    # Running all tests via bazel to create `bazel-testlogs` ──────────────
    subprocess.run(["bazel", "test", "//..."])

    # Sanity check, if bazel-testlogs does not exists, something went wrong.
    current_dir = os.getcwd()
    testlog_dir = os.path.join(current_dir, "bazel-testlogs")
    if not os.path.exists(testlog_dir):
        sys.exit(
            "Something went wrong. `bazel-testlogs` not created after running `bazel test //...`"
        )

    test_file_paths = find_xml_files(testlog_dir)

    # Making directory if needed and moving + renaming files ────────
    # TODO: Get the module dynamically instead of just hardcoding it.
    os.system("mkdir -p testfiles")

    # Moving all files to the correct folder ────────
    for k, v in test_file_paths.items():
        subprocess.run(["cp", k, f"./testfiles/{v}"])  #

    # Generating correct list of paths for the builder ────────
    files = [f"testfiles/{x}" for x in test_file_paths.values()]

    # Creating final rst output file and writing it ────────
    build_rst_file(files, "testfiles", "Tests From Platform")

    # After generating & saving the resulting rst, we build the documentation ────────
    subprocess.run(["bazel", "build", "//docs:docs"])
