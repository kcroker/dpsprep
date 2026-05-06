import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from typing import Any, Literal, cast, get_args

import click
from typing_extensions import override

from dpsprep.exceptions import DpsPrepConfigError
from dpsprep.ranges import (
    RangeOption,
    RangeOptionGroup,
    parse_int_range_option,
    parse_str_range_option,
)


# I have implemented better JSON types elsewhere, but here there is no point to do so.
JsonObject = Mapping[str, Any]
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
    def convert(self, value: str, param: click.Parameter | None, ctx: click.Context | None) -> JsonObject | None:
        return dict(languages=value.split(','))


class ImageModeOverridesClickType(click.ParamType):
    name = 'comma-separated image modes with page ranges'

    def _iter_convert(self, value: str, param: click.Parameter | None, ctx: click.Context | None) -> Iterator[RangeOption[ImageMode]]:
        if value == '':
            return

        for segment in value.split(','):
            try:
                option = parse_str_range_option(segment)
            except DpsPrepConfigError as err:
                self.fail(str(err), param, ctx)

            if option.value not in IMAGE_MODES:
                self.fail(f'Expected one of {", ".join(IMAGE_MODES)}, but got {option.value}', param, ctx)

            yield cast('RangeOption[ImageMode]', option)

    @override
    def convert(self, value: RangeOptionGroup[ImageMode] | str, param: click.Parameter | None, ctx: click.Context | None) -> RangeOptionGroup[ImageMode]:
        if isinstance(value, RangeOptionGroup):
            return value

        return RangeOptionGroup(list(self._iter_convert(value, param, ctx)))


class DpiOverridesClickType(click.ParamType):
    name = 'comma-separated integers with page ranges'

    def _iter_convert(self, value: str, param: click.Parameter | None, ctx: click.Context | None) -> Iterator[RangeOption[int]]:
        if value == '':
            return

        for segment in value.split(','):
            try:
                option = parse_int_range_option(segment)
            except DpsPrepConfigError as err:
                self.fail(str(err), param, ctx)

            if option.value < 1:
                self.fail(f'Expected a positive DPI, but got {option.value}', param, ctx)

            yield option

    @override
    def convert(self, value: RangeOptionGroup[int] | str, param: click.Parameter | None, ctx: click.Context | None) -> RangeOptionGroup[int]:
        if isinstance(value, RangeOptionGroup):
            return value

        return RangeOptionGroup(list(self._iter_convert(value, param, ctx)))


class QualityOverridesClickType(click.ParamType):
    name = 'comma-separated integers with page ranges'

    def _iter_convert(self, value: str, param: click.Parameter | None, ctx: click.Context | None) -> Iterator[RangeOption[int]]:
        if value == '':
            return

        for segment in value.split(','):
            try:
                option = parse_int_range_option(segment)
            except DpsPrepConfigError as err:
                self.fail(str(err), param, ctx)

            if not 1 <= option.value <= 100:
                self.fail(f'Expected quality option to be between 1 and 100, but got {option.value}', param, ctx)

            yield option

    @override
    def convert(self, value: RangeOptionGroup[int] | str, param: click.Parameter | None, ctx: click.Context | None) -> RangeOptionGroup[int]:
        if isinstance(value, RangeOptionGroup):
            return value

        return RangeOptionGroup(list(self._iter_convert(value, param, ctx)))
