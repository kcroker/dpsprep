from typing import Protocol

import djvu.decode
from PIL import Image
from pytest_image_diff.plugin import DiffCompareResult

from .images import process_djvu_page


class ImageDiffProtocol(Protocol):
    def __call__(self, a: Image.Image, b: Image.Image, threshold: float = 1e-3) -> DiffCompareResult:
        ...


def test_process_djvu_page_bitonal(image_diff: ImageDiffProtocol) -> None:
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI('fixtures/lipsum_words.djvu'),
    )
    document.decoding_job.wait()

    fixture = Image.open('fixtures/lipsum_01.png')
    result = process_djvu_page(document.pages[0], mode='infer', i=0)

    page_decode_job = document.pages[0].decode()
    page_decode_job.wait()
    assert result.resolution == page_decode_job.dpi

    # pytest_image_diff (as of v0.0.14) wants to convert monochrome images to transparent grayscale (LA) mode and fails.
    # With Pillow 12, if we do it manually, the diff fails. Luckily, it doesn't fail with RGBA mode.
    assert image_diff(fixture.convert('RGBA'), result.pil_image.convert('RGBA'), threshold=1e-2)
