import os
import html
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element

from pathlib import Path
from dataclasses import dataclass
from typing import Optional, Any


# We will have everythin as string here as that mirrors the xml file
@dataclass
class TestCaseNeed:
    id: str
    file: str
    lineNr: str
    result: dict[
        str, str
    ]  # passed, "" | falied, "failure text" | skippep, "skipped explanation" | disabled, ""
    TestType: str
    DerivationTechnique: str
    # Either or HAVE to be filled.
    PartiallyVerifies: Optional[list[str]] = None
    FullyVerifies: Optional[list[str]] = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]):
        return cls(**data)

    @classmethod
    def clean_text(cls, text: str):
        decoded = html.unescape(text)
        return str(decoded.replace("\n", " ")).strip()

    def __post_init__(self):
        # Self assertion to double check some mandatory options

        # It's mandatory that the test either partially or fully verifies a requirement
        if self.PartiallyVerifies is None and self.FullyVerifies is None:
            raise ValueError(
                f"TestCase: {self.id} Error. Either 'PartiallyVerifies' or 'FullyVerifies' must be provided."
            )
        # Skipped tests should always have a reason associated with them
        # if "skipped" in self.result.keys() and not list(self.result.values())[0]:
        #     raise ValueError(
        #         f"TestCase: {self.id} Error. Test was skipped without provided reason, reason is mandatory for skipped tests."
        #     )
        # Disabled tests are exempt from needing a description, as this is not possible

        # Cleaning Text
        # Do not know if this is alright, or horrific -_-
        if not list(self.result.values())[0]:
            key = list(self.result.keys())[0]
            self.result[key] = self.clean_text(list(self.result.values())[0])



def parse_testcase_result(testcase: ET.Element) -> dict[str, str]:
    skipped = testcase.find("skipped")
    failed = testcase.find("failure")
    status = testcase.get("status")
    # NOTE: Special CPP case of 'disabled'
    if status is not None and status == "notrun":
        return {"disabled": ""}
    if skipped is None and failed is None:
        return {"passed": ""}
    elif failed is not None:
        return {"failed": failed.get("message", "")}
    elif skipped is not None:
        return {"skipped": skipped.get("message", "")}
    else:
        # This shouldn't happen
        raise ValueError(
            f"Testcase: {testcase.get('name')}. Did not find 'failed', 'skipped' or 'passed' in test"
        )



def parse_properties(case_properties: dict[str, Any], properties: Element):
    for prop in properties:
        prop_name = prop.get("name", "")
        prop_value = prop.get("value", "")
        # We ignore the Description of the test
        if prop_name == "Description":
            continue
        if prop_value.startswith("["):
            list_prop_value: list[str] = [
                x.strip()
                for x in prop_value.replace("[", "").replace("]", "").split(",")
                if x
            ]
            case_properties[prop_name] = list_prop_value
            continue
        case_properties[prop_name] = prop_value
    return case_properties


def read_file(file: Path):
    test_case_needs: list[TestCaseNeed] = []
    tree = ET.parse(file)
    root = tree.getroot()
    for testsuite in root.findall("testsuite"):
        for testcase in testsuite.findall("testcase"):
            case_properties = {}
            testname = testcase.get("name")
            test_file = testcase.get("file")
            lineNr = testcase.get("line")
            # Assert worldview that mandatory things are actually there
            assert testname is not None, (
                f"Testcase: {testcase} does not have a 'name' attribute. This is mandatory"
            )
            assert test_file is not None, (
                f"Testcase: {testname} does not have a 'file' attribute. This is mandatory"
            )
            assert lineNr is not None, (
                f"Testcase: {testname} located in {test_file} does not have a 'lineNr' attribute. This is mandator"
            )
            case_properties["id"] = testname
            case_properties["file"] = testname
            case_properties["lineNr"] = lineNr
            case_properties["result"] = parse_testcase_result(testcase)

            properties_element = testcase.find("properties")
            # HINT: This list is hard coded here, might not be ideal to have that in the long run.
            assert properties_element is not None, (
                f"Testcase: {testname} located in {test_file}:{lineNr}, does not have any properties. Properties 'TestType', 'DerivationTechnique' and either 'PartiallyVerifies' or 'FullyVerifies' are mandatory."
            )
            case_properties = parse_properties(case_properties, properties_element)
            test_case_needs.append(TestCaseNeed.from_dict(case_properties))
    return test_case_needs


def find_xml_files(dir: str):
    test_file_name = "test.xml"

    xml_paths: list[Path] = []
    for root, _, files in os.walk(dir):
        if test_file_name in files:
            xml_paths.append(Path(os.path.join(root, test_file_name)))
    return xml_paths


a = find_xml_files("bazel-testlogs")
print(a)
# print(a[0])
b = read_file(Path("test_rust_xml.xml"))
# print("WENT THROUGH ALL")
for c in b:
    print(c)
