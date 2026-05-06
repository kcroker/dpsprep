import sys

import loguru


LOGURU_FORMAT = '<level>{level}</level> <green>{time:HH:mm:ss}</green> <level>{message}</level>'
LOGURU_WARNING_LEVEL = 30


def configure_loguru(*, verbose: bool) -> None:
    loguru.logger.remove()

    loguru.logger.add(
        sys.stderr,
        format=LOGURU_FORMAT,
        level='WARNING',
    )

    loguru.logger.add(
        sys.stdout,
        filter=lambda record: record['level'].no < LOGURU_WARNING_LEVEL,
        format=LOGURU_FORMAT,
        level='DEBUG' if verbose else 'INFO',
    )


def human_readable_size(size: int) -> str:
    if size < 1024:
        return f'{size} bytes'

    if size < 1024 ** 2:
        return f'{size / 1024:.02f} KiB'

    return f'{size / 1024 ** 2:.02f} MiB'
