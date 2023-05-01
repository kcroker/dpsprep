import sys

from pytest import Session
from loguru import logger


def pytest_sessionstart(session: Session):
    logger.remove()
    logger.add(
        sys.stdout,
        format='<level>{level}</level> <green>{time:HH:mm:ss}</green> <level>{message}</level>',
        level='DEBUG'
    )
