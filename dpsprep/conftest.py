from pytest import Session

from .logging import configure_loguru


def pytest_sessionstart(session: Session):
    configure_loguru(verbose=True)
