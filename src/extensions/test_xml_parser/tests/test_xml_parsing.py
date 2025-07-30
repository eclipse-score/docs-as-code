import pytest
import shutil
from collections import defaultdict
from junitparser import TestCase, TestSuite, JUnitXml, Skipped, Failure
from junitparser.junitparser import SystemOut

from test_xml_parser.docs_with_testing_info import find_xml_files
from test_xml_parser.testrstwriter import (
    parse_file,
    build_rst_file,
    build_rst_directive,
)

#                    ╭──────────────────────────────────────────────────────────────────────────────╮
#                    │                                    SETUP                                     │
#                    ╰──────────────────────────────────────────────────────────────────────────────╯


@pytest.fixture(scope="session")
def make_tmp_dirs(tmp_path_factory) -> list[str]:
    data_root = tmp_path_factory.mktemp("test_root")
    data_dir1 = data_root / "testing-xml"
    data_dir2 = data_root / "tooling/second_level"
    data_dir3 = data_root / "tests/another.level/level_four"
    path_list = [data_root, data_dir1, data_dir2, data_dir3]
    for p in path_list[1:]:
        p.mkdir(parents=True, exist_ok=True)
    return path_list


@pytest.fixture(scope="session")
def create_sample_xml_files(make_tmp_dirs) -> list:
    """
    Creating XML files for testing
    """
    root, data_dir1, data_dir2, data_dir3 = make_tmp_dirs
    # File 1. Properties & proper formatting
    suite1 = TestSuite("Sample Test Suite")
    # Generate properties
    suite1.add_property("Verifies", "TOOL_REQ__toolchain_sphinx_needs")
    suite1.add_property("Description", "This is a test, a description")
    suite1.add_property("ASIL", "ASIL_D")
    suite1.add_property("Priority", "1")
    suite1.add_property("TestType", "Requirements-based test")
    suite1.add_property("DerivationTechnique", "analysis of requirements")

    # Add test cases
    test1_1 = TestCase("success_test")
    test1_1.time = 1.2
    test2_1 = TestCase("failed_test")
    test2_1.result = Failure("failed")
    test2_1.time = 0.8
    test3_1 = TestCase("skipped_test")
    test3_1.result = Skipped("skipped")
    test3_1.time = 0.0
    test4_1 = TestCase("success_test_2")
    test4_1.time = 0.6
    suite1.add_testcases([test1_1, test2_1, test3_1, test4_1])

    xml1 = JUnitXml()
    xml1.add_testsuite(suite1)
    xml_file1 = data_dir1 / "test.xml"
    xml1.write(str(xml_file1))

    # File 2. No Properties
    suite2 = TestSuite("Sample Test Suite")

    test1_2 = TestCase("success_test")
    test1_2.time = 1.2
    test2_2 = TestCase("failed_test")
    test2_2.result = Failure("failed")
    test2_2.time = 0.8
    test3_2 = TestCase("skipped_test")
    test3_2.result = Skipped("skipped")
    test3_2.time = 0.0
    test4_2 = TestCase("success_test_2")
    test4_2.time = 0.6
    suite2.add_testcases([test1_2, test2_2, test3_2, test4_2])

    xml2 = JUnitXml()
    xml2.add_testsuite(suite2)
    xml_file2 = data_dir2 / "test.xml"
    xml2.write(str(xml_file2))

    # File 3. No Properties & system out (that should be ignored)
    suite3 = TestSuite("Sample Test Suite")

    test1_3 = TestCase("success_test")
    test1_3.time = 1.2
    test2_3 = TestCase("failed_test")
    test2_3.result = Failure("failed")
    test2_3.time = 0.8
    test3_3 = TestCase("skipped_test")
    test3_3.result = Skipped("skipped")
    test3_3.time = 0.0
    test4_3 = TestCase("success_test_2")
    test4_3.time = 0.6
    suite3.add_testcases([test1_3, test2_3, test3_3, test4_3])

    system_msg = SystemOut(
        "This is a system message that should be completly ignored, and not pose any issues"
    )
    suite3.system_out = system_msg

    xml3 = JUnitXml()
    xml3.add_testsuite(suite3)
    xml_file3 = data_dir3 / "test.xml"
    xml3.write(str(xml_file3))
    return [root, data_dir1, data_dir2, data_dir3]


@pytest.fixture(scope="session")
def create_end_dir(tmp_path_factory):
    base_tmp = tmp_path_factory.getbasetemp()
    testfile_root = base_tmp / "tmp_testfiles"
    testfile_root.mkdir(exist_ok=True)
    return testfile_root


@pytest.fixture(scope="session")
def move_xml_files(create_sample_xml_files, create_end_dir):
    testfile_root = create_end_dir
    root, *all_paths = create_sample_xml_files
    total_paths = [str(x) + "/test.xml" for x in all_paths]
    # remove the base directory
    clean_paths = [str(x).split(str(root) + "/")[1] for x in total_paths]
    expected_file_names = [
        str(x)
        .replace("_", "__")
        .replace("/", "_")
        .replace(".", "_", str(x).count(".", 0, -4))
        if str(x).count(".", 0, -4) >= 1
        else str(x).replace("_", "__").replace("/", "_")
        for x in clean_paths
    ]
    # Will generate a dictionary like so
    # bazel-testlogs/sphinx_extensions/test.dir/test_check/test.xml: bazel-testlogs_sphinx_extensions_test__check_test.xml
    xml_file_dict = find_xml_files(root)
    file_locations = []
    for k, v in xml_file_dict.items():
        file_locations.append(shutil.copy2(k, testfile_root / v))
    return file_locations


