# ruff: file-ignore[unused-function-argument]

"""This is a PEP-517 in-tree build backend that solves a chicken-and-egg problem.

We want the wheels to contain the man page, which is generated dynamically.
Building the man page requires the project dependencies to be installed,
which in turn requires listing them in the build-system.requires array.

Since we already have the project dependencies set up, we simply inject them.
"""
import contextlib
import tomllib
from collections.abc import Sequence
from typing import TYPE_CHECKING

import hatchling.build

# ruff: ignore[unused-import]
from hatchling.build import build_sdist, get_requires_for_build_sdist


with contextlib.suppress(ImportError):
    # ruff: ignore[unused-import]
    from hatchling.build import (
        build_editable,
        get_requires_for_build_editable,
        prepare_metadata_for_build_editable,
        prepare_metadata_for_build_wheel,
    )


if TYPE_CHECKING:
    from dpsprep.options import JsonObject


from .paths import ROOT


def get_requires_for_build_wheel(config_settings: 'dict[str, JsonObject] | None' = None) -> Sequence[str]:
    with open(ROOT / 'pyproject.toml', 'rb') as file:
        contents = tomllib.load(file)

    return contents['project']['dependencies'] + contents['dependency-groups']['man']


def build_wheel(
    wheel_directory: str,
    config_settings: 'dict[str, JsonObject] | None' = None,
    metadata_directory: str | None = None,
) -> str:
    # ruff: ignore[import-outside-top-level]
    from .docs import build_man_page
    build_man_page()
    return hatchling.build.build_wheel(wheel_directory, config_settings, metadata_directory)
