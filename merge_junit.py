import sys

from junitparser import JUnitXml

if len(sys.argv) < 3:
    print("Usage: merge_junit.py <xml1> <xml2> ... <output.xml>")
    sys.exit(1)

output_path = sys.argv[-1]
input_paths = sys.argv[1:-1]

result = JUnitXml()
for path in input_paths:
    xml = JUnitXml.fromfile(path)
    result += xml

result.write(output_path)
print(f"✅ Merged {len(input_paths)} files into {output_path}")
