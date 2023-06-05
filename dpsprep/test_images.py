from typing import Protocol

from pytest_image_diff.plugin import DiffCompareResult
from PIL import Image
import djvu.decode

from .images import djvu_page_to_image


class ImageDiffProtocol(Protocol):
    def __call__(self, a: Image.Image, b: Image.Image, threshold: float = 1e-3) -> DiffCompareResult:
        ...


def test_djvu_page_to_image_bitonal(image_diff: ImageDiffProtocol):
    document = djvu.decode.Context().new_document(
        djvu.decode.FileURI('fixtures/lipsum_words.djvu')
    )
    document.decoding_job.wait()

    fixture = Image.open('fixtures/lipsum_01.png').convert('1')
    result = djvu_page_to_image(document.pages[0], i=0)

    assert image_diff(fixture, result, threshold=1e-2)
