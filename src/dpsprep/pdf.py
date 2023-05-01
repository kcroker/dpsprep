import io
from typing import Iterable

from loguru import logger
from pypdf import PdfMerger
from reportlab.pdfgen.canvas import Canvas
import djvu.decode
import djvu.sexpr

from .paths import PdfPaths
from .text import TextDrawVisitor
from .images import djvu_page_to_image, compress_image


def djvu_page_to_pdf(page: djvu.decode.Page, quality: int):
    page_job = page.decode(wait=True)
    page.get_info()

    image = compress_image(
        djvu_page_to_image(page),
        quality
    )

    store = io.BytesIO()
    canvas = Canvas(store, pagesize=page_job.size)
    canvas.drawInlineImage(image, 0, 0)
    visitor = TextDrawVisitor(canvas)
    visitor.visit(page.text.sexpr)
    canvas.save()

    store.seek(0)
    return store


def merge_combined_from_fs(paths: PdfPaths, pages: Iterable[int]):
    sorted_pages = sorted(pages)

    if len(sorted_pages) == 1:
        logger.info(f'Outputting one page into {repr(str(paths.dest))}')
    else:
        logger.info(f'Merging {len(sorted_pages)} pages into {repr(str(paths.dest))}')

    output_pdf = PdfMerger()

    for i in sorted_pages:
        output_pdf.merge(
            page_number=i,
            fileobj=paths.get_page_pdf_path(i),
            import_outline=False
        )

    return output_pdf
