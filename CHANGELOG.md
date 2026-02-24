## v2.4.2 (2025-02-24)

* Fix issue where only the main process has its logger configured

## v2.4.1 (2025-02-24)

* Fix compatibility issues with the new OCRmyPDF API
* Remove support for Python 3.10

## v2.4.0 (2025-02-24)

* Migrate to `uv` from `pyenv` + `poetry`
* Update dependencies

## v2.3.1 (2025-10-28)

* Fix mixed-up email format

## v2.3.0 (2025-10-28)

* Remove support for Python 3.9
* Migrate to standardized `pyproject.toml`
* Update dependencies

## v2.2.15 (2025-07-02)

* Add support for installation via `pipx`

## v2.2.14 (2025-05-27)

* Improve installation notes
* Bump djvulibre-python version

## v2.2.13 (2025-02-12)

* Fail-safe quality settings for non-JPEG images

## v2.2.12 (2025-01-27)

* Update pytest_image_diff and fix newly broken tests

## v2.2.11 (2025-01-26)

* Update dependencies

## v2.2.10 (2024-10-25)

* Improve interface with OCRmyPDF
* Fix CI build

## v2.2.9 (2024-10-25)

* Improve type hints
* Update dependencies

## v2.2.8 (2024-10-18)

* Support single characters in the text layer

## v2.2.7 (2024-08-27)

* Improve tab and newline handling

## v2.2.6 (2024-08-05)

* Fix accidental whitespace removal from text blocks

## v2.2.5 (2024-07-20)

* Re-add ability to force the image mode (RGB/Grayscale/Monochrome)

## v2.2.4 (2024-02-24)

* Update dependencies

## v2.2.3 (2023-12-09)

* Fix CI build
* Ignore invalid UTF-8 sequences
* Ignore unrecognized page titles in the outline (#23)

## v2.2.2 (2023-10-29)

* Update dependencies

## v2.2.1 (2023-11-06)

* Handle invalid PDF pages
* Fix exception in text layer processing (#20)

## v2.2.0 (2023-10-28)

* Add options for disabling the text layer and for directly running OCR

## v2.1.5 (2023-10-27)

* Fix inverted colors in images (#16)

## v2.1.4 (2023-10-06)

* Fix typo in logging code

## v2.1.3 (2023-10-06)

* Improve logging

## v2.1.2 (2023-10-02)

* Accidental version bump

## v2.1.1 (2023-10-02)

* Remove debug code

## v2.1.0 (2023-10-02)

* Add support for OCRmyPDF

## v2.0.2 (2023-08-03)

* Update some other dependencies
* Replace `python-djvulibre` with `djvulibre-python`

## v2.0.1 (2023-06-22)

* Minor improvements in packaging

## v2.0.0 (2023-05-04)

* Fully rewrite
