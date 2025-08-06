import os
import xml.etree.ElementTree as ET
import json
import itertools

from xml.etree.ElementTree import Element
from pathlib import Path
from typing import Any

from sphinx.application import Sphinx
from sphinx.environment import BuildEnvironment
from sphinx_needs import logging
from sphinx_needs.api import generate_need
from sphinx_needs.utils import NeedsSphinxConfig
from sphinx_needs.data import SphinxNeedsData


from src.extensions.score_source_code_linker.generate_source_code_links_json import (
    find_ws_root,
)
from src.extensions.score_source_code_linker.testlink import (
    TestCaseNeed,
    store_test_xml_parsed_json
)

logger = logging.get_logger(__name__)



def parse_testcase_result(testcase: ET.Element) -> tuple[str, str]:
    skipped = testcase.find("skipped")
    failed = testcase.find("failure")
    status = testcase.get("status")
    # NOTE: Special CPP case of 'disabled'
    if status is not None and status == "notrun":
        return "disabled", ""
    if skipped is None and failed is None:
        return "passed", ""
    elif failed is not None:
        return "failed", failed.get("message", "")
    elif skipped is not None:
        return "skipped", skipped.get("message", "")
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
        case_properties[prop_name] = prop_value
        # if prop_value.startswith("["):
        #     list_prop_value: list[str] = [
        #         x.strip()
        #         for x in prop_value.replace("[", "").replace("]", "").split(",")
        #         if x
        #     ]
        #     case_properties[prop_name] = list_prop_value
        #     continue
    return case_properties


def read_file(file: Path)-> tuple[list[TestCaseNeed], list[str]]:
    test_case_needs: list[TestCaseNeed] = []
    non_prop_tests: list[str] = []
    tree = ET.parse(file)
    root = tree.getroot()

    for testsuite in root.findall("testsuite"):
        for testcase in testsuite.findall("testcase"):
            case_properties = {}
            testname = testcase.get("name")
            assert testname is not None, (
                f"Testcase: {testcase} does not have a 'name' attribute. This is mandatory. This should not happen, something is wrong."
            )
            test_file = testcase.get("file")
            lineNr = testcase.get("line")
            # Assert worldview that mandatory things are actually there
            # Disabled temporarily
            # assert test_file is not None, (
            #     f"Testcase: {testname} does not have a 'file' attribute. This is mandatory"
            # )
            # assert lineNr is not None, (
            #     f"Testcase: {testname} located in {test_file} does not have a 'lineNr' attribute. This is mandator"
            # )
            case_properties["id"] = testname
            case_properties["file"] = test_file
            case_properties["lineNr"] = lineNr
            case_properties["result"], case_properties["result_text"] = parse_testcase_result(testcase)

            properties_element = testcase.find("properties")
            # HINT: This list is hard coded here, might not be ideal to have that in the long run.
            if properties_element is None:
                non_prop_tests.append(testname)
                continue
            # assert properties_element is not None, (
            #     f"Testcase: {testname} located in {test_file}:{lineNr}, does not have any properties. Properties 'TestType', 'DerivationTechnique' and either 'PartiallyVerifies' or 'FullyVerifies' are mandatory."
            # )
            case_properties = parse_properties(case_properties, properties_element)
            test_case_needs.append(TestCaseNeed.from_dict(case_properties))
    #logger.warning(test_case_needs)
    return test_case_needs, non_prop_tests


def find_xml_files(dir: Path):
    test_file_name = "test.xml"

    xml_paths: list[Path] = []
    for root, _, files in os.walk(dir):
        if test_file_name in files:
            xml_paths.append(Path(os.path.join(root, test_file_name)))
    #logger.warning(f"XML PATHS: {xml_paths}")
    return xml_paths


def run_xml_parser(app: Sphinx, env: BuildEnvironment):
    ws_root = find_ws_root()
    assert ws_root is not None
    bazel_testlogs = ws_root / "bazel-testlogs"
    xml_file_paths = find_xml_files(bazel_testlogs)
    test_case_needs =  generate_test_needs(app, env, xml_file_paths)
    #a = list(itertools.chain.from_iterable([tcn.to_dict() for tcn in test_case_needs]))
    output = list(itertools.chain.from_iterable(tcn.to_dict() for tcn in test_case_needs))
    logger.warning(f"WOW THIS IS OUTPUT: {output}")
    # This is not ideal, due to duplication, but I can't think of a better solution right now
    store_test_xml_parsed_json(Path(app.outdir)/"score_xml_parser_cache.json", output)




def generate_test_needs(app: Sphinx, env: BuildEnvironment,xml_paths: list[Path]) -> list[TestCaseNeed]:
    # TODO: Delete?
    tcns: list[TestCaseNeed] =[]
    for f in xml_paths:
        #logger.warning(f"XML FILE: {f}")
        b, z = read_file(f)
        for non_prop_test in z:
            logger.warning(f"Test: {non_prop_test} has no properties. Could not create need")
        # Now we build the needs from it
        tcns.extend(b)
        for c in b:
            construct_need(app, c, env)
    return tcns 
    #logger.warning(str([x for x in tcns]))
    save_json(app.outdir,tcns)


def construct_need(app: Sphinx, tn: TestCaseNeed, env: BuildEnvironment):
    a = NeedsSphinxConfig(app.config)
    need = generate_need(
            needs_config=a, 
            docname="index",
            lineno=1,
            need_type= "testcase", 
            title=tn.id, 
            tags="TEST",
            id=f"testcase__{tn.id}",
            # Unsure if I should make them as links here already. As the backlinks are shot.
            fully_verifies=tn.FullyVerifies if tn.FullyVerifies is not None else "",
            partially_verifies=tn.PartiallyVerifies if tn.PartiallyVerifies is not None else "",
            test_type=tn.TestType,
            derivation_technique=tn.DerivationTechnique,
            file=tn.file,
            lineNr=tn.lineNr,
            result=tn.result, # We just want the 'failed' or whatever
            result_text=tn.result_text if tn.result_text else ""
    )
    Needs_Data = SphinxNeedsData(env)
    Needs_Data.add_need(need)
    #nd = Needs_Data.get_needs_view()
    # logger.warning("===========================================================================")
    # logger.warning(f"Total needs after adding: {len(nd)}")
    # if need['id'] in nd:
    #     logger.warning(f"Successfully added need: {need['id']}")
    # else:
    #     logger.warning(f"Failed to add need: {need['id']}")
    # logger.warning("===========================================================================")

    #logger.warning(f"OUTPUT: {output}")

# def build_needs(app: Sphinx, tns: list[TestCaseNeed]):
#     for testcase in tns:
#         construct_need()


