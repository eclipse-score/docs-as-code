import html
import re
import json

from itertools import chain
from sphinx_needs import logging
from typing import Any
from dataclasses import dataclass, asdict
from pathlib import Path


LOGGER = logging.get_logger(__name__)

@dataclass(frozen=True)
class TestLink:
    file: Path
    line: int
    need: str
    verify_type: str
    result: str
    result_text: str = ""

class TestLinkJSONEncoder(json.JSONEncoder):
    def default(self, o: object):
        if isinstance(o, TestLink):
            return asdict(o)
        if isinstance(o, Path):
            return str(o)
        return super().default(o)


def TestLinkJSONDecoder(d: dict[str, Any]) -> TestLink | dict[str, Any]:
    if {"file", "line", "need", "verify_type", "result", "result_text",} <= d.keys():
        return TestLink(
            file=Path(d["file"]),
            line=d["line"],
            need=d["need"],
            verify_type=d["verify_type"],
            result=d["result"],
            result_text=d["result_text"]
        )
    else:
        # It's something else, pass it on to other decoders
        return d


# We will have everythin as string here as that mirrors the xml file
@dataclass
class TestCaseNeed:
    id: str
    file: str
    lineNr: str
    result: str # passed | falied | skipped | disabled
    TestType: str
    DerivationTechnique: str
    result_text: str = "" # Can be None on anything but failed
    # Either or HAVE to be filled.
    PartiallyVerifies: str | None = None
    FullyVerifies: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]): # type-ignore
        return cls(**data) # type-ignore

    @classmethod
    def clean_text(cls, text: str):
        # This might not be the right thing in all circumstances
        ansi_regex  = re.compile(r"\x1b\[[0-9;]*m")
        ansi_clean = ansi_regex.sub("", text)
        decoded = html.unescape(ansi_clean)
        return str(decoded.replace("\n", " ")).strip()


    def __post_init__(self):
        # Cleaning text
        if self.result_text:
            self.result_text = self.clean_text(self.result_text)
        # Self assertion to double check some mandatory options
        # For now this is disabled

        # It's mandatory that the test either partially or fully verifies a requirement
        # if self.PartiallyVerifies is None and self.FullyVerifies is None:
        #     raise ValueError(
        #         f"TestCase: {self.id} Error. Either 'PartiallyVerifies' or 'FullyVerifies' must be provided."
        #     )
        # Skipped tests should always have a reason associated with them
        # if "skipped" in self.result.keys() and not list(self.result.values())[0]:
        #     raise ValueError(
        #         f"TestCase: {self.id} Error. Test was skipped without provided reason, reason is mandatory for skipped tests."
        #     )

    def to_dict(self) -> list[TestLink]:
        """Convert TestCaseNeed to list of TestLink objects.""" 
        def process_verification(self, verify_field: str | None, verify_type: str):
            """Process a verification field and yield TestLink objects."""
            if not verify_field:
                return
                
            LOGGER.debug(f"{verify_type.upper()} VERIFIES: {verify_field}", 
                        type="score_source_code_linker")
            
            for need in verify_field.split(","):
                yield TestLink(
                    file=Path(self.file),
                    line=int(self.lineNr),
                    need=need.strip(),
                    verify_type=verify_type,
                    result=self.result,
                    result_text=self.result_text
                )
        
        return list(chain(
            process_verification(self, self.PartiallyVerifies, "partially"),
            process_verification(self, self.FullyVerifies, "fully")
        ))


def store_test_xml_parsed_json(file: Path, testlist: list[TestLink]):
    # After `rm -rf _build` or on clean builds the directory does not exist, so we need to create it
    file.parent.mkdir(exist_ok=True)
    with open(file, "w") as f:
        json.dump(
            testlist,
            f,
            cls=TestLinkJSONEncoder, 
            indent=2,
            ensure_ascii=False,
        )


def load_test_xml_parsed_json(file: Path) -> list[TestLink]:
    links: list[TestLink] = json.loads(
        file.read_text(encoding="utf-8"),
        object_hook=TestLinkJSONDecoder,
    )
    assert isinstance(links, list), (
        "The source xml parser links should be a list of TestLink objects."
    )
    assert all(isinstance(link, TestLink) for link in links), (
        "All items in source_xml_parser should be TestLink objects."
    )
    return links
