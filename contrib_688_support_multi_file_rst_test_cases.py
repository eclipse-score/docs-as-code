# Support multi-file RST test cases (fix for issue #688)

```python
import os
import shutil
import tempfile
import subprocess
import re
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass

@dataclass
class TestResult:
    success: bool
    warnings: List[Tuple[str, int, str]]  # (filename, line_number, message)
    error: Optional[str] = None

class RSTTestRunner:
    """Supports both single-file and multi-file RST test cases for Sphinx validation."""
    
    def __init__(self, srcdir: str = None):
        self.srcdir = srcdir or os.path.dirname(os.path.abspath(__file__))
        self.build_dir = None
        
    def _is_multifile_testcase(self, testcase_path: Path) -> bool:
        """Check if testcase is a directory with index.rst or contains multiple .rst files."""
        if testcase_path.is_dir():
            return (testcase_path / "index.rst").exists() or \
                   len(list(testcase_path.glob("*.rst"))) > 1
        return False
    
    def _copy_testcase_to_temp(self, testcase_path: Path, temp_dir: Path) -> Path:
        """Copy testcase (file or directory) to temporary directory."""
        if testcase_path.is_dir():
            dest = temp_dir / testcase_path.name
            shutil.copytree(testcase_path, dest)
            return dest
        else:
            dest = temp_dir / testcase_path.name
            shutil.copy2(testcase_path, dest)
            return dest
    
    def _build_sphinx_project(self, src_path: Path, build_path: Path) -> TestResult:
        """Build Sphinx project and collect warnings."""
        try:
            # Ensure build directory exists
            build_path.mkdir(parents=True, exist_ok=True)
            
            # Run Sphinx build
            result = subprocess.run(
                [
                    "sphinx-build",
                    "-b", "html",
                    "-W",  # Turn warnings into errors for validation
                    str(src_path),
                    str(build_path)
                ],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            # Parse warnings from stderr
            warnings = self._parse_sphinx_warnings(result.stderr)
            
            # Return success if no warnings (since we use -W)
            return TestResult(
                success=result.returncode == 0,
                warnings=warnings,
                error=None if result.returncode == 0 else result.stderr
            )
            
        except subprocess.TimeoutExpired:
            return TestResult(
                success=False,
                warnings=[],
                error="Sphinx build timed out"
            )
        except Exception as e:
            return TestResult(
                success=False,
                warnings=[],
                error=str(e)
            )
    
    def _parse_sphinx_warnings(self, stderr: str) -> List[Tuple[str, int, str]]:
        """Parse Sphinx warnings into structured format."""
        warnings = []
        # Pattern matches: path/to/file.rst:line: severity: message
        pattern = r'([^:]+):(\d+):\s*(\w+):\s*(.+)'
        
        for line in stderr.split('\n'):
            match = re.search(pattern, line)
            if match:
                filepath, lineno, severity, message = match.groups()
                # Extract just the filename for clarity
                filename = os.path.basename(filepath)
                warnings.append((filename, int(lineno), f"{severity}: {message}"))
        
        return warnings
    
    def run_single_file_test(self, rst_file: Path) -> TestResult:
        """Run test for a single RST file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal conf.py
            conf_file = temp_path / "conf.py"
            conf_content = """
project = 'Test'
extensions = ['sphinx.ext.needs']
html_theme = 'basic'
"""
            conf_file.write_text(conf_content)
            
            # Copy RST file
            rst_dest = temp_path / rst_file.name
            shutil.copy2(rst_file, rst_dest)
            
            # Build
            build_path = temp_path / "_build"
            return self._build_sphinx_project(temp_path, build_path)
    
    def run_multifile_test(self, testcase_dir: Path) -> TestResult:
        """Run test for a multi-file testcase directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create minimal conf.py in the testcase directory
            conf_file = testcase_dir / "conf.py"
            if not conf_file.exists():
                conf_content = """
project = 'Test'
extensions = ['sphinx.ext.needs']
html_theme = 'basic'
"""
                conf_file.write_text(conf_content)
            
            # Copy entire directory
            dest_dir = temp_path / testcase_dir.name
            shutil.copytree(testcase_dir, dest_dir)
            
            # Build
            build_path = temp_path / "_build"
            result = self._build_sphinx_project(dest_dir, build_path)
            
            # For multi-file tests, filter warnings to only include files in the testcase
            filtered_warnings = [
                w for w in result.warnings 
                if w[0] in [f.name for f in testcase_dir.glob("*.rst")] or w[0] == "index.rst"
            ]
            
            return TestResult(
                success=result.success,
                warnings=filtered_warnings,
                error=result.error
            )
    
    def run_test(self, testcase_path: str) -> TestResult:
        """
        Run an RST test case.
        
        Args:
            testcase_path: Path to either a single .rst file or a directory containing
                          an index.rst and related files.
        
        Returns:
            TestResult with success status and any warnings.
        """
        path = Path(testcase_path)
        
        if not path.exists():
            return TestResult(
                success=False,
                warnings=[],
                error=f"Test case not found: {testcase_path}"
            )
        
        if path.is_dir():
            if not self._is_mult
