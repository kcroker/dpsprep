import argparse
import shutil
from typing import Any

import loguru

from .workdir import WorkingDirectory

# We use OCRmyPDF in a non-canonical way: only optimize the file without performing any OCR.
# The optimization procedure provides good results and preserves the text layer and outline.
# The code here is based on
# https://github.com/ocrmypdf/OCRmyPDF/blob/fb006ef39f7f8842dec1976bebe4bcd5ca2e8df8/src/ocrmypdf/optimize.py#L724


class OptimizeOptions(argparse.Namespace):
    """Emulate ocrmypdf's options."""

    input_file: str
    jobs: int
    optimize: int
    jpeg_quality: int
    png_quality: int
    jbig2_page_group_size: int
    jbig2_lossy: bool
    jbig2_threshold: float
    quiet: bool
    progress_bar: bool

    def __init__(
        self, input_file: str, jobs: int, optimize_: int, jpeg_quality: int, png_quality: int,
    ) -> None:
        self.input_file = input_file
        self.jobs = jobs
        self.optimize = optimize_
        self.jpeg_quality = jpeg_quality
        self.png_quality = png_quality
        self.jbig2_page_group_size = 0
        self.jbig2_lossy = False
        self.jbig2_threshold = 0.85 # This seems to be the default
        # Changing the two verbosity options seems to have no effect in this concrete case
        self.quiet = True
        self.progress_bar = False


def optimize_pdf(workdir: WorkingDirectory, optlevel: int, quality: int, pool_size: int) -> bool:
    try:
        # ObjectStreamMode is actually from pikepdf, but I did not want to include that as a dependency
        from ocrmypdf.optimize import ObjectStreamMode, PdfContext, optimize
        from ocrmypdf.pdfinfo import PdfInfo
    except ImportError:
        loguru.logger.warning('Cannot detect OCRmyPDF. No optimizations will be performed on the output file.')
        shutil.copy(workdir.combined_pdf_path, workdir.optimized_pdf_path)
        return False

    options = OptimizeOptions(
        input_file=str(workdir.combined_pdf_path),
        jobs=pool_size,  # These correspond to CPU cores rather than threads, but it seems better to use the available pool size parameter
        optimize_=optlevel,
        jpeg_quality=quality,
        png_quality=quality,
    )

    info = PdfInfo(workdir.combined_pdf_path)
    context = PdfContext(options, workdir.ocrmypdf_tmp_path, workdir.combined_pdf_path, info, None)

    optimize(
        workdir.combined_pdf_path,
        workdir.optimized_pdf_path,
        context,
        {
            'compress_streams': True,
            'preserve_pdfa': True,
            'object_stream_mode': ObjectStreamMode.generate,
        },
    )

    return True


def perform_ocr(workdir: WorkingDirectory, options: dict[str, Any]) -> bool:
    try:
        from ocrmypdf import api
    except ImportError:
        loguru.logger.warning('Cannot detect OCRmyPDF. No OCR will be performed on the output file.')
        shutil.copy(workdir.combined_pdf_without_text_path, workdir.combined_pdf_path)
        return False

    try:
        api.ocr(
            input_file=workdir.combined_pdf_without_text_path,
            output_file=workdir.combined_pdf_path,
            **options,
        )
    except Exception as err:  # noqa: BLE001
        loguru.logger.warning(f'OCRmyPDF failed: {err}')
        shutil.copy(workdir.combined_pdf_without_text_path, workdir.combined_pdf_path)
        return False
    else:
        return True
