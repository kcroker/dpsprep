from pathlib import Path
from typing import Union
import hashlib
import os
import shutil
import tempfile

from loguru import logger


HASHING_BUFFER_SIZE = 64 * 1024


# Based on
# https://stackoverflow.com/posts/22058673/revisions
def get_file_hash(path: Union[os.PathLike, str]):
    h = hashlib.sha1()

    with open(path, 'rb') as file:
        data = file.read(HASHING_BUFFER_SIZE)

        while len(data) > 0:
            h.update(data)
            data = file.read(HASHING_BUFFER_SIZE)

    return h.hexdigest()


class WorkingDirectory:
    src: Path
    dest: Path
    workdir: Path

    def __init__(self, src: Union[os.PathLike, str], dest: Union[os.PathLike, str, None]):
        self.src = Path(src)

        if dest is None:
            self.dest = Path(Path(src).with_suffix('.pdf').name)
        else:
            self.dest = Path(dest)

        # Working path
        # If possible, we avoid the ephemeral storage /tmp
        persistent_tmp = Path('/var/tmp')

        if persistent_tmp.exists() and (persistent_tmp.stat().st_mode & (os.W_OK | os.X_OK)):
            logger.debug('Using non-ephemeral storage "/var/tmp".')
            root = persistent_tmp
        else:
            logger.debug(f'Using default system storage {repr(tempfile.gettempdir())}.')
            root = Path(tempfile.gettempdir())

        self.workdir = root / 'dpsprep' / get_file_hash(self.src)

    def create_if_necessary(self):
        if not self.workdir.exists():
            logger.debug(f'Creating {repr(str(self.workdir))}.')
            self.workdir.mkdir(parents=True)

        if not self.ocrmypdf_tmp_path.exists():
            logger.debug(f'Creating {repr(str(self.ocrmypdf_tmp_path))}.')

    def get_page_pdf_path(self, i: int):
        return self.workdir / f'page_bg_{i + 1}.pdf'

    @property
    def text_layer_pdf_path(self):
        return self.workdir / 'text_layer.pdf'

    @property
    def ocrmypdf_tmp_path(self):
        return self.workdir / 'ocrmypdf'

    @property
    def combined_pdf_without_text_path(self):
        return self.workdir / 'combined_without_text.pdf'

    @property
    def combined_pdf_path(self):
        return self.workdir / 'combined.pdf'

    @property
    def optimized_pdf_path(self):
        return self.workdir / 'optimized.pdf'

    def destroy(self):
        shutil.rmtree(self.workdir)
