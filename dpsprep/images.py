import pathlib
from typing import Literal, NamedTuple

import djvu.decode
import djvu.sexpr
import loguru
import PIL.features
from PIL import Image, ImageOps

ImageMode = Literal['rgb', 'grayscale', 'bitonal', 'infer']


djvu_pixel_formats = {
    'rgb': djvu.decode.PixelFormatRgb(byte_order='RGB'),
    'grayscale': djvu.decode.PixelFormatGrey(),
    'bitonal': djvu.decode.PixelFormatPackedBits('>'),
}


for pixel_format in djvu_pixel_formats.values():
    pixel_format.rows_top_to_bottom = 1
    pixel_format.y_top_to_bottom = 0


pil_modes = {
    'rgb': 'RGB',
    'grayscale': 'L',
    'bitonal': '1',
}


class ProcessedPageBackground(NamedTuple):
    pil_image: Image.Image
    resolution: int


def process_djvu_page(page: djvu.decode.Page, mode: ImageMode, i: int) -> ProcessedPageBackground:
    page_job = page.decode(wait=True)
    width, height = page_job.size
    buffer = bytearray(3 * width * height) # RGB at most

    rect = (0, 0, width, height)

    if mode == 'infer':
        mode = 'bitonal' if page_job.type == djvu.decode.PAGE_TYPE_BITONAL else 'rgb'

    if mode == 'bitonal':
        if not PIL.features.check_codec('libtiff'):
            loguru.logger.warning('Bitonal image compression may suffer because Pillow has been built without libtiff support.')
    elif not PIL.features.check_codec('jpg'):
        loguru.logger.warning('Multitonal image compression may suffer because Pillow has been built without libjpeg support.')

    try:
        page_job.render(
            # RENDER_COLOR is simply a default value and doesn't actually imply colors
            mode=djvu.decode.RENDER_COLOR,
            page_rect=rect,
            render_rect=rect,
            pixel_format=djvu_pixel_formats[mode],
            buffer=buffer,
        )
    except djvu.decode.NotAvailable:
        loguru.logger.warning(f'libdjvu claims that data for page {i + 1} is not available. Producing a blank page.')
        image = Image.new(
            pil_modes['bitonal'],
            page_job.size,
            1,
        )

        return ProcessedPageBackground(image, page_job.dpi)

    image = Image.frombuffer(
        pil_modes[mode],
        page_job.size,
        buffer,
        'raw'
    )

    return ProcessedPageBackground(
        # I have experimentally determined that we need to invert the black-and-white images. -- Ianis, 2023-05-13
        # See also https://github.com/kcroker/dpsprep/issues/16
        ImageOps.invert(image) if mode == 'bitonal' else image,
        page_job.dpi
    )


def failsafe_save_djvu_page(page_bg: ProcessedPageBackground, target: pathlib.Path, quality: int | None, page_number: int) -> None:
    if quality is not None:
        if page_bg.pil_image.mode in pil_modes['bitonal'] and PIL.features.check_codec('libtiff'):
            loguru.logger.warning('Pillow uses TIFF for encoding bitonal PDF images. The encoder does not support a "quality" setting. If the conversion fails, please try again without specifying quality.')

        try:
            page_bg.pil_image.save(
                target,
                format='PDF',
                quality=quality,
                resolution=page_bg.resolution
            )
        except ValueError:
            loguru.logger.warning(f'Failed to encode page {page_number}. Trying again without setting quality.')
        else:
            return

    page_bg.pil_image.save(
        target,
        format='PDF',
        resolution=page_bg.resolution
    )
