# *******************************************************************************
# Copyright (c) 2025 Contributors to the Eclipse Foundation
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

from diagram import (
    ClassDiagram,
    PlantUmlRenderer,
    RelationKind,
    Visibility,
)


def test_simple_class_diagram_snapshot():
    d = ClassDiagram()
    d.add_class("A")
    d.add_member("A", "id")
    d.relate("A", "B", label="uses")

    result = PlantUmlRenderer().render(d)

    assert (
        result
        == """\
class A as "A" {
  + id
}
class B as "B" {
}
A --> B : uses
"""
    )


def test_stereotype_and_private_member():
    d = ClassDiagram()
    d.add_class("User", stereotype="Entity")
    d.add_member("User", "password", visibility=Visibility.PRIVATE)

    result = PlantUmlRenderer().render(d)

    print(repr(result))

    assert (
        result
        == """\
class User as "User" <<Entity>> {
  - password
}
"""
    )


def test_inheritance_relation():
    d = ClassDiagram()
    d.relate("Base", "Derived", kind=RelationKind.INHERITANCE)

    result = PlantUmlRenderer().render(d)

    print(repr(result))

    assert (
        result
        == """\
class Base as "Base" {
}
class Derived as "Derived" {
}
Base <|-- Derived
"""
    )
