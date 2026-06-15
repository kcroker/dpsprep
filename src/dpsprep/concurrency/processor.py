# Due to some compatibility issues, we only support multiprocessing-based concurrency with explicit message passing.
# This is discussed in the concurrency notes in the project's wiki.

import logging
import multiprocessing
from multiprocessing.pool import Pool
from typing import TYPE_CHECKING

import djvu.decode
from rich.progress import Progress, TaskID

from dpsprep.concurrency.message import ExceptionWorkerMessage, LogRecordWorkerMessage, TaskDoneWorkerMessage
from dpsprep.exceptions import DpsPrepConcurrencyError
from dpsprep.options import DpsPrepOptions

from .worker import SubprocessWorker


if TYPE_CHECKING:
    from multiprocessing.connection import Connection

    from .message import WorkerMessage


logger = logging.getLogger(__name__)


class SubprocessDocumentProcessor:
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

        self.rich_progress = Progress()
        self.rich_task = self.rich_progress.add_task('Processing', total=len(document.pages) + 1)

        self.active_tasks = 0

    def on_child_error(self, err: BaseException | None) -> None:
        if err:
            logger.exception('Worker error.', exc_info=err)
            self.child_conn.send(ExceptionWorkerMessage(err))

    def process(self) -> None:
        worker = SubprocessWorker(self.options, self.child_conn)

        with self.rich_progress:
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

            while not self.rich_progress.finished:
                try:
                    if self.parent_conn.poll(0.1):
                        match data := self.parent_conn.recv():
                            case ExceptionWorkerMessage():
                                raise DpsPrepConcurrencyError('Worker error') from data.error  # noqa: TRY301

                            case LogRecordWorkerMessage():
                                logger.handle(data.record)

                            case TaskDoneWorkerMessage():
                                self.rich_progress.advance(self.rich_task)

                except KeyboardInterrupt:
                    logger.info('Conversion interrupted. Terminating all workers.')
                    self.pool.terminate()
                    raise

                except DpsPrepConcurrencyError:
                    logger.info('Terminating all other workers.')
                    self.pool.terminate()
                    raise

            self.pool.join()
