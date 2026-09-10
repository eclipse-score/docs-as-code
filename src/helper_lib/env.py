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

import json
import logging
import os
from collections.abc import Mapping
from pathlib import Path
from typing import cast

logger = logging.getLogger(__name__)


class Environment:
    """Typed access to the process environment used by the CLI config loader."""

    def __init__(self, values: Mapping[str, str] | None = None) -> None:
        self._values = os.environ if values is None else values

    def get(self, name: str, default: str | None = None) -> str:
        """Read a value, raising when it is missing and no default is supplied."""
        value = self._values.get(name)
        logger.debug("Env: %s = %s", name, value)
        if value is not None:
            # Preserve an explicitly configured value, including an empty string.
            return value.strip()
        elif default is not None:
            # A caller-provided default makes this environment variable optional.
            return default
        else:
            # A missing value without a default is required configuration.
            raise ValueError(f"Environment variable {name} is not set")

    def optional_path(self, name: str) -> Path | None:
        """
        Read an optional path from the environment.

        Note: this will not verify or modify the exact environment variable's value beyond converting it to a Path.
        """
        value = self.get(name, "")
        return Path(value) if value else None

    def required_path(self, name: str) -> Path:
        """
        Read a required path from the environment.

        Note: this will not verify or modify the exact environment variable's value beyond converting it to a Path.
        """
        value = self.get(name, "")
        if not value:
            raise ValueError(f"Environment variable {name} is not set")
        return Path(value)

    def json(self, name: str, default: str | None = None) -> object:
        """Read and decode a JSON value from the environment."""
        return json.loads(self.get(name, default))

    def string_list(self, name: str, default: str | None = None) -> list[str]:
        """Read a JSON list and validate that every item is a string."""
        raw_value = self.get(name, default)
        # DATA was historically allowed to be present but empty. Treat that as
        # an empty list while still requiring the environment variable itself.
        if not raw_value:
            return []
        value = json.loads(raw_value)
        if not isinstance(value, list) or not all(
            isinstance(item, str) for item in cast(list[object], value)
        ):
            raise ValueError(
                f"Environment variable {name} must contain a list of strings"
            )
        return cast(list[str], value)
