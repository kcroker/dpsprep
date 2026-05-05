import djvu.decode
from PIL import Image, ImageChops, ImageStat

from .images import process_djvu_page


# A simple score function for Pillow images.
# We previously used the pytest-image-diff module, which used the diffimg module.
# It turned out that diffimg uses a similar approach, so we dropped the dependency in favor of a few-liner.
def calculate_image_diff_score(a: Image.Image, b: Image.Image) -> float:
    assert a.size == b.size, 'We only support diffing images with identical sizes'
    assert a.mode == b.mode, 'We only support diffing images with the same mode'

    diff = ImageChops.difference(a, b)
    stat = ImageStat.Stat(diff)
    return max(stat.rms) / 256  # The ImageStat module uses 256 bins


def test_process_djvu_page_bitonal() -> None:
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI('fixtures/lipsum_words.djvu'),
    )
    document.decoding_job.wait()

    fixture = Image.open('fixtures/lipsum_01.png')
    result = process_djvu_page(document.pages[0], mode='infer', i=0)

    page_decode_job = document.pages[0].decode()
    page_decode_job.wait()
    assert result.resolution == page_decode_job.dpi

    assert calculate_image_diff_score(fixture, result.pil_image) < 0.05
