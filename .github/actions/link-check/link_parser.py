import argparse
import re
import sys
from dataclasses import dataclass
from datetime import datetime

PARSING_STATUSES = ["broken"]


@dataclass
class BrokenLink:
    location: str
    line_nr: str
    reasoning: str


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
        if len(status_and_url) < 2:
            continue
        reasoning = status_and_url[1].strip()

        broken_links.append(
            BrokenLink(
                location=location,
                line_nr=line_nr,
                reasoning=reasoning,
            )
        )

    return broken_links


def generate_markdown_table(broken_links: list[BrokenLink]) -> str:
    table = "| Location | Line Number | Reasoning |\n"
    table += "|----------|-------------|-----------|\n"

    for link in broken_links:
        table += f"| {link.location} | {link.line_nr} | {link.reasoning} |\n"

    return table


def generate_issue_body(broken_links: list[BrokenLink]) -> str:
    markdown_table = generate_markdown_table(broken_links)
    return f"""
# Broken Links Report.
**Last updated: {datetime.now().strftime("%d-%m-%Y %H:%M")}**

The following broken links were detected in the documentation:
{markdown_table}
Please investigate and fix these issues to ensure all links are functional.
Thank you!

> To test locally if all link issues are resolved use `bazel run //:docs_link_check`

---
This issue will be auto updated regularly if link issues are found.
You may close it if you wish.
Though a new one will be created if link issues are still present.

"""


def strip_ansi_codes(text: str) -> str:
    """Remove ANSI escape sequences from text"""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


if __name__ == "__main__":
    arg = argparse.ArgumentParser(
        description="Parse broken links from Sphinx log and generate issue body."
    )
    arg.add_argument("logfile", type=str, help="Path to the Sphinx log file.")
    args = arg.parse_args()
    with open(args.logfile) as f:
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
