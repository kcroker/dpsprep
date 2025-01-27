from typing import Protocol

import djvu.decode
from PIL import Image
from pytest_image_diff.plugin import DiffCompareResult

from .images import djvu_page_to_image


class ImageDiffProtocol(Protocol):
    def __call__(self, a: Image.Image, b: Image.Image, threshold: float = 1e-3) -> DiffCompareResult:
        ...


def test_djvu_page_to_image_bitonal(image_diff: ImageDiffProtocol) -> None:
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI('fixtures/lipsum_words.djvu'),
    )
    document.decoding_job.wait()

    fixture = Image.open('fixtures/lipsum_01.png')
    result = djvu_page_to_image(document.pages[0], mode='infer', i=0)

    # pytest_image_diff (as of v0.0.14) wants to convert monochrome images to LA mode and fails, so we do it manually
    assert image_diff(fixture.convert('LA'), result.convert('LA'), threshold=1e-2)
