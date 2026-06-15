import pathlib
from dataclasses import dataclass


@dataclass(frozen=True)
class WorkingDirectory:
    src: pathlib.Path
    dest: pathlib.Path
    working: pathlib.Path

    def get_page_pdf_path(self, i: int) -> pathlib.Path:
        return self.working / f'page_bg_{i + 1}.pdf'

    @property
    def text_layer_pdf_path(self) -> pathlib.Path:
        return self.working / 'text_layer.pdf'

    @property
    def ocrmypdf_tmp_path(self) -> pathlib.Path:
        return self.working / 'ocrmypdf'

    @property
    def combined_pdf_without_text_path(self) -> pathlib.Path:
        return self.working / 'combined_without_text.pdf'

    @property
    def combined_pdf_path(self) -> pathlib.Path:
        return self.working / 'combined.pdf'

    @property
    def optimized_pdf_path(self) -> pathlib.Path:
        return self.working / 'optimized.pdf'
