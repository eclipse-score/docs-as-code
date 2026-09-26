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
def join_path(prefix, rest):
    """
    Compose two docname segments with `/`. No trailing `/` is preserved.

    When a segment is ``None``, it contributes no path text; the remaining
    segment is normalized in the same way.

    Args:
      prefix: Leading docname segment, possibly empty or ``None``.
      rest: Trailing docname segment, possibly empty or ``None``.

    Returns:
      The combined docname.
    """
    rest = (rest or "").rstrip("/")
    prefix = (prefix or "").rstrip("/")

    if not prefix or prefix == ".":
        return rest
    if not rest or rest == ".":
        return prefix

    return prefix + "/" + rest

def dirname(path):
    idx = path.rfind("/")
    return "" if idx < 0 else path[:idx]

def glob_doc_sources(prefix):
    """Return glob patterns for documentation sources below ``prefix``."""
    extensions = [
        "png", "svg", "md", "rst", "html", "css",
        "puml", "need", "yaml", "json", "csv", "inc",
    ]
    param = [join_path(prefix, "**/*." + ext) for ext in extensions]
    srcs = native.glob(param, allow_empty = True)
    return srcs
