import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from dpsprep.exceptions import DpsPrepConfigError
from dpsprep.images import ImageMode


# I have implemented better JSON types elsewhere, but here there is no point to do so.
Json = Mapping[str, Any]


@dataclass(frozen=True)
class DpsPrepOptions:
    mode: ImageMode
    no_text: bool
    pool_size: int
    verbose: bool
    dpi: int | None
    ocr_options: Json | None
    optlevel: int | None
    quality: int | None


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