@pytest.fixture(scope="session")
def create_golden_file(create_end_dir):
    testfile_root = create_end_dir
    output_str = """
TESTING
=======



.. needtable::
   :filter: 'xml-test' in tags and type == 'testcase'
   :columns: id, result
   :style: table
   :style_row: tr_[[copy('result')]]



.. test-file:: tests_another_level_level__four_test
   :file: /tmp/pytest/tmp_testfiles/tests_another_level_level__four_test.xml
   :id: tests_another_level_level__four_test
   :tags: xml-test
   :verifies: {}
   :properties: {}
   :links: [[tr_link("verifies", "id")]]
   :auto_suites:
   :auto_cases:



.. test-file:: tooling_second__level_test
   :file: /tmp/pytest/tmp_testfiles/tooling_second__level_test.xml
   :id: tooling_second__level_test
   :tags: xml-test
   :verifies: {}
   :properties: {}
   :links: [[tr_link("verifies", "id")]]
   :auto_suites:
   :auto_cases:



.. test-file:: testing-xml_test
   :file: /tmp/pytest/tmp_testfiles/testing-xml_test.xml
   :id: testing-xml_test
   :tags: xml-test
   :verifies: TOOL_REQ__toolchain_sphinx_needs
   :properties: {'Description': 'This is a test, a description', 'ASIL': 'ASIL_D', 'Priority': '1', 'TestType': 'Requirements-based test', 'DerivationTechnique': 'analysis of requirements'}
   :links: [[tr_link("verifies", "id")]]
   :auto_suites:
   :auto_cases:


"""
    with open(f"{testfile_root}/golden_file.rst", "w") as f:
        f.write(output_str)


#                    ╭──────────────────────────────────────────────────────────────────────────────╮
#                    │                                  UNIT-TESTS                                  │
#                    ╰──────────────────────────────────────────────────────────────────────────────╯


def test_find_xml_files(create_sample_xml_files):
    root, *all_paths = create_sample_xml_files
    total_paths = [str(x) + "/test.xml" for x in all_paths]
    # remove the base directory
    clean_paths = [str(x).split(str(root) + "/")[1] for x in total_paths]

    expected_file_names = [
        str(x)
        .replace("_", "__")
        .replace("/", "_")
        .replace(".", "_", str(x).count(".", 0, -4))
        if str(x).count(".", 0, -4) >= 1
        else str(x).replace("_", "__").replace("/", "_")
        for x in clean_paths
    ]

    # Will generate a dictionary like so
    # bazel-testlogs/sphinx_extensions/test.dir/test_check/test.xml: bazel-testlogs_sphinx_extensions_test__check_test.xml
    xml_file_dict = find_xml_files(root)
    # Testing our expetation against how the function truly works
    for k, v in xml_file_dict.items():
        assert k in total_paths
        assert v in expected_file_names


def test_parse_file(move_xml_files):
    locations = move_xml_files
    for path in locations:
        info_dict = {}
        str_path = str(path)
        info_dict = defaultdict(dict)
        dict_to_test = parse_file(str_path)
        if "testing-xml" in str_path:
            info_dict = {
                "verifies": "TOOL_REQ__toolchain_sphinx_needs",
                "metadata": {
                    "Description": "This is a test, a description",
                    "ASIL": "ASIL_D",
                    "Priority": "1",
                    "TestType": "Requirements-based test",
                    "DerivationTechnique": "analysis of requirements",
                },
                "filename": str_path.split("/")[-1].removesuffix(".xml"),
                "filepath": str_path,
            }
        elif "tooling" in str_path:
            info_dict = {
                "filename": str_path.split("/")[-1].removesuffix(".xml"),
                "filepath": str_path,
            }
        elif "tests" in str_path:
            info_dict = {
                "filename": str_path.split("/")[-1].removesuffix(".xml"),
                "filepath": str_path,
            }
        else:
            assert False, (
                "Did not find either of ['testing-xml', 'tooling', 'tests'] in the str_paths"
            )
        assert dict_to_test == info_dict


def test_build_directive(move_xml_files):
    locations = move_xml_files
    for path in locations:
        str_path = str(path)
        info = parse_file(str_path)
        output_str = f"""
.. test-file:: {info["filename"]}
   :file: {info["filepath"]}
   :id: {info["filename"]}
   :tags: xml-test
   :verifies: {info["verifies"]}
   :properties: {info["metadata"]}
   :links: [[tr_link("verifies", "id")]]
   :auto_suites:
   :auto_cases:
"""
        directive_to_test = build_rst_directive(info)
        # testing complete equality
        assert directive_to_test == output_str
        # testing spaces. 3 spaces are requiered in the begining to make it a valid rst option
        options_to_test = [
            x
            for x in directive_to_test.split("\n")
            if x != "" and not x.startswith("..")
        ]
        for option in options_to_test:
            assert option.startswith("   ")


#                    ╭──────────────────────────────────────────────────────────────────────────────╮
#                    │                               End to End test                                │
#                    ╰──────────────────────────────────────────────────────────────────────────────╯


def test_build_rst_file(move_xml_files, create_end_dir, create_golden_file):
    create_golden_file
    testfile_root = create_end_dir
    locations = move_xml_files
    build_rst_file([str(x) for x in locations], testfile_root, "TESTING")
    file_to_test = testfile_root / "test.rst"
    golden_file = testfile_root / "golden_file.rst"
    with open(file_to_test, "r") as f:
        file_to_test_content = f.read()
    with open(golden_file, "r") as f:
        golden_file_content = f.read()
    assert file_to_test_content == golden_file_content
