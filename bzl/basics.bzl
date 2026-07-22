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
    """Compose two docname segments with `/`.

    Args:
      prefix: Leading docname segment, possibly empty.
      rest: Trailing docname segment, possibly empty.

    Returns:
      The combined docname.
    """
    if not prefix or prefix == ".":
        return rest
    if not rest:
        return prefix
    return prefix + "/" + rest

def dirname(path):
    """
    Return the leading docname segment of a docname,
    e.g. the directory portion of a filepath.
    """

    idx = path.rfind("/")
    return "" if idx < 0 else path[:idx]

def doc_source_globs(source_dir):
    """Return glob for documentation sources below ``source_dir``."""

    extensions = [
        "png", "svg", "md", "rst", "html", "css",
        "puml", "need", "yaml", "json", "csv", "inc",
    ]
    return native.glob(
        [join_path(source_dir, "**/*." + ext) for ext in extensions],
        allow_empty = True
    )
