import os
import sys
from types import TracebackType

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
    # ruff: disable[PLR2004]
    if size < 1024:
        return f'{size} bytes'

    if size < 1024 ** 2:
        return f'{size / 1024:.02f} KiB'

    return f'{size / 1024 ** 2:.02f} MiB'
    # ruff: enable[PLR2004]


# img2pdf abuses debug logging by using print
# This is a way to temporarily silence it
class SilencePrint:
    def __enter__(self) -> None:
        sys.stdout = open(os.devnull, 'w', encoding='utf-8')

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
     ) -> None:
        sys.stdout.close()
        sys.stdout = cached_stdout
