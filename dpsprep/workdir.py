import hashlib
import os
import pathlib
import shutil
import tempfile
from typing import Union

import loguru

HASHING_BUFFER_SIZE = 64 * 1024


# Based on
# https://stackoverflow.com/posts/22058673/revisions
def get_file_hash(path: Union[os.PathLike, str]) -> str:
    h = hashlib.sha1()

    with open(path, 'rb') as file:
        data = file.read(HASHING_BUFFER_SIZE)

        while len(data) > 0:
            h.update(data)
            data = file.read(HASHING_BUFFER_SIZE)

    return h.hexdigest()


class WorkingDirectory:
    src: pathlib.Path
    dest: pathlib.Path
    workdir: pathlib.Path

    def __init__(self, src: Union[os.PathLike, str], dest: Union[os.PathLike, str, None]) -> None:
        self.src = pathlib.Path(src)

        if dest is None:
            self.dest = pathlib.Path(pathlib.Path(src).with_suffix('.pdf').name)
        else:
            self.dest = pathlib.Path(dest)

        # Working path
        # If possible, we avoid the ephemeral storage /tmp
        persistent_tmp = pathlib.Path('/var/tmp')  # noqa: S108

        if persistent_tmp.exists() and (persistent_tmp.stat().st_mode & (os.W_OK | os.X_OK)):
            loguru.logger.debug('Using non-ephemeral storage "/var/tmp".')
            root = persistent_tmp
        else:
            loguru.logger.debug(f'Using default system storage {tempfile.gettempdir()!r}.')
            root = pathlib.Path(tempfile.gettempdir())

        self.workdir = root / 'dpsprep' / get_file_hash(self.src)

    def create_if_necessary(self) -> None:
        if not self.workdir.exists():
            loguru.logger.debug(f'Creating {str(self.workdir)!r}.')
            self.workdir.mkdir(parents=True)

        if not self.ocrmypdf_tmp_path.exists():
            loguru.logger.debug(f'Creating {str(self.ocrmypdf_tmp_path)!r}.')

    def get_page_pdf_path(self, i: int) -> pathlib.Path:
        return self.workdir / f'page_bg_{i + 1}.pdf'

    @property
    def text_layer_pdf_path(self) -> pathlib.Path:
        return self.workdir / 'text_layer.pdf'

    @property
    def ocrmypdf_tmp_path(self) -> pathlib.Path:
        return self.workdir / 'ocrmypdf'

    @property
    def combined_pdf_without_text_path(self) -> pathlib.Path:
        return self.workdir / 'combined_without_text.pdf'

    @property
    def combined_pdf_path(self) -> pathlib.Path:
        return self.workdir / 'combined.pdf'

    @property
    def optimized_pdf_path(self) -> pathlib.Path:
        return self.workdir / 'optimized.pdf'

    def destroy(self) -> None:
        shutil.rmtree(self.workdir)
