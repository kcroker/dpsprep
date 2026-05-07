# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## 2.6.3 - 2026-05-07

* Add an "ocr" extra.
* Set minimal worker pool size to 1

## 2.6.2 - 2026-05-06

* Repackage submodule as a Python package to avoid build complications.

## 2.6.1 - 2026-05-06

* Determine versions and dates without git (for building the docs).

## 2.6.0 - 2026-05-06

### Additions

* Implement page ranges for `--mode`, `--dpi` and `--quality`.
* Add a `--socr` ("streamlined" OCR) option that abbreviates `--ocr '{"language": ["eng", "grc"]}'` to `--ocrs eng,grc`.
* Add a `-f` short variant for `--overwrite`.

### Changes

* Deprecate the short overwrite flag `-o` in favor of `-f`.
* Warnings and errors are not logger to stderr.
* Restructure the code into smaller chunks.
* General maintenance work.

## 2.5.4 - 2026-04-24

* Run `uv` security audit and update some dependencies.

## 2.5.3 - 2026-03-25

* Fix broken workflow without text layer translation.
* Shorter names for temporary directories.
* Code maintenance.

## 2.5.2 - 2026-03-25

* Relax dependency versions.

## 2.5.1 - 2026-03-14

* Allow manually configuring PDF page resolution (DPI).

## 2.5.0 - 2026-03-13

* Account for DjVu file resolution.
* Simplify image diffing and regenerate better-quality fixtures.

## 2.4.2 - 2026-02-24

* Fix issue where only the main process has its logger configured.

## 2.4.1 - 2026-02-24

* Fix compatibility issues with the new OCRmyPDF API.
* Remove support for Python 3.10.

## 2.4.0 - 2026-02-24

* Migrate to `uv` from `pyenv` + `poetry`.
* Update dependencies.

## 2.3.1 - 2025-10-28

* Fix mixed-up email format.

## 2.3.0 - 2025-10-28

* Remove support for Python 3.9.
* Migrate to standardized `pyproject.toml`.
* Update dependencies.

## 2.2.15 - 2025-07-02

* Add support for installation via `pipx`.

## 2.2.14 - 2025-05-27

* Improve installation notes.
* Bump djvulibre-python version.

## 2.2.13 - 2025-02-12

* Fail-safe quality settings for non-JPEG images.

## 2.2.12 - 2025-01-27

* Update pytest_image_diff and fix newly broken tests.

## 2.2.11 - 2025-01-26

* Update dependencies.

## 2.2.10 - 2024-10-25

* Improve interface with OCRmyPDF.
* Fix CI build.

## 2.2.9 - 2024-10-25

* Improve type hints.
* Update dependencies.

## 2.2.8 - 2024-10-18

* Support single characters in the text layer.

## 2.2.7 - 2024-08-27

* Improve tab and newline handling.

## 2.2.6 - 2024-08-05

* Fix accidental whitespace removal from text blocks.

## 2.2.5 - 2024-07-20

* Re-add ability to force the image mode (RGB/Grayscale/Monochrome).

## 2.2.4 - 2024-02-24

* Update dependencies.

## 2.2.3 - 2023-12-09

* Fix CI build.
* Ignore invalid UTF-8 sequences.
* Ignore unrecognized page titles in the outline (#23).

## 2.2.2 - 2023-10-29

* Update dependencies.

## 2.2.1 - 2023-11-06

* Handle invalid PDF pages.
* Fix exception in text layer processing (#20).

## 2.2.0 - 2023-10-28

* Add options for disabling the text layer and for directly running OCR.

## 2.1.5 - 2023-10-27

* Fix inverted colors in images (#16).

## 2.1.4 - 2023-10-06

* Fix typo in logging code.

## 2.1.3 - 2023-10-06

* Improve logging.

## 2.1.2 - 2023-10-02

* Accidental version bump.

## 2.1.1 - 2023-10-02

* Remove debug code.

## 2.1.0 - 2023-10-02

* Add support for OCRmyPDF.

## 2.0.2 - 2023-08-03

* Update some other dependencies.
* Replace `python-djvulibre` with `djvulibre-python`.

## 2.0.1 - 2023-06-22

* Minor improvements in packaging.

## 2.0.0 - 2023-05-04

* Fully rewrite.
