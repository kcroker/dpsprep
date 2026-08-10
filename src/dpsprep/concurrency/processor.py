# Due to some compatibility issues, we only support multiprocessing-based concurrency with explicit message passing.
# This is discussed in the concurrency notes in the project's wiki.

import logging
import multiprocessing
from multiprocessing.pool import Pool
from typing import TYPE_CHECKING

import djvu.decode
from rich.progress import Progress, TaskID

from dpsprep.exceptions import DpsPrepConcurrencyError
from dpsprep.options import DpsPrepOptions

from .counter import PageCounter
from .message import (
    ExceptionWorkerMessage,
    ImagePageProcessedMessage,
    LogRecordWorkerMessage,
    TextLayerAlreadyProcessedMessage,
    TextPageProcessedMessage,
)
from .worker import SubprocessWorker


if TYPE_CHECKING:
    from multiprocessing.connection import Connection

    from .message import WorkerMessage


logger = logging.getLogger(__name__)


class SubprocessPageProcessor:
    options: DpsPrepOptions
    document: djvu.decode.Document

    parent_conn: 'Connection[WorkerMessage]'
    child_conn: 'Connection[WorkerMessage]'
    pool: Pool

    rich_progress: Progress
    rich_task: TaskID

    def __init__(self, options: DpsPrepOptions, document: djvu.decode.Document) -> None:
        self.options = options
        self.document = document

        self.parent_conn, self.child_conn = multiprocessing.Pipe()
        self.pool = Pool(processes=self.options.pool_size)

    def on_child_error(self, err: BaseException | None) -> None:
        if err:
            logger.exception('Worker error.', exc_info=err)
            self.child_conn.send(ExceptionWorkerMessage(err))

    # ruff: ignore[complex-structure]
    def process(self) -> None:
        worker = SubprocessWorker(self.options, self.child_conn)
        counter = PageCounter(len(self.document.pages))

        rich_progress = Progress()
        rich_task = rich_progress.add_task('Processing pages', total=counter.total)

        with rich_progress:  # ruff: ignore[too-many-nested-blocks]
            if not self.options.no_text:
                self.pool.apply_async(
                    worker.process_text,
                    error_callback=self.on_child_error,
                )

            for worker_id in range(self.options.pool_size):
                self.pool.apply_async(
                    worker.process_page_bg, [worker_id],
                    error_callback=self.on_child_error,
                )

            self.pool.close()

            while not rich_progress.finished:
                # ruff: ignore[too-many-statements-in-try-clause]
                try:
                    if self.parent_conn.poll(0.1):
                        match message := self.parent_conn.recv():
                            case ExceptionWorkerMessage():
                                # ruff: ignore[raise-within-try]
                                raise DpsPrepConcurrencyError('Worker error') from message.error

                            case LogRecordWorkerMessage():
                                logger.handle(message.record)

                            case ImagePageProcessedMessage():
                                counter.images[message.page] = True

                                if counter.text[message.page]:
                                    rich_progress.advance(rich_task)

                            case TextPageProcessedMessage():
                                counter.text[message.page] = True

                                if counter.images[message.page]:
                                    rich_progress.advance(rich_task)

                            case TextLayerAlreadyProcessedMessage():
                                for page in range(counter.total):
                                    counter.text[page] = True

                                    if counter.images[page]:
                                        rich_progress.advance(rich_task)

                except KeyboardInterrupt:
                    logger.info('Conversion interrupted. Terminating all workers.')
                    self.pool.terminate()
                    raise

                except DpsPrepConcurrencyError:
                    logger.info('Terminating all other workers.')
                    self.pool.terminate()
                    raise

            self.pool.join()
