import io

from PIL import Image
import djvu.decode
import djvu.sexpr


djvu_pixel_format = djvu.decode.PixelFormatRgb(byte_order='RGB')
djvu_pixel_format.rows_top_to_bottom = 1
djvu_pixel_format.y_top_to_bottom = 0


def djvu_page_to_image(page: djvu.decode.Page):
    page_job = page.decode(wait=True)
    width, height = page_job.size

    buffer = bytearray(3 * width * height)

    rect = (0, 0, width, height)
    page_job.render(
        mode=djvu.decode.RENDER_COLOR,
        page_rect=rect,
        render_rect=rect,
        pixel_format=djvu_pixel_format,
        row_alignment=3 * width, # RGB, 3 bytes per pixel
        buffer=buffer
    )

    return Image.frombuffer(
        'RGB',
        page_job.size,
        buffer,
        'raw'
    )


def compress_image(src: Image.Image, quality: int):
    assert 0 <= quality <= 100
    store = io.BytesIO()
    src.save(store, format='JPEG', quality=quality)
    dest = Image.open(store)
    return dest
