import hashlib
import logging
import os
import pathlib
import shutil
import tempfile

from dpsprep.workdir import WorkingDirectory


HASHING_BUFFER_SIZE = 64 * 1024
logger = logging.getLogger(__name__)


def get_file_hash(path: os.PathLike | str) -> str:
    h = hashlib.blake2b(digest_size=4)

    with open(path, 'rb') as file:
        data = file.read(HASHING_BUFFER_SIZE)

        while len(data) > 0:
            h.update(data)
            data = file.read(HASHING_BUFFER_SIZE)

    return h.hexdigest()


def initialize_workdir(
    src: os.PathLike | str,
    dest: os.PathLike | str | None,
    delete_existing: bool = False,
) -> WorkingDirectory:
    # Working path
    # If possible, we avoid the ephemeral storage /tmp
    persistent_tmp = pathlib.Path('/var/tmp')

    if persistent_tmp.exists() and (persistent_tmp.stat().st_mode & (os.W_OK | os.X_OK)):
        logger.debug('Using non-ephemeral storage /var/tmp.')
        root = persistent_tmp
    else:
        logger.debug(f'Using default system storage {tempfile.gettempdir()}.')
        root = pathlib.Path(tempfile.gettempdir())

    src_ = pathlib.Path(src)
    working = root / 'dpsprep' / get_file_hash(src_)
    workdir = WorkingDirectory(
        src=src_,
        dest=pathlib.Path(src_.with_suffix('.pdf').name if dest is None else dest),
        working=working,
    )

    if workdir.working.exists():
        if delete_existing:
            logger.debug(f'Removing existing working directory {working}.')
            destroy_workdir(workdir)
            logger.info(f'Removed existing working directory {working}.')
        else:
            logger.info(f'Reusing working directory {working}.')
    else:
        logger.info(f'Working directory {working} has been created.')

    if not working.exists():
        logger.debug(f'Creating {working}.')
        working.mkdir(parents=True)

    if not workdir.ocrmypdf_tmp_path.exists():
        logger.debug(f'Creating {workdir.ocrmypdf_tmp_path}.')

    return workdir


def destroy_workdir(workdir: WorkingDirectory) -> None:
    shutil.rmtree(workdir.working)
