import shutil

import loguru

from dpsprep.logging import human_readable_size
from dpsprep.ocrmypdf_adapter import run_ocrmypdf_optimizer
from dpsprep.options import DpsPrepOptions
from dpsprep.workdir import WorkingDirectory


def attempt_to_optimize_result(workdir: WorkingDirectory, options: DpsPrepOptions, djvu_size: int, combined_size: int) -> None:
    opt_success = False

    if options.optlevel is not None:
        loguru.logger.info(f'Performing level {options.optlevel} optimization.')
        opt_success = run_ocrmypdf_optimizer(workdir, options)

    if opt_success:
        opt_size = workdir.optimized_pdf_path.stat().st_size

        loguru.logger.info(f'The optimized file has size {human_readable_size(opt_size)}, which is {round(100 * opt_size / combined_size, 2)}% of the raw combined file and {round(100 * opt_size / djvu_size, 2)}% of the DjVu source file.')

        if opt_size < combined_size:
            loguru.logger.info('Using the optimized file.')
            shutil.copy(workdir.optimized_pdf_path, workdir.dest)
        else:
            loguru.logger.info('Using the raw combined file.')
            shutil.copy(workdir.combined_pdf_path, workdir.dest)
    else:
        shutil.copy(workdir.combined_pdf_path, workdir.dest)
