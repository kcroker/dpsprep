import logging
import pathlib
from typing import NamedTuple

import djvu.decode
import PIL.features
from PIL import Image, ImageOps

from dpsprep.options import DpsPrepOptions, ImageMode


logger = logging.getLogger(__name__)


djvu_pixel_formats = {
    ImageMode.RGB: djvu.decode.PixelFormatRgb(byte_order='RGB'),
    ImageMode.GRAYSCALE: djvu.decode.PixelFormatGrey(),
    ImageMode.BITONAL: djvu.decode.PixelFormatPackedBits('>'),
}


for pixel_format in djvu_pixel_formats.values():
    pixel_format.rows_top_to_bottom = 1
    pixel_format.y_top_to_bottom = 0


pil_modes = {
    ImageMode.RGB: 'RGB',
    ImageMode.GRAYSCALE: 'L',
    ImageMode.BITONAL: '1',
}


class ProcessedPageBackground(NamedTuple):
    pil_image: Image.Image
    resolution: int
    mode: ImageMode


def process_djvu_page(page: djvu.decode.Page, mode: ImageMode, i: int) -> ProcessedPageBackground:
    page_job = page.decode(wait=True)
    width, height = page_job.size
    buffer = bytearray(3 * width * height)  # RGB at most

    rect = (0, 0, width, height)

    if mode == ImageMode.INFER:
        mode = ImageMode.BITONAL if page_job.type == djvu.decode.PAGE_TYPE_BITONAL else ImageMode.RGB

    if mode == ImageMode.BITONAL:
        if not PIL.features.check_codec('libtiff'):
            logger.warning('Bitonal image compression may suffer because Pillow has been built without libtiff support.')
    elif not PIL.features.check_codec('jpg'):
        logger.warning('Multitonal image compression may suffer because Pillow has been built without libjpeg support.')

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
        logger.warning(f'libdjvu claims that data for page {i + 1} is not available. Producing a blank page.')
        image = Image.new(
            pil_modes[ImageMode.BITONAL],
            page_job.size,
            1,
        )

        return ProcessedPageBackground(image, page_job.dpi, ImageMode.BITONAL)

    image = Image.frombuffer(
        pil_modes[mode],
        page_job.size,
        buffer,
        'raw',
    )

    return ProcessedPageBackground(
        # I have experimentally determined that we need to invert the black-and-white images. -- Ianis, 2023-05-13
        # See also https://github.com/kcroker/dpsprep/issues/16
        ImageOps.invert(image) if mode == ImageMode.BITONAL else image,
        page_job.dpi,
        mode,
    )


def failsafe_save_djvu_page(page_bg: ProcessedPageBackground, target: pathlib.Path, options: DpsPrepOptions, i: int) -> None:
    quality = options.quality_overrides.get_value_for_zero_based_page(i)
    dpi = options.dpi_overrides.get_value_for_zero_based_page(i) or page_bg.resolution

    if quality is not None:
        if page_bg.pil_image.mode in pil_modes[ImageMode.BITONAL] and PIL.features.check_codec('libtiff'):
            logger.warning('Pillow uses TIFF for encoding bitonal PDF images. The encoder does not support a "quality" setting. If the conversion fails, please try again without specifying quality.')

        try:
            page_bg.pil_image.save(
                target,
                format='PDF',
                quality=quality,
                resolution=dpi,
            )
        except ValueError:
            logger.warning(f'Failed to encode page {i}. Trying again without setting quality.')
        else:
            return

    page_bg.pil_image.save(
        target,
        format='PDF',
        resolution=dpi,
    )
