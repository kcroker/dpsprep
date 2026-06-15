import logging

import djvu.decode

from dpsprep.logging import human_readable_size
from dpsprep.options import DpsPrepOptions

from .processor import SubprocessDocumentProcessor


logger = logging.getLogger(__name__)


# Due to some compatibility issues, we only support multiprocessing-based concurrency with explicit message passing.
# This is discussed in the concurrency notes in the project's wiki.
def concurrently_process_document(options: DpsPrepOptions, document: djvu.decode.Document) -> None:
    djvu_size = options.workdir.src.stat().st_size
    logger.info(f'Processing {options.workdir.src} with {len(document.pages)} pages and size {human_readable_size(djvu_size)} using {options.pool_size} workers.')

    proc = SubprocessDocumentProcessor(options, document)
    proc.process()

    logger.info('Processed all pages.')
