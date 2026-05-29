# *******************************************************************************
# Copyright (c) 2026 Contributors to the Eclipse Foundation
#
# See the NOTICE file(s) distributed with this work for additional
# information regarding copyright ownership.
#
# This program and the accompanying materials are made available under the
# terms of the Apache License Version 2.0 which is available at
# https://www.apache.org/licenses/LICENSE-2.0
#
# SPDX-License-Identifier: Apache-2.0
# *******************************************************************************
from __future__ import annotations

import sphinx_needs.directives.need
from sphinx_needs.config import NeedsSphinxConfig
from sphinx_needs.data import ExtendType, NeedsExtendType, NeedsMutable
from sphinx_needs.directives.needextend import extend_needs_data as original_function
from sphinx_needs.exceptions import NeedsInvalidFilter
from sphinx_needs.filter_common import filter_needs_mutable
from sphinx_needs.logging import get_logger, log_warning
from sphinx_needs.needs_schema import (
    FieldFunctionArray,
    FieldLiteralValue,
    LinksFunctionArray,
    LinksLiteralValue,
)

logger = get_logger(__name__)


def score_extend_needs_data_func(  # noqa: C901
    all_needs: NeedsMutable,
    extends: dict[str, NeedsExtendType],
    needs_config: NeedsSphinxConfig,
):
    """Use data gathered from needextend directives to modify fields of existing needs."""
    # regardless of parallel build worker completion order.
    sorted_extends = sorted(extends.values(), key=lambda x: (x["docname"], x["lineno"]))

    current_needextend: NeedsExtendType
    for current_needextend in sorted_extends:
        need_filter = current_needextend["filter"]
        location = (current_needextend["docname"], current_needextend["lineno"])

        # ╓                                                          ╖
        # ║ This is currently as a grace period still allowed, but   ║
        # ║ will be forbiden in future releases                      ║
        # ╙                                                          ╜
        # if "c.this_doc()" not in need_filter:
        # error_msg = "Potentially altering needs outside of the document is not allowed. Please add 'c.this_doc()' to the needextend to limit it to only needs in the same document"
        # log_warning(logger, error_msg, "needextend", location=location)

        if current_needextend["filter_is_id"]:
            try:
                found_needs = [all_needs[need_filter]]
            except KeyError:
                error = f"Provided id {need_filter!r} for needextend does not exist."
                if current_needextend["strict"]:
                    raise NeedsInvalidFilter(error) from KeyError
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
            if found_need["is_external"]:
                log_warning(
                    logger,
                    f"Error when extending need: {found_need['id']}. "
                    + "It is not allowed to modify external needs via needextend",
                    "needextend",
                    location,
                )
            # Work in the stored needs, not on the search result
            need = all_needs[found_need["id"]]

            location = (
                current_needextend["docname"],
                current_needextend["lineno"],
            )

            for _, etype, link_value in current_needextend["list_modifications"]:
                match (etype, link_value):
                    case (
                        ExtendType.REPLACE | ExtendType.DELETE,
                        LinksLiteralValue() | LinksFunctionArray(),
                    ):
                        # Replacing / Deleting links is not allowed
                        error_msg = (
                            f"Error when extending need: {need['id']}. "
                            "Replace or Delete action is not allowed via needextends."
                        )
                        # logger.warning_for_need(current_needextend["id"], error_msg)
                        log_warning(logger, error_msg, "needextend", location=location)

            for option_name, etype, field_value in current_needextend["modifications"]:
                if etype == ExtendType.DELETE:
                    error_msg = (
                        f"Error when extending need: {need['id']}. "
                        "Delete action is not allowed via needextends."
                    )
                    log_warning(logger, error_msg, "needextend", location=location)
                match (etype, field_value):
                    case (ExtendType.APPEND, FieldLiteralValue()):
                        if isinstance(field_value.value, str):
                            error_msg = (
                                f"Error when extending need: {need['id']}. "
                                "Append action is not allowed via needextends on 'string type options'."
                            )
                            log_warning(
                                logger, error_msg, "needextend", location=location
                            )

                    case (
                        ExtendType.REPLACE,
                        None | FieldLiteralValue() | FieldFunctionArray(),
                    ):
                        if need[option_name]:
                            error_msg = f"Error when extending need: {need['id']}. Replacing of options that are already set is not allowed via needextends."

                            log_warning(
                                logger, error_msg, "needextend", location=location
                            )
    return original_function(all_needs, extends, needs_config)


sphinx_needs.directives.need.extend_needs_data = score_extend_needs_data_func
