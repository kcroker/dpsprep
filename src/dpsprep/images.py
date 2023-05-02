from typing import Literal

from PIL import Image, ImageOps
from loguru import logger
import djvu.decode
import djvu.sexpr


ImageMode = Literal['rgb', 'grayscale', 'bitonal']


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


def djvu_page_to_image(page: djvu.decode.Page, mode: ImageMode) -> Image.Image:
    page_job = page.decode(wait=True)
    width, height = page_job.size
    buffer = bytearray(3 * width * height) # RGB at most

    rect = (0, 0, width, height)
    page_job.render(
        # RENDER_COLOR is simply a default value and doesn't actually imply colors
        mode=djvu.decode.RENDER_COLOR,
        page_rect=rect,
        render_rect=rect,
        pixel_format=djvu_pixel_formats[mode],
        buffer=buffer
    )

    image = Image.frombuffer(
        pil_modes[mode],
        page_job.size,
        buffer,
        'raw'
    )

    # Monochrome images are read as inverted for some reason
    if mode == 'bitonal':
        return ImageOps.invert(image)

    return image
