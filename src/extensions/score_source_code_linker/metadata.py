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

from typing import TypedDict, TypeGuard

class MetaData(TypedDict):
    module_name: str
    hash: str
    url: str

def is_metadata(x: object) -> TypeGuard[MetaData]:
    # Make this as strict/loose as you want; at minimum, it must be a dict.
    return isinstance(x, dict) and {"module_name", "hash", "url"} <= x.keys()
