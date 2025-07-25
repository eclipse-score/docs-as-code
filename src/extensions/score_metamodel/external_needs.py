
import json
import os
from dataclasses import dataclass
from pathlib import Path

from sphinx.application import Sphinx
from sphinx_needs.needsfile import NeedsList


@dataclass
class ExternalNeedsSource:
    bazel_module: str
    path_to_target: str
    target: str

def parse_external_needs_sources(v: str) -> list[ExternalNeedsSource]:
    if v in ["[]", ""]:
        return []

    # v:         ["@score_docs_as_code//src:docs_assets"]
    # reptr(v): '["@score_docs_as_code//src:docs_assets"]'

    print(f"exception: {type(v)} {repr(v)}")
    data = json.loads(v)

    def parse_bazel_external_need(s: str) -> ExternalNeedsSource | None:
        # Example: "@repo//path/to:target" or "@repo//:target"
        if not s.startswith("@") or "//" not in s or ":" not in s:
            raise ValueError(f"Invalid external need string: {s}")
        repo_and_path, target = s.split(":", 1)
        repo, path_to_target = repo_and_path.split("//", 1)
        repo = repo.lstrip("@")

        if target == "needs_json":
            return ExternalNeedsSource(
                bazel_module=repo,
                path_to_target=path_to_target,
                target=target
            )
        else:
            return None

    return [res for el in data if (res := parse_bazel_external_need(el))]

def connect_external_needs(app: Sphinx, config):
    app.add_config_value('project_url', "", rebuild="env")
    app.add_config_value('project_prefix', "", rebuild="env")
    # Patch json exporter to include our custom fields
    # Note: yeah, NeedsList is the json exporter!
    orig_function = NeedsList._finalise
    def temp(self: NeedsList):
        self.needs_list["project_url"] = app.config.project_url
        self.needs_list["project_prefix"] = app.config.project_prefix
        orig_function(self)
    NeedsList._finalise = temp

    external_needs = parse_external_needs_sources(app.config.external_needs_source)

    for e in external_needs:
        # orig: "/score_process~/process/docs_needs_latest/_build/needs/needs.json"
        # /score_process~/needs_json/_build/needs/needs.json
        assert not e.path_to_target # needs_json is always at the root of the module
        json_file = f"/{e.bazel_module}~/{e.target}/_build/needs/needs.json"
        if r := os.getenv("RUNFILES_DIR"):
            json_file = r + json_file

        needs_json_data = json.loads(Path(json_file).read_text(encoding="utf-8"))

        app.config.needs_external_needs.append(
            {
                "id_prefix": needs_json_data["project_prefix"],
                "base_url": needs_json_data["project_url"] + "/main",
                "json_path": json_file,
            }
        )
        # Making the prefixes uppercase here to match sphinx_needs, as it does this internally too.
        app.config.allowed_external_prefixes.append(needs_json_data["project_prefix"].upper())
