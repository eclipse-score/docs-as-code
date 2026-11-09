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

"""Platform-selected native PlantUML executable target using select()."""

def plantuml_binary(name, visibility = None):
    """Declare a public PlantUML alias for the current execution platform."""
    native.alias(
        name = name,
        actual = select({
            "//src:plantuml_linux_x86_64": "@plantuml_native_linux_amd64//:plantuml",
            "//src:plantuml_linux_arm64": "@plantuml_native_linux_arm64//:plantuml",
            "//src:plantuml_macos_arm64": "@plantuml_native_macos_arm64//:plantuml",
            "//src:plantuml_windows_x86_64": "@plantuml_native_windows_amd64//:plantuml.exe",
        }),
        visibility = visibility,
    )
