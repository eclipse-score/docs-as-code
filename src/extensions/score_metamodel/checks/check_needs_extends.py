from __future__ import annotations
from docutils import nodes

from sphinx_needs.config import NeedsSphinxConfig
from sphinx_needs.data import ExtendType, NeedsExtendType, NeedsMutable
from sphinx_needs.exceptions import NeedsInvalidFilter
from sphinx_needs.filter_common import filter_needs_mutable
from sphinx_needs.logging import get_logger, log_warning
from sphinx_needs.need_item import NeedModification
from sphinx_needs.needs_schema import (
    FieldFunctionArray,
    FieldLiteralValue,
    LinksFunctionArray,
    LinksLiteralValue,
)
import sphinx_needs.directives.need 


class Needextend(nodes.General, nodes.Element):
    pass


logger = get_logger(__name__)



def score_extend_needs_data_func(
    all_needs: NeedsMutable,
    extends: dict[str, NeedsExtendType],
    needs_config: NeedsSphinxConfig,
) -> None:
    """Use data gathered from needextend directives to modify fields of existing needs."""

    # Sort by (docname, lineno) to ensure deterministic ordering,
    # regardless of parallel build worker completion order.
    sorted_extends = sorted(extends.values(), key=lambda x: (x["docname"], x["lineno"]))

    current_needextend: NeedsExtendType
    raise RuntimeError("TESING replacement func")
    for current_needextend in sorted_extends:
        need_filter = current_needextend["filter"]
        location = (current_needextend["docname"], current_needextend["lineno"])
        if current_needextend["filter_is_id"]:
            try:
                found_needs = [all_needs[need_filter]]
            except KeyError:
                error = f"Provided id {need_filter!r} for needextend does not exist."
                if current_needextend["strict"]:
                    raise NeedsInvalidFilter(error)
                else:
                    log_warning(logger, error, "needextend", location=location)
                continue
        else:
            try:
                found_needs = filter_needs_mutable(
                    all_needs,
                    needs_config,
                    need_filter,
                    location=location,
                    origin_docname=current_needextend["docname"],
                )
            except Exception as e:
                log_warning(
                    logger,
                    f"Invalid filter {need_filter!r}: {e}",
                    "needextend",
                    location=location,
                )
                continue
        for found_need in found_needs:
            # Work in the stored needs, not on the search result
            need = all_needs[found_need["id"]]
            need.add_modification(
                NeedModification(
                    docname=current_needextend["docname"],
                    lineno=current_needextend["lineno"],
                )
            )

            location = (
                current_needextend["docname"],
                current_needextend["lineno"],
            )


            for option_name, etype, link_value in current_needextend[
                "list_modifications"
            ]:
                # append link = ok?!
                # replace / remove link = nope
                # set option = ok
                # replace / remove option = nope
                match (etype, link_value):
                    case (ExtendType.APPEND, LinksLiteralValue()):
                        if (df := need._dynamic_fields.get(option_name)) is not None:
                            need._dynamic_fields[option_name] = LinksFunctionArray(
                                (*df.value, *link_value.value)
                            )
                            need[option_name] = []
                        else:
                            existing = need.get_links(option_name, as_str=False)
                            need[option_name] = [
                                *existing,
                                *(  # keep unique
                                    v for v in link_value.value if v not in existing
                                ),
                            ]
                    case (ExtendType.APPEND, LinksFunctionArray()):
                        if (df := need._dynamic_fields.get(option_name)) is not None:
                            need._dynamic_fields[option_name] = LinksFunctionArray(
                                (  # keep unique
                                    *df.value,
                                    *(v for v in link_value.value if v not in df.value),
                                )
                            )
                            need[option_name] = []
                        else:
                            existing = need.get_links(option_name, as_str=False)
                            need._dynamic_fields[option_name] = LinksFunctionArray(
                                (
                                    *existing,
                                    *(  # keep unique
                                        v for v in link_value.value if v not in existing
                                    ),
                                )
                            )
                            need[option_name] = []
                    case (ExtendType.REPLACE | ExtendType.DELETE, LinksLiteralValue()):
                        error_msg = (
                            "Replace or Delete action is not allowed via needextends."
                        )
                        log_warning(logger, error_msg, "needextend", location=location)
                        raise RuntimeError(f"{location}: {error_msg}")
                    case (ExtendType.REPLACE | ExtendType.DELETE, LinksFunctionArray()):
                        error_msg = (
                            "Replace or Delete action is not allowed via needextends."
                        )
                        log_warning(logger, error_msg, "needextend", location=location)
                        raise RuntimeError(f"{location}: {error_msg}")
                    case other_link:
                        raise RuntimeError(
                            f"Unhandled case {other_link} for {option_name!r}"
                        )

            for option_name, etype, field_value in current_needextend["modifications"]:
                match (etype, field_value):
                    case (ExtendType.APPEND, FieldLiteralValue()):
                        if (df := need._dynamic_fields.get(option_name)) is not None:
                            need._dynamic_fields[option_name] = (
                                FieldFunctionArray((*df.value, *field_value.value))
                                if isinstance(field_value.value, list)
                                else FieldFunctionArray((*df.value, field_value.value))
                            )
                        else:
                            if isinstance(field_value.value, list):
                                need[option_name] = [
                                    *need[option_name],
                                    *field_value.value,
                                ]
                            elif isinstance(field_value.value, str):
                                need[option_name] = (
                                    need[option_name] + " " + field_value.value
                                    if need[option_name]
                                    else field_value.value
                                )
                            else:
                                raise RuntimeError(
                                    f"Cannot append non-string/array value {field_value.value!r} to field '{option_name}'"
                                )
                    case (ExtendType.APPEND, FieldFunctionArray()):
                        if (df := need._dynamic_fields.get(option_name)) is not None:
                            need._dynamic_fields[option_name] = FieldFunctionArray(
                                (*df.value, *field_value.value)
                            )
                        else:
                            if isinstance(need[option_name], list):
                                need._dynamic_fields[option_name] = FieldFunctionArray(
                                    (*need[option_name], *field_value.value)
                                )
                            elif isinstance(need[option_name], str):
                                need._dynamic_fields[option_name] = FieldFunctionArray(
                                    (
                                        need[option_name],
                                        *field_value.value,
                                    )
                                )
                            else:
                                raise RuntimeError(
                                    f"Cannot append non-string/array value {field_value.value!r} to field '{option_name}'"
                                )
                    case (ExtendType.REPLACE | ExtendType.DELETE, None):
                        error_msg = (
                            "Replace or Delete action is not allowed via needextends."
                        )
                        log_warning(logger, error_msg, "needextend", location=location)
                        raise RuntimeError(f"{location}: {error_msg}")
                    case (ExtendType.REPLACE | ExtendType.DELETE, FieldLiteralValue()):
                        error_msg = (
                            "Replace or Delete action is not allowed via needextends."
                        )
                        log_warning(logger, error_msg, "needextend", location=location)
                        raise RuntimeError(f"{location}: {error_msg}")
                    case (ExtendType.REPLACE | ExtendType.DELETE, FieldFunctionArray()):
                        error_msg = (
                            "Replace or Delete action is not allowed via needextends."
                        )
                        log_warning(logger, error_msg, "needextend", location=location)
                        raise RuntimeError(f"{location}: {error_msg}")
                        # TODO reset need[option_name] to something sensible?
                    case other_field:
                        raise RuntimeError(
                            f"Unhandled case {other_field} for {option_name!r}"
                        )


sphinx_needs.directives.need.extends_needs_data = score_extend_needs_data_func

print("=====================================")
print("WE HAVE REPLACED THE EXTENDS FUNC")
print("=====================================")
