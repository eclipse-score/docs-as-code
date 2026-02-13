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

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Final

# ============================================================
# Model (renderer-independent)
# ============================================================


class Visibility(str, Enum):
    PUBLIC = "+"
    PRIVATE = "-"
    PROTECTED = "#"
    PACKAGE = "~"


class RelationKind(str, Enum):
    ASSOCIATION = "association"
    UNDIRECTED = "undirected"
    INHERITANCE = "inheritance"
    IMPLEMENTS = "implements"
    DEPENDENCY = "dependency"
    COMPOSITION = "composition"
    AGGREGATION = "aggregation"


@dataclass
class Member:
    name: str
    visibility: Visibility = Visibility.PUBLIC
    type_hint: str | None = None


@dataclass
class ClassNode:
    name: str
    stereotype: str | None = None
    members: list[Member] = field(default_factory=list)


@dataclass
class Relation:
    src: str
    dst: str
    kind: RelationKind = RelationKind.ASSOCIATION
    label: str | None = None


@dataclass
class ClassDiagram:
    """
    Renderer-agnostic AST for class diagrams.

    Intentionally minimal:
    - attributes only (no methods)
    - no multiplicities
    - no packages / namespaces
    - no notes or comments
    """

    classes: dict[str, ClassNode] = field(default_factory=dict)
    relations: list[Relation] = field(default_factory=list)

    # ---- class helpers -------------------------------------------------

    def add_class(self, name: str, *, stereotype: str | None = None) -> ClassNode:
        return self._ensure_class(name, stereotype=stereotype)

    def _ensure_class(self, name: str, *, stereotype: str | None = None) -> ClassNode:
        if not name:
            raise ValueError("class name must not be empty")

        node = self.classes.get(name)
        if node is None:
            node = ClassNode(name=name, stereotype=stereotype)
            self.classes[name] = node
            return node

        if stereotype is not None and node.stereotype is None:
            node.stereotype = stereotype
        return node

    # ---- members -------------------------------------------------------

    def add_member(
        self,
        class_name: str,
        member_name: str,
        *,
        visibility: Visibility = Visibility.PUBLIC,
        type_hint: str | None = None,
    ) -> None:
        if not member_name:
            raise ValueError("member name must not be empty")

        node = self._ensure_class(class_name)
        node.members.append(Member(member_name, visibility, type_hint))

    # ---- relations -----------------------------------------------------

    def relate(
        self,
        src: str,
        dst: str,
        *,
        kind: RelationKind = RelationKind.ASSOCIATION,
        label: str | None = None,
    ) -> None:
        if not src or not dst:
            raise ValueError("relation endpoints must not be empty")

        self._ensure_class(src)
        self._ensure_class(dst)
        self.relations.append(Relation(src=src, dst=dst, kind=kind, label=label))


# ============================================================
# PlantUML renderer
# ============================================================


class PlantUmlRenderer:
    """
    Renders a ClassDiagram into PlantUML.
    """

    _ARROWS: Final[dict[RelationKind, str]] = {
        RelationKind.ASSOCIATION: "-->",
        RelationKind.UNDIRECTED: "--",
        RelationKind.INHERITANCE: "<|--",
        RelationKind.IMPLEMENTS: "<|..",
        RelationKind.DEPENDENCY: "..>",
        RelationKind.COMPOSITION: "*--",
        RelationKind.AGGREGATION: "o--",
    }

    def render(self, diagram: ClassDiagram) -> str:
        """Render a ClassDiagram as PlantUML text."""
        alias = self._AliasMap()

        lines: list[str] = [
            # "@startuml", <- added by needuml!
            # "skinparam linetype ortho",
        ]

        for c in diagram.classes.values():
            cid = alias[c.name]
            display = self._quote(c.name)

            if c.stereotype:
                s = self._escape_stereotype(c.stereotype)
                lines.append(f"class {cid} as {display} <<{s}>> {{")
            else:
                lines.append(f"class {cid} as {display} {{")

            for m in c.members:
                if m.type_hint:
                    lines.append(f"  {m.visibility.value} {m.name} : {m.type_hint}")
                else:
                    lines.append(f"  {m.visibility.value} {m.name}")
            lines.append("}")

        for r in diagram.relations:
            src = alias[r.src]
            dst = alias[r.dst]
            arrow = self._ARROWS[r.kind]

            if r.label:
                lines.append(f"{src} {arrow} {dst} : {self._escape_label(r.label)}")
            else:
                lines.append(f"{src} {arrow} {dst}")

        # lines.append("@enduml") <- added by needuml!
        return "\n".join(lines) + "\n"

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _quote(text: str) -> str:
        """Quote a PlantUML display name."""
        return f'"{text.replace('"', r"\"")}"'

    @staticmethod
    def _escape_label(text: str) -> str:
        """Escape a link label for PlantUML."""
        return text.replace("\n", " ").replace("\r", " ").replace(":", r"\:")

    @staticmethod
    def _escape_stereotype(text: str) -> str:
        """Escape a stereotype for << >> usage."""
        return (
            text.replace("\n", " ")
            .replace("\r", " ")
            .replace("<<", "< <")
            .replace(">>", "> >")
        )

    class _AliasMap:
        """
        Dict-like mapping from class names to readable PlantUML identifiers.

        Accessing a key ensures the alias exists:
            alias["My Class"] -> "My_Class"
        """

        def __init__(self) -> None:
            """Create a new alias map."""
            self._map: dict[str, str] = {}
            self._used: set[str] = set()

        def __getitem__(self, name: str) -> str:
            """Return the alias for a class name, creating it if needed."""
            if name not in self._map:
                self._map[name] = self._create_alias(name)
            return self._map[name]

        # ------------------------
        # internals
        # ------------------------

        def _create_alias(self, name: str) -> str:
            """Create a new readable, collision-free alias."""
            base = self._sanitize(name)
            alias = base
            counter = 2

            while alias in self._used:
                alias = f"{base}_{counter}"
                counter += 1

            self._used.add(alias)
            return alias

        def _sanitize(self, name: str) -> str:
            """Convert an arbitrary name into a readable identifier."""
            VALID_CHARS = re.compile(r"[A-Za-z0-9_]")
            chars = [ch if VALID_CHARS.fullmatch(ch) else "_" for ch in name]
            alias = "".join(chars).strip("_")
            if not alias:
                raise ValueError(f"Cannot create alias for name: {name!r}")
            return alias
