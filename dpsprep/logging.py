import os
import sys
from types import TracebackType
from typing import Union

import loguru

cached_stdout = sys.stdout


def configure_loguru(*, verbose: bool) -> None:
    loguru.logger.remove()
    loguru.logger.add(
        cached_stdout,
        format='<level>{level}</level> <green>{time:HH:mm:ss}</green> <level>{message}</level>',
        level='DEBUG' if verbose else 'INFO',
    )


def human_readable_size(size: int) -> str:
    if size < 1024:
      return f'{size} bytes'

    if size < 1024 ** 2:
      return f'{size / 1024:.02f} KiB'

    return f'{size / 1024 ** 2:.02f} MiB'


# img2pdf abuses debug logging by using print
# This is a way to temporarily silence it
class SilencePrint:
    def __enter__(self) -> None:
        sys.stdout = open(os.devnull, 'w')

    def __exit__(
        self,
        exc_type: Union[type[BaseException], None],
        exc_value: Union[BaseException, None],
        traceback: Union[TracebackType, None]
     ) -> None:
        sys.stdout.close()
        sys.stdout = cached_stdout
