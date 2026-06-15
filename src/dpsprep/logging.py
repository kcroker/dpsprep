import logging

from rich.logging import RichHandler


def configure_logging(verbose: bool) -> None:
    base_logger = logging.getLogger('dpsprep')
    base_logger.setLevel(logging.DEBUG if verbose else logging.INFO)
    base_logger.addHandler(RichHandler(log_time_format='%X'))


def human_readable_size(size: int) -> str:
    if size < 1024:
        return f'{size} bytes'

    if size < 1024 ** 2:
        return f'{size / 1024:.02f} KiB'

    return f'{size / 1024 ** 2:.02f} MiB'
