import enum
import logging
from dataclasses import dataclass


@dataclass(frozen=True)
class ExceptionWorkerMessage:
    error: BaseException


@dataclass(frozen=True)
class LogRecordWorkerMessage:
    record: logging.LogRecord


class TaskDoneType(enum.IntEnum):
    TEXT = enum.auto()
    IMAGE = enum.auto()


@dataclass(frozen=True)
class TaskDoneWorkerMessage:
    type: TaskDoneType
    page: int


WorkerMessage = ExceptionWorkerMessage | LogRecordWorkerMessage | TaskDoneWorkerMessage
