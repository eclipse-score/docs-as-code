import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class NeedLink:
    """Represents a single template string finding in a file."""

    file: Path
    line: int
    tag: str
    need: str
    full_line: str


# Ensuring our found json does not get parsed in future iterations
def encode_comment(s: str) -> str:
    return s.replace(" ", "-----", 1)


def decode_comment(s: str) -> str:
    return s.replace("-----", " ", 1)


class NeedLinkEncoder(json.JSONEncoder):
    def default(self, o: object):
        if isinstance(o, NeedLink):
            d = asdict(o)
            d["tag"] = encode_comment(d.get("tag", ""))
            d["full_line"] = encode_comment(d.get("full_line", ""))
            return d
        if isinstance(o, Path):
            return str(o)
        return super().default(o)


def needlink_decoder(d: dict[str, Any]) -> NeedLink | dict[str, Any]:
    if {"file", "line", "tag", "need", "full_line"} <= d.keys():
        return NeedLink(
            file=Path(d["file"]),
            line=d["line"],
            tag=decode_comment(d["tag"]),
            need=d["need"],
            full_line=decode_comment(d["full_line"]),
        )
    else:
        # It's something else, pass it on to other decoders
        return d


def store_source_code_links_json(file: Path, needlist: list[NeedLink]):
    # After `rm -rf _build` or on clean builds the directory does not exist, so we need to create it
    file.parent.mkdir(exist_ok=True)
    with open(file, "w") as f:
        json.dump(
            needlist,
            f,
            cls=NeedLinkEncoder,  # use your custom encoder
            indent=2,
            ensure_ascii=False,
        )


def load_source_code_links_json(file: Path) -> list[NeedLink]:
    links: list[NeedLink] = json.loads(
        file.read_text(encoding="utf-8"),
        object_hook=needlink_decoder,
    )
    assert isinstance(links, list), (
        "The source code links should be a list of NeedLink objects."
    )
    assert all(isinstance(link, NeedLink) for link in links), (
        "All items in source_code_links should be NeedLink objects."
    )
    return links
