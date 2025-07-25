
import json
from dataclasses import dataclass

from sphinx.application import Sphinx


@dataclass
class ExternalNeedsSource:
    bazel_module: str
    path_to_target: str
    target: str

def parse_external_needs_sources(v: str) -> list[ExternalNeedsSource]:
    if v in ["[]", ""]:
        return []

    data = json.loads(v)

    def parse_bazel_external_need(s: str) -> ExternalNeedsSource:
        # Example: "@repo//path/to:target" or "@repo//:target"
        if not s.startswith("@") or "//" not in s or ":" not in s:
            raise ValueError(f"Invalid external need string: {s}")
        repo_and_path, target = s.split(":", 1)
        repo, path_to_target = repo_and_path.split("//", 1)
        repo = repo.lstrip("@")
        return ExternalNeedsSource(
            bazel_module=repo,
            path_to_target=path_to_target,
            target=target
        )

    return [parse_bazel_external_need(el) for el in data]

def connect_external_needs(app: Sphinx, config):
    external_needs = parse_external_needs_sources(app.config.external_needs_source)

    raise ValueError(
        f"external_needs: {external_needs}"
    )

    for e in external_needs:
        json_file = f"/{e.bazel_module}/{e.path_to_target}/{e.target}/_build/needs/needs.json"
        app.config.needs_external_needs.append(
            {
                "id_prefix": "TODO_PREFIX_",
                "base_url": "TODO_BASE_URL_",
                "json_url": json_file,
            }
        )
        # Making the prefixes uppercase here to match sphinx_needs, as it does this internally too.
        app.config.allowed_external_prefixes.append("TODO_PREFIX_".upper())
