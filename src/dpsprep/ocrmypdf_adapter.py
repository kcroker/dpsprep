# We use OCRmyPDF in a non-canonical way: only optimize the file without performing any OCR.
# The optimization procedure provides good results and preserves the text layer and outline.
# The code here is based on
#   https://github.com/ocrmypdf/OCRmyPDF/blob/fb006ef39f7f8842dec1976bebe4bcd5ca2e8df8/src/ocrmypdf/optimize.py#L724
# with some simplifications for OCRmyPDF 17

# ruff: noqa: PLC0415

import shutil

import loguru

from dpsprep.options import DpsPrepOptions, Json
from dpsprep.workdir import WorkingDirectory


def run_ocrmypdf_optimizer(workdir: WorkingDirectory, options: DpsPrepOptions) -> bool:
    if options.optlevel is None:
        return False

    try:
        # ObjectStreamMode is actually from pikepdf, but I did not want to include that as a dependency
        from ocrmypdf._options import OcrOptions
        from ocrmypdf.optimize import ObjectStreamMode, PdfContext, optimize
        from ocrmypdf.pdfinfo import PdfInfo
    except ImportError:
        loguru.logger.warning('Cannot detect OCRmyPDF. No optimizations will be performed on the output file.')
        return False

    quality = options.quality_overrides.get_global_value()

    omp_options = OcrOptions(
        input_file=workdir.combined_pdf_without_text_path,
        output_file=workdir.combined_pdf_path,
        # Jobs correspond to CPU cores rather than threads, but it seems better to use the available pool size parameter
        jobs=options.pool_size,
        optimize=options.optlevel,
        # When set to 0, OCRmyPDF's "optimize" function attempts to adjust them
        jpg_quality=quality or 0,
        png_quality=quality or 0,
    )

    info = PdfInfo(workdir.combined_pdf_path)
    context = PdfContext(omp_options, workdir.ocrmypdf_tmp_path, workdir.combined_pdf_path, info, None)

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


def perform_ocr(workdir: WorkingDirectory, options: Json) -> bool:
    try:
        from ocrmypdf import api
    except ImportError:
        loguru.logger.warning('Cannot detect OCRmyPDF. No OCR will be performed on the output file.')
        return False

    try:
        api.ocr(
            input_file_or_options=workdir.combined_pdf_without_text_path,
            output_file=workdir.combined_pdf_path,
            **options,
        )
    except Exception as err:
        loguru.logger.warning(f'OCRmyPDF failed: {err}')
        shutil.copy(workdir.combined_pdf_without_text_path, workdir.combined_pdf_path)
        return False
    else:
        return True
