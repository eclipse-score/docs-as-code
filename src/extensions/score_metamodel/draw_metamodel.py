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

from metamodel_types import ScoreNeedType
from sphinx.config import Config

from .diagram import (
    ClassDiagram,
    PlantUmlRenderer,
    Visibility,
)


class DrawMetamodel:
    def __init__(self, config: Config):
        self._config = config

    def __repr__(self) -> str:
        # avoid sphinx caching a function pointer which is different on every build
        return "draw_metamodel"

    def _get_need_types(self, types: str | list[str]) -> list[ScoreNeedType]:
        if isinstance(types, str):
            types = [types]

        if len(types) == 0:
            raise ValueError(f"No need types found for directives: {types}")

        need_types: list[ScoreNeedType] = []
        for nt in self._config.needs_types:
            if nt["directive"] in types:
                need_types.append(nt)

        return need_types

    def _add_attributes_to_class(
        self,
        diagram: ClassDiagram,
        class_name: str,
        nt: ScoreNeedType,
        attributes: list[str],
    ) -> None:
        for opt, allowed_values in nt.get("mandatory_options", {}).items():
            if opt in attributes:
                diagram.add_member(
                    class_name,
                    opt,
                    type_hint=allowed_values,
                    visibility=Visibility.PUBLIC,
                )

        for opt, allowed_values in nt.get("optional_options", {}).items():
            if opt in attributes:
                diagram.add_member(
                    class_name,
                    opt,
                    type_hint=allowed_values,
                    visibility=Visibility.PRIVATE,
                )

    def _add_links_to_class(
        self,
        diagram: ClassDiagram,
        class_name: str,
        nt: ScoreNeedType,
        links: list[str],
    ) -> None:
        all_links = nt.get("mandatory_links", {}) | nt.get("optional_links", {})

        selected_links = {
            k: v for k, v in all_links.items() if links == "all" or k in links
        }

        for link_name, link_targets in selected_links.items():
            for target in link_targets:
                target_name = target if isinstance(target, str) else target["directive"]

                diagram.relate(class_name, target_name, label=link_name)

    def __call__(
        self,
        types: str | list[str],
        *,
        attributes: list[str] | None = None,
        links: list[str] | None = None,
    ) -> str:
        need_type_objects = self._get_need_types(types)

        diagram = ClassDiagram()
        for nt in need_type_objects:
            class_name = nt["directive"]
            title = nt.get("title")

            diagram.add_class(class_name, stereotype=title)

            if attributes:
                self._add_attributes_to_class(diagram, class_name, nt, attributes)

            if links:
                self._add_links_to_class(diagram, class_name, nt, links)

        return PlantUmlRenderer().render(diagram)
