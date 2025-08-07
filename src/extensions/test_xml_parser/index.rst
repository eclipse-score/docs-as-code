Test XML parser
===============

Overview
--------
The 'Test XML parser' is a tool that automatically collects, parses and generates formatted `junitxml` test reports 
from the Bazel test results. It creates an overview page with all test-case results and links any of the test-files to 
requirements if possible.

Usage 
-----
To use the 'Test XML parser' all you have to do is execute the following command::
    bazel run //docs:build_with_testing_info

This executes a python script (located at 'tools/sphinx_extensions/build/test_xml_parser/test_xml_parser/').
The script executes the following steps in order: 

1. Executes all tests via bazel with the `bazel test //...` command. 
2. Locates all `test.xml` files within the `bazel-testlog` folder 
3. Moves and renames all files found from their original place to the `testfiles/` folder. Renaming them with the following rules. 

   '_' -> '__'

   '/' -> '_'

   '.' -> '_' (except for the .xml)

4. Reads all files inside `testfiles/`, parses them and extracts information out of them.
5. Aggregates parsed information into a `test.rst` file located inside `testfiles/`.

The file shows the following things: 

1. Table of test-cases with their status color coded (Green = pass, Red = failed, Grey = skipped)
2. A need for each test-file found with all metadata included as well as any links to other requirements if possible
3. A need for each test-suite inside each of the files
4. A need for each test-case inside each of the test-suites

Here is a snipped of what a created file could look like:: 
 # insert testcases-preview image here


