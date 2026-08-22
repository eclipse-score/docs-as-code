"""missing consistency check during metamodel parsing (fix for issue #737)"""

import re
from pathlib import Path
from collections import defaultdict

class MetamodelConsistencyChecker:
    def __init__(self, metamodel_dir: str):
        self.metamodel_dir = Path(metamodel_dir)
        self.errors = []
        self.model_elements = {}
        self.references = defaultdict(list)

    def _parse_element(self, file_path: Path):
        content = file_path.read_text(encoding='utf-8')
        element_match = re.search(r'@startuml\s+(\w+)', content)
        if element_match:
            element_name = element_match.group(1)
            self.model_elements[element_name] = file_path
        ref_matches = re.findall(r'(\w+)\s*(?:-->|->|..)\s*(\w+)', content)
        for source, target in ref_matches:
            self.references[source].append((target, file_path.name))

    def _check_references(self):
        all_elements = set(self.model_elements.keys())
        for source, refs in self.references.items():
            if source not in all_elements:
                self.errors.append(f"Reference source '{source}' not defined in any metamodel file")
            for target, file_name in refs:
                if target not in all_elements:
                    self.errors.append(f"Reference target '{target}' from '{file_name}' -> '{target}' is not defined")

    def _check_duplicate_definitions(self):
        seen = {}
        for element_name, file_path in self.model_elements.items():
            if element_name in seen:
                self.errors.append(f"Duplicate definition of element '{element_name}': {seen[element_name]} and {file_path}")
            else:
                seen[element_name] = file_path

    def check(self):
        for file_path in self.metamodel_dir.rglob('*.puml'):
            self._parse_element(file_path)
        self._check_duplicate_definitions()
        self._check_references()
        return {'consistent': len(self.errors) == 0, 'errors': self.errors}

def check_metamodel_consistency(metamodel_directory: str) -> dict:
    checker = MetamodelConsistencyChecker(metamodel_directory)
    return checker.check()

