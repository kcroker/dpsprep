import os
import sys

from loguru import logger


cached_stdout = sys.stdout


def configure_loguru(verbose: bool):
    logger.remove()
    logger.add(
        cached_stdout,
        format='<level>{level}</level> <green>{time:HH:mm:ss}</green> <level>{message}</level>',
        level='DEBUG' if verbose else 'INFO'
    )


def human_readable_size(size: int):
    if size < 1024:
      return f'{size} bytes'

    if size < 1024 ** 2:
      return f'{size / 1024:.02f} KiB'

    return f'{size / 1024 ** 2:.02f} MiB'


# img2pdf abuses debug logging by using print
# This is a way to temporarily silence it
class SilencePrint:
    def __enter__(self):
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = cached_stdout
