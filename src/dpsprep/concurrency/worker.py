import logging
import signal
from typing import TYPE_CHECKING

import djvu.decode

from dpsprep.options import DpsPrepOptions
from dpsprep.workflow.processing import process_page_bg, process_text

from .message import LogRecordWorkerMessage, TaskDoneWorkerMessage, WorkerMessage


if TYPE_CHECKING:
    from multiprocessing.connection import Connection


logger = logging.getLogger(__name__)


class SubprocessWorkerLoggerHandler(logging.Handler):
    conn: 'Connection[WorkerMessage]'

    def __init__(self, conn: 'Connection[WorkerMessage]') -> None:
        super().__init__()
        self.conn = conn

    def emit(self, record: logging.LogRecord) -> None:
        self.conn.send(LogRecordWorkerMessage(record))


class SubprocessWorker:
    options: DpsPrepOptions
    child_conn: 'Connection[WorkerMessage]'

    def __init__(self, options: DpsPrepOptions, child_conn: 'Connection[WorkerMessage]') -> None:
        self.options = options
        self.child_conn = child_conn

    def setup_child_process(self) -> None:
        # First, we disable the SIGINT handler altogether.
        # See https://stackoverflow.com/a/6191991/2756776
        signal.signal(signal.SIGINT, signal.SIG_IGN)

        # Then, we setup a special logger that pipes its messages to the parent via a multiprocessing Pipe.
        base_logger = logging.getLogger('dpsprep')
        base_logger.setLevel(logging.DEBUG if self.options.verbose else logging.INFO)
        base_logger.handlers.clear()
        base_logger.addHandler(SubprocessWorkerLoggerHandler(self.child_conn))

    def process_text(self) -> None:
        self.setup_child_process()

        # The document must be read anew because the underlying structures are not properly copied.
        document = djvu.decode.Context().new_document(
            djvu.decode.FileURI(self.options.workdir.src),
        )
        document.decoding_job.wait()

        process_text(self.options, document)
        self.child_conn.send(TaskDoneWorkerMessage())

    def process_page_bg(self, worker_id: int) -> None:
        self.setup_child_process()

        # The document must be read anew because the underlying structures are not properly copied.
        document = djvu.decode.Context().new_document(
            djvu.decode.FileURI(self.options.workdir.src),
        )
        document.decoding_job.wait()

        for i in range(worker_id, len(document.pages), self.options.pool_size):
            process_page_bg(self.options, document, i)
            self.child_conn.send(TaskDoneWorkerMessage())
