import hashlib
import logging
import os
import pathlib
import shutil
import tempfile

from dpsprep.workdir import WorkingDirectory


PERSISTENT_TMP = pathlib.Path('/var/tmp')  # See the initialize_workdir documentation below.
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
    tmp_root: os.PathLike | str | None,
    delete_existing: bool = False,
) -> WorkingDirectory:
    """Create a working directory and initialize a WorkingDirectory structure.

    Cross-platform temporary directories are difficult to handle. The standard library's documentation
    for tempfile.gettempdir() lists a procedure for determining which directory to use.

    On Linux distributions, the usual /tmp is severely restricted both in capacity and persistence
    because it is usually stored in RAM. Both of these are solved by /var/tmp (see [1]).

    We can largely avoid caring about the persistence issue, however some DjVu documents can produce
    gigabytes of PDF files. So, on Linux, we use /var/tmp whenever possible. The specific access check
    we use was suggested in [2]. In case it fails, perhaps we should try creating dummy files where
    our intermediate results will be stored.

    Finally, we allow explicit overrides via the tmp_root variable. We assume the it is writable.
    Click checks this for us explicitly in the CLI.

    [1] https://www.pathname.com/fhs/pub/fhs-2.3.html#VARTMPTEMPORARYFILESPRESERVEDBETWEE
    [2] https://github.com/kcroker/dpsprep/issues/59
    """
    if tmp_root:
        logger.debug(f'Using custom temporary directory {tmp_root}.')
    elif os.name == 'posix' and os.access(PERSISTENT_TMP, os.W_OK | os.X_OK):
        tmp_root = PERSISTENT_TMP
        logger.debug('Using non-ephemeral storage {PERSISTENT_TMP}.')
    else:
        tmp_root = tempfile.gettempdir()
        logger.debug(f'Using default system storage {tmp_root}.')

    src_ = pathlib.Path(src)
    working = pathlib.Path(tmp_root) / 'dpsprep' / get_file_hash(src_)
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
