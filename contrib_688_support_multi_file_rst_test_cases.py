"""Support multi-file RST test cases (fix for issue #688)"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Union, List


class RstTestRunner:
    """A test runner that supports both single-file and multi-file RST test cases."""

    def __init__(self, src_dir: Union[str, Path], build_dir: Union[str, Path]):
        self.src_dir = Path(src_dir)
        self.build_dir = Path(build_dir)
        self.app = None  # Placeholder for Sphinx app setup

    def _prepare_test_source(self, test_case: Union[str, Path]) -> Path:
        """Copy the test case (file or directory) into a temporary source directory."""
        test_path = Path(test_case)
        if not test_path.exists():
            raise FileNotFoundError(f"Test case not found: {test_path}")

        temp_src = Path(tempfile.mkdtemp(prefix="rst_test_", dir=self.build_dir))

        if test_path.is_file():
            # Single-file case: copy as index.rst
            dest_file = temp_src / "index.rst"
            shutil.copy2(test_path, dest_file)
        elif test_path.is_dir():
            # Multi-file case: copy entire directory
            for item in test_path.iterdir():
                dest_item = temp_src / item.name
                if item.is_dir():
                    shutil.copytree(item, dest_item)
                else:
                    shutil.copy2(item, dest_item)
        else:
            raise ValueError(f"Invalid test case path: {test_path}")

        return temp_src

    def _validate_warnings(self, warning_log: str, source_files: List[Path]) -> bool:
        """Validate warnings per source file. Returns True if all warnings are expected."""
        for source in source_files:
            expected_warnings_file = source.with_suffix(source.suffix + ".warnings")
            if expected_warnings_file.exists():
                expected = expected_warnings_file.read_text().strip().splitlines()
            else:
                expected = []

            actual = [
                line for line in warning_log.splitlines()
                if f"{source.name}:" in line or "index.rst:" in line  # Handle cross-refs
            ]

            # Simple check - in practice, this would be more sophisticated
            if set(actual) != set(expected):
                print(f"Warning mismatch for {source.name}:")
                print(f"Expected: {expected}")
                print(f"Actual: {actual}")
                return False
        return True

    def run_test(self, test_case: Union[str, Path]) -> bool:
        """Run a single RST test case and return whether it passed."""
        try:
            src_path = self._prepare_test_source(test_case)
            source_files = list(src_path.glob("*.rst"))

            # Simulate building with Sphinx (actual implementation would call Sphinx API)
            warning_log = self._simulate_build(src_path)

            # Validate warnings against expectations
            passed = self._validate_warnings(warning_log, source_files)

            # Cleanup
            shutil.rmtree(src_path, ignore_errors=True)

            return passed
        except Exception as e:
            print(f"Test failed with exception: {e}")
            return False

    def _simulate_build(self, src_path: Path) -> str:
        """Placeholder for actual Sphinx build logic."""
        # In a real implementation, this would use Sphinx's application API
        # to build the project and capture warnings
        return ""


# Example usage:
# runner = RstTestRunner(src_dir="tests/rst", build_dir="builds")
# runner.run_test(Path("tests/rst/multi_doc_case/"))
# runner.run_test(Path("tests/rst/single_doc_case.rst"))

