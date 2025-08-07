from collections import defaultdict
from junitparser import JUnitXml


def build_rst_directive(info: dict[str, str]):
    """
    Builds rst compliant directives for a given test-file
    It automatically links the id's listed in verifies to the needs via the dynamic function

    input:
        info (dict[str,str]): Dictionary output from the `parse_file` function.
                              Containing various data about the parsed xml file.

    Example:

    input:
    ======
        {
            "verifies": "TOOL_REQ__toolchain_sphinx_needs_build__requirement_linkage_status_check",
            "metadata": {
                        'Description': 'It should check the traceability like linkage of attributes.',
                        'ASIL': 'ASIL_D',
                        'Priority': '1',
                        'TestType': 'Requirements-based test',
                        'DerivationTechnique': 'Analysis of requirements'
                         }
            "filename": tools_sphinx_extensions_test_requirements_checks_test_checks_test
            "filepath": testfiles/tools_sphinx_extensions_test_requirements_checks_test_checks_test.xml
        }

    output:
    =======
    .. test-file:: tools_sphinx_extensions_test_requirements_checks_test_checks_test
       :file: testfiles/tools_sphinx_extensions_test_requirements_checks_test_checks_test.xml
       :id: tools_sphinx_extensions_test_requirements_checks_test_checks_test
       :verifies: TOOL_REQ__toolchain_sphinx_needs_build__requirement_linkage_status_check
       :properties: {'Description': 'It should check the traceability like linkage of attributes.', 'ASIL': 'ASIL_D', 'Priority': '1', 'TestType': 'Requirements-based test', 'DerivationTechnique': 'Analysis of requirements'}
       :links: [[tr_link("verifies", "id")]]

    """

    return f"""
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


def parse_file(file: str) -> dict[str, str]:
    """
    Parsing the test.xml file into a dictionary.
    Infos extracted are:

    Verifies: str # Comma seperated
    Filename: str # Pure filename
    Filepath: str
    Metadata: dict[str,str] # All other properties defined in the test besides `verifies`

    input:
    ======
        file (str): Filepath to the test.xml that should be parsed

    Example:

    input:
    ======
        file: "testfiles/tools_sphinx_extensions_test_requirements_checks_test_checks_test.xml"

    Properties of the file look like this:
    <properties>
        <property name="Verifies"
            value="TOOL_REQ__toolchain_sphinx_needs_build__requirement_linkage_status_check" />
        <property name="Description"
            value="It should check the traceability like linkage of attributes." />
        <property name="ASIL" value="ASIL_D" />
        <property name="Priority" value="1" />
        <property name="TestType" value="Requirements-based test" />
        <property name="DerivationTechnique" value="Analysis of requirements" />
    </properties>

    output:
    =======
    {
        "verifies": "TOOL_REQ__toolchain_sphinx_needs_build__requirement_linkage_status_check",
        "metadata": {
                    'Description': 'It should check the traceability like linkage of attributes.',
                    'ASIL': 'ASIL_D',
                    'Priority': '1',
                    'TestType': 'Requirements-based test',
                    'DerivationTechnique': 'Analysis of requirements'
                     }
        "filename": tools_sphinx_extensions_test_requirements_checks_test_checks_test
        "filepath": testfiles/tools_sphinx_extensions_test_requirements_checks_test_checks_test.xml
    }
    """
    info_dict = defaultdict(dict)
    xml = JUnitXml.fromfile(file)
    for suite in xml:
        for prop in suite.properties():
            if prop.name == "Verifies":
                info_dict["verifies"] = prop.value
                continue
            info_dict["metadata"].update({prop.name: prop.value})
    info_dict["filename"] = file.split("/")[-1].removesuffix(".xml")
    info_dict["filepath"] = file
    return info_dict


def build_rst_file(files: list[str], outputpath: str, model: str):
    """
    Calling all other functions and putting all files found in a single module together
    Writing a valid rst file as output.

    input:
    ======
        files (list[str]): A list of filepaths to all the test files you want to parse
        outputpath (str): The path where a `test.rst` should be saved
        model (str): This dictactes the title of the written rst file
    """
    output = f"""
{model}
{"=" * len(model)}
\n\n
.. needtable::
   :filter: 'xml-test' in tags and type == 'testcase'
   :columns: id, result
   :style: table
   :style_row: tr_[[copy('result')]]
\n
"""
    for file in files:
        test_info = parse_file(file)
        output += build_rst_directive(test_info) + "\n\n"
    with open(f"{outputpath}/test.rst", "w") as f:
        f.write(output)


# build_rst_file(["/home/maxi/tmp/platform/testfiles/tools_sphinx_extensions_test_requirements_checks_test_checks_test.xml"],"","Testfiles")
