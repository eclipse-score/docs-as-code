from pathlib import Path
from types import SimpleNamespace
from typing import cast

from html_options import return_html_theme_options
from sphinx.application import Sphinx


def test_default_logo_assets_are_available() -> None:
    app = cast(
        Sphinx,
        SimpleNamespace(config=SimpleNamespace(html_context={"github_user": "dummy"})),
    )

    logo = return_html_theme_options(app)["logo"]

    assert Path(logo["image_light"]).name == "Eclipse-S-CORE-colour-horizontal.png"
    assert Path(logo["image_dark"]).name == "Eclipse-S-CORE-dark.png"
    assert Path(logo["image_light"]).is_file()
    assert Path(logo["image_dark"]).is_file()
    assert logo["alt_text"] == "Eclipse S-CORE documentation - Home"
