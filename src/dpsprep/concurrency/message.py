import logging
from dataclasses import dataclass


@dataclass(frozen=True)
class ExceptionWorkerMessage:
    error: BaseException


@dataclass(frozen=True)
class LogRecordWorkerMessage:
    record: logging.LogRecord


@dataclass(frozen=True)
class TaskDoneWorkerMessage:
    pass


WorkerMessage = ExceptionWorkerMessage | LogRecordWorkerMessage | TaskDoneWorkerMessage
