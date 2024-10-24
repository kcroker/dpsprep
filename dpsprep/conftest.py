import loguru
import pytest


@pytest.fixture(autouse=True)
def disable_loguru() -> None:
    loguru.logger.remove()
