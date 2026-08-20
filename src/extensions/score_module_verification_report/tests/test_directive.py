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
"""Unit tests for the configuration-resolution logic in
:mod:`score_module_verification_report.directive`.

The directive requires a full Sphinx environment to instantiate, so we test
the pure derivation rules in isolation via small helper invocations that
replicate the logic from ``run()`` without standing up Sphinx.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Helpers that mirror the derivation logic in directive.py so we can test
# it without a Sphinx environment.
# ---------------------------------------------------------------------------


def _resolve(
    *,
    option_module_id: str = "",
    option_feature_id: str = "",
    option_component_prefix: str = "",
    config: dict | None = None,
) -> dict:
    """Run the same config-resolution logic as ``run()`` and return a
    dict with the resolved fields."""
    if config is None:
        config = {}
    module_id = option_module_id or config.get("module_id", "")
    module_short = (
        module_id[len("mod__"):]
        if module_id.startswith("mod__")
        else module_id
    )
    component_prefix = (
        option_component_prefix
        or config.get("component_prefix")
        or ("comp__" + module_short + "_" if module_short else "comp__")
    )
    feature_id = (
        option_feature_id
        or config.get("feature_id")
        or f"feat__{module_short}"
    )
    feature_slug = (
        feature_id.split("__", 1)[1] if "__" in feature_id else feature_id
    )
    return {
        "module_id": module_id,
        "module_short": module_short,
        "component_prefix": component_prefix,
        "feature_id": feature_id,
        "feature_slug": feature_slug,
    }


# ---------------------------------------------------------------------------
# Tests — option-only (no config file)
# ---------------------------------------------------------------------------


def test_module_id_option_derives_prefix_and_feature():
    r = _resolve(option_module_id="mod__baselibs")
    assert r["module_id"] == "mod__baselibs"
    assert r["module_short"] == "baselibs"
    assert r["component_prefix"] == "comp__baselibs_"
    assert r["feature_id"] == "feat__baselibs"
    assert r["feature_slug"] == "baselibs"


def test_explicit_feature_id_option_overrides_derived():
    r = _resolve(option_module_id="mod__baselibs", option_feature_id="feat__bl")
    assert r["feature_id"] == "feat__bl"
    assert r["feature_slug"] == "bl"


def test_explicit_component_prefix_option_overrides_derived():
    r = _resolve(option_module_id="mod__baselibs", option_component_prefix="comp__bl_")
    assert r["component_prefix"] == "comp__bl_"


def test_module_id_without_mod_prefix():
    r = _resolve(option_module_id="mymodule")
    assert r["module_short"] == "mymodule"
    assert r["component_prefix"] == "comp__mymodule_"
    assert r["feature_id"] == "feat__mymodule"


def test_empty_module_id_gives_generic_prefix():
    r = _resolve()
    assert r["module_id"] == ""
    assert r["component_prefix"] == "comp__"
    assert r["feature_id"] == "feat__"


# ---------------------------------------------------------------------------
# Tests — option takes precedence over config
# ---------------------------------------------------------------------------


def test_option_module_id_beats_config():
    r = _resolve(
        option_module_id="mod__fromopt",
        config={"module_id": "mod__fromconfig"},
    )
    assert r["module_id"] == "mod__fromopt"


def test_option_feature_id_beats_config():
    r = _resolve(
        option_module_id="mod__baselibs",
        option_feature_id="feat__opt",
        config={"feature_id": "feat__cfg"},
    )
    assert r["feature_id"] == "feat__opt"


def test_option_component_prefix_beats_config():
    r = _resolve(
        option_module_id="mod__baselibs",
        option_component_prefix="comp__opt_",
        config={"component_prefix": "comp__cfg_"},
    )
    assert r["component_prefix"] == "comp__opt_"


def test_config_used_when_no_option_given():
    r = _resolve(
        config={
            "module_id": "mod__cfg",
            "feature_id": "feat__cfg",
            "component_prefix": "comp__cfg_",
        }
    )
    assert r["module_id"] == "mod__cfg"
    assert r["feature_id"] == "feat__cfg"
    assert r["component_prefix"] == "comp__cfg_"


def test_config_feature_id_used_when_no_option():
    r = _resolve(
        option_module_id="mod__baselibs",
        config={"feature_id": "feat__custom"},
    )
    assert r["feature_id"] == "feat__custom"


# ---------------------------------------------------------------------------
# Tests — feature_slug extraction
# ---------------------------------------------------------------------------


def test_feature_slug_splits_on_double_underscore():
    r = _resolve(option_feature_id="feat__my_module")
    assert r["feature_slug"] == "my_module"


def test_feature_slug_falls_back_to_full_id_when_no_double_underscore():
    r = _resolve(option_feature_id="noprefix")
    assert r["feature_slug"] == "noprefix"
