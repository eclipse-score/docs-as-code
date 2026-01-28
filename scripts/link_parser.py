import argparse
import re
import sys
from dataclasses import dataclass

PARSING_STATUSES = ["broken"]


@dataclass
class BrokenLink:
    location: str
    line_nr: str
    url: str
    status: str
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


def generate_markdown_table(broken_links: list[BrokenLink]) -> str:
    table = "| Location | Line Number | URL | Status | Reasoning |\n"
    table += "|----------|-------------|-----|--------|-----------|\n"

    for link in broken_links:
        table += (
            f"| {link.location} | {link.line_nr} | "
            f"{link.url} | {link.status} | {link.reasoning} |\n"
        )

    return table


def generate_issue_body(broken_links: list[BrokenLink]) -> str:
    markdown_table = generate_markdown_table(broken_links)
    return f"""
# Broken Links Report
The following broken links were detected in the documentation:
{markdown_table}
Please investigate and fix these issues to ensure all links are functional.
Thank you!
"""


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
