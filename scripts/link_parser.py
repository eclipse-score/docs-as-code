"""
EXAMPLE LOG INPUT:

(how-to/write_docs: line    7) ok        https://docutils.sourceforge.io/rst.html
(internals/extensions/extension_guide: line  136) ok        https://docs.pytest.org/en/stable/
(internals/extensions/source_code_linker: line  221) broken    https://eclipse-score.github.io/docs-as-code/main/requirements/requirements.html#tool_req__docs_common_attr_id_scheme - 404 Client Error: Not Found for url: https://eclipse-score.github.io/docs-as-code/main/requirements/requirements.html
(internals/extensions/source_code_linker: line  224) broken    https://eclipse-score.github.io/docs-as-code/main/requirements/requirements.html#tool_req__docs_dd_link_source_code_link - 404 Client Error: Not Found for url: https://eclipse-score.github.io/docs-as-code/main/requirements/requirements.html
(internals/extensions/source_code_linker: line  221) broken    https://eclipse-score.github.io/docs-as-code/main/requirements/requirements.html#tool_req__docs_common_attr_status - 404 Client Error: Not Found for url: https://eclipse-score.github.io/docs-as-code/main/requirements/requirements.html
(concepts/bidirectional_traceability: line   29) ok        https://eclipse-score.github.io
(internals/extensions/extension_guide: line  128) ok        https://github.com/eclipse-score/docs-as-code/tree/main/src/extensions/score_draw_uml_funcs
(internals/extensions/extension_guide: line  127) ok        https://github.com/eclipse-score/docs-as-code/tree/main/src/extensions/score_metamodel
(internals/extensions/extension_guide: line  122) ok        https://github.com/eclipse-score/docs-as-code/tree/main/src/extensions/score_source_code_linker/
(internals/benchmark_results: line   18) ok        https://github.com/eclipse-score/process_description
(internals/extensions/extension_guide: line  124) ok        https://github.com/eclipse-score/tooling/blob/main/python_basics/score_pytest/README.md
(internals/extensions/sync_toml: line    6) ok        https://needs-config-writer.useblocks.com/
(internals/extensions/source_code_linker: line   67) ok        https://github.com/eclipse-score/tooling/tree/main/python_basics/score_pytest
(concepts/bidirectional_traceability: line   47) ok        https://sphinx-collections.readthedocs.io/en/latest/
(how-to/other_modules: line   63) ok        https://sphinx-needs.readthedocs.io/en/latest/
(internals/extensions/extension_guide: line   47) broken    https://github.com/useblocks/sphinx-needs/blob/master/docs/contributing.rst#structure-of-the-extensions-logic - Anchor 'structure-of-the-extensions-logic' not found
(internals/requirements/capabilities: line    5) redirect  https://sphinx-needs.readthedocs.io/ - with Found to https://sphinx-needs.readthedocs.io/en/stable/
(      how-to/faq: line   37) ok        https://ubcode.useblocks.com
(internals/extensions/sync_toml: line    9) ok        https://ubcode.useblocks.com/ubc/introduction.html
(how-to/write_docs: line    4) ok        https://www.sphinx-doc.org/en/master/
(internals/requirements/capabilities: line    5) redirect  https://www.sphinx-doc.org/ - with Found to https://www.sphinx-doc.org/en/master/
(internals/extensions/extension_guide: line  135) ok        https://www.sphinx-doc.org/en/master/development/tutorials/index.html
(internals/extensions/extension_guide: line  133) ok        https://www.sphinx-doc.org/en/master/extdev/testing.html#module-sphinx.testing
(internals/extensions/extension_guide: line  132) redirect  https://www.sphinx-doc.org/en - with Found to https://www.sphinx-doc.org/en/master/
(internals/extensions/extension_guide: line   65) ok        https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.add_config_value
(internals/extensions/extension_guide: line   46) ok        https://www.sphinx-doc.org/en/master/extdev/event_callbacks.html#core-events-overview
(internals/extensions/extension_guide: line   45) ok        https://www.sphinx-doc.org/en/master/extdev/appapi.html#sphinx.application.Sphinx.connect
"""

import argparse
import sys
import re
from dataclasses import dataclass

PARSING_STATUSES = ["broken"]


@dataclass
class BrokenLink:
    location: str
    line_nr: str
    url: str
    status: str
    reasoning: str


# Make me a function that parses the above string and returns a list with all links that are broken or don't work and where they are in the documentation.
# The string above is just an example. The actuall string will need to parse std out from a sphinx execution, or read a txt file that contains this format.
def parse_broken_links(log: str) -> list[BrokenLink]:
    broken_links: list[BrokenLink] = []
    lines = log.strip().split("\n")

    for line in lines:
        parts = line.split(") ")
        if len(parts) < 2:
            continue

        location_part = parts[0].replace("(", "").strip()
        location = location_part.split(":")[0].strip()
        line_nr = location_part.split("line")[-1].strip()
        status_and_url_part = parts[1]

        if not any(status in status_and_url_part for status in PARSING_STATUSES):
            continue
        status_and_url = status_and_url_part.split(" - ")
        # status = list(filter(None,status_and_url.split(' ')))
        if len(status_and_url) < 2:
            continue
        status, url = status_and_url[0].strip().split()
        reasoning = status_and_url[1].strip()

        broken_links.append(
            BrokenLink(
                location=location,
                line_nr=line_nr,
                url=url,
                status=status,
                reasoning=reasoning,
            )
        )

    return broken_links


# make me a function that takes the dictionary of parse_broken_links and puts them into a nice markdown table.
def generate_markdown_table(broken_links: list[BrokenLink]) -> str:
    table = "| Location | Line Number | URL | Status | Reasoning |\n"
    table += "|----------|-------------|-----|--------|-----------|\n"

    for link in broken_links:
        table += f"| {link.location} | {link.line_nr} | {link.url} | {link.status} | {link.reasoning} |\n"

    return table


def generate_issue_body(broken_links: list[BrokenLink]) -> str:
    markdown_table = generate_markdown_table(broken_links)
    issue_body = f"""
# Broken Links Report
The following broken links were detected in the documentation:
{markdown_table}
Please investigate and fix these issues to ensure all links are functional.
Thank you!
"""
    return issue_body


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from text"""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


if __name__ == "__main__":
    argparse = argparse.ArgumentParser(
        description="Parse broken links from Sphinx log and generate issue body."
    )
    argparse.add_argument("logfile", type=str, help="Path to the Sphinx log file.")
    args = argparse.parse_args()
    with open(args.logfile, "r") as f:
        log_content_raw = f.read()
    log_content = strip_ansi_codes(log_content_raw)
    broken_links = parse_broken_links(log_content)
    if not broken_links:
        # Nothing broken found, can exit early
        sys.exit(0)
    issue_body = generate_issue_body(broken_links)
    if broken_links:
        with open("issue_body.md", "w") as out:
            out.write(issue_body)
