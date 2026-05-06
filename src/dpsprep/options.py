import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Literal, cast, get_args

from dpsprep.exceptions import DpsPrepConfigError
from dpsprep.ranges import (
    RangeOptionGroup,
    parse_int_range_group_option,
    parse_str_range_group_option,
)


# I have implemented better JSON types elsewhere, but here there is no point to do so.
Json = Mapping[str, Any]
ImageMode = Literal['rgb', 'grayscale', 'bitonal', 'infer']
IMAGE_MODES = get_args(ImageMode)

DEFAULT_IMAGE_MODE: ImageMode = 'infer'


@dataclass(frozen=True)
class DpsPrepOptions:
    # Range options
    mode_overrides: RangeOptionGroup[ImageMode]
    dpi_overrides: RangeOptionGroup[int]
    quality_overrides: RangeOptionGroup[int]

    # Other options
    no_text: bool
    pool_size: int
    verbose: bool
    ocr_options: Json | None
    optlevel: int | None


def parse_ocr_options(ocr_str: str | None, socr_str: str | None) -> Json | None:
    if socr_str is not None:
        if ocr_str is not None:
            raise DpsPrepConfigError('Cannot specify both --ocr and -socr simultaneously.')

        return dict(languages=socr_str.split(','))

    if ocr_str is None:
        return None

    try:
        options = json.loads(ocr_str)
    except ValueError as err:
        raise DpsPrepConfigError(f'The OCR option string {ocr_str!r} must be a JSON object.') from err

    if not isinstance(options, dict):
        raise DpsPrepConfigError(f'The OCR option string {ocr_str!r} must be a JSON object.')

    return options


def parse_mode_option(string: str) -> RangeOptionGroup[ImageMode]:
    group = parse_str_range_group_option(string)

    for range_ in group.ranges:
        if range_.value not in IMAGE_MODES:
            raise DpsPrepConfigError(f'Invalid image mode {range_.value}')

    return cast('RangeOptionGroup[ImageMode]', group)


def parse_dpi_option(string: str) -> RangeOptionGroup[int]:
    group = parse_int_range_group_option(string)

    for range_ in group.ranges:
        if range_.value < 1:
            raise DpsPrepConfigError(f'Invalid DPI {range_.value}')

    return group


def parse_quality_option(string: str) -> RangeOptionGroup[int]:
    group = parse_int_range_group_option(string)

    for range_ in group.ranges:
        if not 1 <= range_.value <= 100:
            raise DpsPrepConfigError(f'Expected quality option to be between 1 and 100, but got {range_.value}')

    return group


def parse_all_options(
    # Options that need parsing
    ocr: str | None,
    socr: str | None,
    mode: str,
    dpi: str,
    quality: str,

    # Options that don't need parsing
    no_text: bool,
    pool_size: int,
    verbose: bool,
    optlevel: int | None,
) -> DpsPrepOptions:
    ocr_options = parse_ocr_options(ocr, socr)

    if ocr_options:
        no_text = True

    return DpsPrepOptions(
        mode_overrides=parse_mode_option(mode),
        dpi_overrides=parse_dpi_option(dpi),
        quality_overrides=parse_quality_option(quality),

        no_text=no_text,
        ocr_options=ocr_options,
        optlevel=optlevel,
        pool_size=pool_size,
        verbose=verbose,
    )

