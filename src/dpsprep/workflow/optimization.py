import logging
import shutil

from dpsprep.logging import human_readable_size
from dpsprep.ocrmypdf_adapter import run_ocrmypdf_optimizer
from dpsprep.options import DpsPrepOptions


logger = logging.getLogger(__name__)


def attempt_to_optimize_result(options: DpsPrepOptions, djvu_size: int, combined_size: int) -> None:
    opt_success = False

    if options.optlevel is not None:
        logger.info(f'Performing level {options.optlevel} optimization.')
        opt_success = run_ocrmypdf_optimizer(options)

    if opt_success:
        opt_size = options.workdir.optimized_pdf_path.stat().st_size

        logger.info(f'The optimized file has size {human_readable_size(opt_size)}, which is {round(100 * opt_size / combined_size, 2)}% of the raw combined file and {round(100 * opt_size / djvu_size, 2)}% of the DjVu source file.')

        if opt_size < combined_size:
            logger.info('Using the optimized file.')
            shutil.copy(options.workdir.optimized_pdf_path, options.workdir.dest)
        else:
            logger.info('Using the raw combined file.')
            shutil.copy(options.workdir.combined_pdf_path, options.workdir.dest)
    else:
        shutil.copy(options.workdir.combined_pdf_path, options.workdir.dest)
