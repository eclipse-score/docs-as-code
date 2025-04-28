# File based rule checks

## Test Function
The functionality of the Sphinx build rules can be verified with test rst files.

The function *test_check_rules* in *test_rules_file_based.py* is executed for
each rst file in the directory *rst*.
It creates a SphinxTestApp and a document source folder with an index.rst file
that contains a toctree with the given rst file.

It uses the SphinxTestApp to build the documentation and checks for the
**expected/not expected** warnings.

## Create a test rst file
To add a new test case create a new rst file in the rst directory.
The test files can also be organized in a subfolder structure below directory rst.
The test files are expected to contain the following format:

    #EXPECT: <warning message>
    #EXPECT-NOT: <warning message>

    <need information>

**\<warning message>**<br>
Message text which is expected/not expected during the
                    Sphinx build to be shown.
                    This message is checked for the Sphinx-Needs directive
                    specified after the EXPECT/EXPECT-NOT statement.

**\<need information>**<br>
One or more Sphinx-Needs directives needed for the
                    Sphinx document build

**Example:**

    EXPECT: std_wp__test__abcd: is missing required option: `status`.

    .. std_wp:: Test requirement
        :id: std_wp__test__abcd

This example verifies that the warning message
*std_wp__test__abcd: is missing required option: `status`*
is shown during the Sphinx build.
