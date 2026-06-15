import enum
import json
import sys
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

import click

from dpsprep.workdir import WorkingDirectory


if sys.version_info < (3, 12):
    from typing_extensions import override
else:
    from typing import override

from dpsprep.exceptions import DpsPrepConfigError, DpsPrepParseError
from dpsprep.range import (
    RangeOptionGroup,
    parse_enum_range_group,
    parse_int_range_group,
)


# I have implemented better JSON types elsewhere, but here there is no point to do so.
JsonObject = Mapping[str, Any]


class ImageMode(enum.StrEnum):
    RGB = 'rgb'
    GRAYSCALE = 'grayscale'
    BITONAL = 'bitonal'
    INFER = 'infer'


DEFAULT_IMAGE_MODE = ImageMode.INFER


@dataclass(frozen=True)
class DpsPrepOptions:
    workdir: WorkingDirectory

    # Range options
    mode_overrides: RangeOptionGroup[ImageMode]
    dpi_overrides: RangeOptionGroup[int]
    quality_overrides: RangeOptionGroup[int]

    # Other options
    no_text: bool
    pool_size: int
    verbose: bool
    ocr_options: JsonObject | None
    optlevel: int | None


def parse_ocr_options(ocr_str: str | None, socr_str: str | None) -> JsonObject | None:
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


class OcrOptionClickType(click.ParamType):
    name = 'JSON object'

    @override
    def convert(self, value: str | JsonObject | None, param: click.Parameter | None, ctx: click.Context | None) -> JsonObject | None:
        if value is None:
            return None

        if isinstance(value, Mapping):
            return value

        try:
            ocr_options = json.loads(value)
        except ValueError:
            self.fail(f'The OCR option string {value!r} must be a JSON object.', param, ctx)

        if not isinstance(ocr_options, dict):
            self.fail(f'The OCR option string {value!r} must be a JSON object.', param, ctx)

        return ocr_options


class SocrOptionClickType(click.ParamType):
    name = 'comma-separated languages'

    @override
    def convert(self, value: str | JsonObject | None, param: click.Parameter | None, ctx: click.Context | None) -> JsonObject | None:
        if value is None:
            return None

        if isinstance(value, Mapping):
            return value

        return dict(languages=value.split(','))


class ImageModeOverridesClickType(click.ParamType):
    name = 'comma-separated image modes with page ranges'

    @override
    def convert(self, value: RangeOptionGroup[ImageMode] | str, param: click.Parameter | None, ctx: click.Context | None) -> RangeOptionGroup[ImageMode]:
        if isinstance(value, RangeOptionGroup):
            return value

        try:
            return parse_enum_range_group(value, ImageMode)
        except DpsPrepParseError as err:
            self.fail(str(err), param, ctx)



class DpiOverridesClickType(click.ParamType):
    name = 'comma-separated integers with page ranges'

    @override
    def convert(self, value: RangeOptionGroup[int] | str, param: click.Parameter | None, ctx: click.Context | None) -> RangeOptionGroup[int]:
        if isinstance(value, RangeOptionGroup):
            return value

        try:
            group = parse_int_range_group(value)
        except DpsPrepParseError as err:
            self.fail(str(err), param, ctx)

        for range_option in group.ranges:
            if range_option.value < 1:
                self.fail(f'Expected a positive DPI, but got {range_option.value}', param, ctx)

        return group


class QualityOverridesClickType(click.ParamType):
    name = 'comma-separated integers with page ranges'

    @override
    def convert(self, value: RangeOptionGroup[int] | str, param: click.Parameter | None, ctx: click.Context | None) -> RangeOptionGroup[int]:
        if isinstance(value, RangeOptionGroup):
            return value

        try:
            group = parse_int_range_group(value)
        except DpsPrepParseError as err:
            self.fail(str(err), param, ctx)

        for range_option in group.ranges:
            if not 1 <= range_option.value <= 100:
                self.fail(f'Expected quality option to be between 1 and 100, but got {range_option.value}', param, ctx)

        return group
