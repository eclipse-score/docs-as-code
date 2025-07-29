import os
from pathlib import Path
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Optional, Any


# We will have everythin as string here as that mirrors the xml file
@dataclass
class TestCaseNeed():
    id: str
    file: str
    lineNr: str 
    result: str # passed, falied, skipped, disabled
    TestType: str
    DerivationTechnique: str
    failureText: Optional[str] = None
    # Mandatory if result == skipped
    skippedText: Optional[str] = None
    disabledText: Optional[str] = None
    # Either or HAVE to be filled.
    PartiallyVerifies: Optional[list[str]] = None
    FullyVerifies: Optional[list[str]] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(**data)

    @classmethod
    def clean_text(cls, text:str):
        return text.replace("\n", " ").lstrip().rstrip()

    def __post_init__(self):
        # Self assertion to double check some mandatory options

        # It's mandatory that the test either partially or fully verifies a requirement
        if self.PartiallyVerifies is None and self.FullyVerifies is None:
            raise ValueError(f"TestCase: {self.id} Error. Either 'PartiallyVerifies' or 'FullyVerifies' must be provided.")
        # Skipped tests should always have a reason associated with them
        if self.result == "skipped" and self.skippedText is None:
            raise ValueError(f"TestCase: {self.id} Error. Test was skipped without reason")
        # Disabled tests are exempt from needing a description.

        # Cleaning Text
        if self.failureText is not None:
            self.failureText = self.clean_text(self.failureText)
        if self.skippedText is not None:
            self.skippedText = self.clean_text(self.skippedText)
        if self.disabledText is not None:
            self.disabledText = self.clean_text(self.disabledText)


# TODO: Unsure if this is even useful.
@dataclass
class TestFileResults():
    cases: int
    passed: int 
    failed: int
    skipped: int
    disabled: int




def parse_testcase_result_rust(testcase:ET.Element): 
    skipped = testcase.find('skipped')
    failed =testcase.find("failure")
    if skipped is None and failed is None:
        return "passed" 
    elif failed is not None:
        if failed.text is not None:
            clean_text(failed.text)
        return "failed"
    elif skipped is not None:
        if skipped.text is not None:
            clean_text(skipped.text)
        return "skipped"


def parse_testcase_result_python(testcase: ET.Element)-> tuple[str, str|None]:
    skipped = testcase.find('skipped')
    failed =testcase.find("failure")
    if skipped is None and failed is None:
        return "passed", None
    elif failed is not None:
        return "failed", failed.get("message")
    elif skipped is not None:
        return "skipped", skipped.get("message")
    else:
        # This shouldn't happen
        raise ValueError(f"Testcase: {testcase.get('name')}. Did not find 'failed', 'skipped' or 'passed' in test")

def parse_testcase_result_cpp(testcase: ET.Element):
    status = testcase.get("status", "")
    pass

def aggregate_testfile_stats(tfr: TestFileResults, testcase: TestCaseNeed)->TestFileResults:
    tfr.cases += 1
    if testcase.result == "passed":
        tfr.passed += 1
    if testcase.result == "failed":
        tfr.failed += 1
    if testcase.result == "skipped":
        tfr.skipped += 1
    return tfr

def read_file(file: Path):
    test_case_needs:list[TestCaseNeed] = []
    tree = ET.parse(file)
    root = tree.getroot()
    for testsuite in root.findall('testsuite'):
        for testcase in testsuite.findall('testcase'):
            case_properties = {}
            case_properties["id"] = testcase.get("name", "")
            case_properties["file"] = testcase.get('file', "")
            case_properties["lineNr"] = testcase.get('line', "")
            case_properties["result"] = testcase.get('result', "")
            # Check which parsing to choose
            if case_properties["file"].endswith(".py"):
                parse_testcase_result_python(testcase)
            elif case_properties["file"].endswith(".rs"):
                parse_testcase_result_rust(testcase)
            elif case_properties["file"].endswith(".cpp"):
                parse_testcase_result_cpp(testcase)

            properties_element = testcase.find('properties')
            if properties_element is None:
                continue
            for prop in properties_element:
                prop_name = prop.get("name", "")
                prop_value = prop.get("value", "")
                if prop_name == "Description":
                    continue
                if prop_value.startswith("["):
                    list_prop_value:list[str] = [x.strip() for x in prop_value.replace("[", "").replace("]","").split(",") if x]
                    case_properties[prop.get("name")] = list_prop_value
                    continue
                case_properties[prop.get('name')] = prop.get('value')
            #print(case_properties)
            tcn = TestCaseNeed.from_dict(case_properties)  
            test_case_needs.append(tcn)
    return test_case_needs            

def find_xml_files(dir: str): 
    test_file_name = "test.xml"

    xml_paths: list[Path] = []
    for root, _, files in os.walk(dir):
        if test_file_name in files:
            xml_paths.append(Path(os.path.join(root, test_file_name)))
    return xml_paths

a = find_xml_files("bazel-testlogs")
#print(a[0])
b = read_file(Path('test_rust_xml.xml'))
#print(b)
