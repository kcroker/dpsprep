# dpsprep

[![Tests](https://github.com/kcroker/dpsprep/actions/workflows/test.yml/badge.svg)](https://github.com/kcroker/dpsprep/actions/workflows/test.yml) [![AUR Package](https://img.shields.io/aur/version/dpsprep)](https://aur.archlinux.org/packages/dpsprep)

Convert DjVu files to PDF.

The name comes from Sony's Digital Paper System (DPS), for which the tool was initially developed - see [below](#kevins-notes-regarding-the-first-version).

## Table of contents

* [Usage](#usage)
* [Installation](#installation)
* [Project setup](#project-setup)

Also see [the wiki](https://github.com/kcroker/dpsprep/wiki).

## Usage

Full example (the name of the PDF is optional and inferred from the input name):

    dpsprep --pool=8 --quality=50 input.djvu output.pdf

If you have [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) installed, you can use its PDF optimizer:

    dpsprep -O3 input.djvu

You can also skip translating the text layer (it is sometimes not being translated well) and redo the OCR:

    dpsprep --socr rus,eng,grc input.djvu

Rather than launching the `ocrmypdf` CLI, we use the API directly. The option `--socr` ("streamlined" OCR) used above is a shorthand for the following:

    dpsprep --ocr '{"language": ["rus", "eng", "grc"]}' input.djvu

Sometimes the pages of scanned books are saved as colorful images. For PDF, saving bitonal page backgrounds as RGB images can inflate the file by an order of magnitude (see the [notes on compression](https://github.com/kcroker/dpsprep/wiki/compression) in the wiki). We try to infer the color mode of each page, however that is sometimes inefficient. In such cases, we can force the color mode as follows:

    dpsprep --mode bitonal input.djvu start.pdf

In case we want to preserve the cover page as-is, we can use ranges:

    dpsprep --mode bitonal[2-end] input.djvu start.pdf

For details on these and other options, as well as the allowed range syntax, consult the man file ([online](https://github.com/kcroker/dpsprep/wiki/dpsprep.1)).

## Installation

### Automatic

An easy way to install a `dpsprep` executable for the current user is via [`uv`](https://docs.astral.sh/uv/):

    uv tool install dpsprep --from git+https://github.com/kcroker/dpsprep

or [`pipx`](https://pipx.pypa.io):

    pipx install git+https://github.com/kcroker/dpsprep

As described in the [notes on compression](https://github.com/kcroker/dpsprep/wiki/compression) in the wiki, you might want to also include the `compress` extra:

    uv tool install dpsprep --from git+https://github.com/kcroker/dpsprep[compress]

Similarly, for OCR, the `ocr` extra must be used (coincidentally, both pull in the same package - OCRmyPDF).

Sometimes a particular feature branch need to be tested. For installing a fixed revision (i.e. common/branch/tag), the following should work (if `extra-name` is needed, use `dpsprep@rev[extra-name]`):

    uv tool install dpsprep --from git+https://github.com/kcroker/dpsprep@rev

The only hard prerequisite is `djvulibre` (e.g. `djvulibre` on Arch, `libdjvulibre-dev` on Ubuntu, etc.). We use the Python bindings from the package [`djvulibre-python`](https://github.com/FriedrichFroebel/python-djvulibre) (not to be confused with the unmaintained [`python-djvulibre`](https://github.com/jwilk-archive/python-djvulibre); see [this pull request](https://github.com/kcroker/dpsprep/pull/10)).

> [!TIP]
> A few people have reported installation problems; see [this possible solution](https://github.com/kcroker/dpsprep/issues/38) and [this sample Dockerfile](https://github.com/kcroker/dpsprep/pull/37).

> [!NOTE]
> Note that Windows support in `djvulibre-python` requires 64-bit `djvulibre`, and they only officially distribute 32-bit Windows packages. If you manage to make it work, consider opening a pull request.

Optional prerequisites are:

* `libtiff` for bitonal image compression.
* `libjpeg` (or `libjpeg-turbo`) for multitotal (RGB or grayscale) compression.
* `OCRmyPDF` and `jbig2enc` for PDF optimization (see the next section).

`libtiff` depends on `libjpeg`, so installing `libtiff` will likely install both.

For details on how these dependencies can be installed, see the GitHub Actions [test workflow](./.github/workflows/test.yml) and the [dpsprep](https://aur.archlinux.org/packages/dpsprep) package for Arch Linux.

### Manual

Setting up the project in is again done via `uv`. Once inside the cloned repository, the environment for the program can be set up by simply running `uv sync`. After than, the following should work:

    uv run dpsprep [OPTIONS] SRC [DEST]

> [!NOTE]
> Previous versions used [`pyenv`](https://github.com/pyenv/pyenv) for managing Python versions and [`poetry`](https://python-poetry.org/) for managing dependencies and building. Since then the project migrated to `uv`, which subsumes both and provides other niceties.

You can also build and install the project, for example via [`pipx`](https://pipx.pypa.io/en/stable/):

    uv build --wheel
    pipx install --include-deps dist/*.whl

> [!TIP]
> The build can fail if the [`uv_build`](https://docs.astral.sh/uv/concepts/build-backend/) Python package is not installed. Make sure not only the `uv` binary, but also the corresponding Python package is available. For example, in the Arch repositories, these are distinct packages, `uv` and `python-uv`. Alternatively, try to install the [`uv-build`](https://pypi.org/project/uv-build/) PyPI package (`python-uv-build` in Arch) explicitly in this case.

If you want `dpsprep` to be able to use `ocrmypdf` from `pipx`'s isolated environment, you must [inject](https://fig.io/manual/pipx/inject) it explicitly via

    pipx inject dpsprep ocrmypdf

> [!TIP]
> If you are packaging this for some other package manager, consider using PEP-517 tools as shown in [this PKGBUILD file](https://aur.archlinux.org/cgit/aur.git/tree/PKGBUILD?h=dpsprep).

> [!NOTE]
> Previous versions of the tool itself used to depend on third-party binaries, but this is no longer the case. The test fixtures are checked in, however regenerating them (see [`./fixtures/Makefile`](./fixtures/Makefile)) requires `pdflatex` (texlive, among others), `gs` (Ghostscript), `oxipng` (oxipng), `pdftotext` (Poppler), `djvudigital` (GSDjVU) and `djvused` (DjVuLibre).

## Project setup

The project uses `uv` for managing Python versions, dependencies and builds. Running `uv sync` will create a virtual environment with an appropriate Python version (based on [.python-version](./.python-version)) and install all development dependencies.

Other tasks like linting, type checking and building the documentation are described in [`poe.toml`](./poe.toml) (configuration for [poethepoet](https://pypi.org/project/poethepoet/)).

Run [`tox`](https://tox.wiki/) (via e.g. `uv run tox` or `poe run test-multienv`) to test the project in all supported environments.

If you plan to submit any work, consider also updating [`CHANGELOG.md`](./CHANGELOG.md).

## Kevin's notes regarding the first version

I wrote this with the specific intent of converting ebooks in the DJVU format into PDFs for use with the fantastic (but pricey) 
Sony Digital Paper System.

DjVu technology is strikingly superior for many ebook applications, yet the Sony Digital Paper System (rev 1.3 US)
only supports PDF technology: this is because its primary design purpose is not as an ereader.  The device, however, 
is quite nearly the **perfect** ereader.

Unfortunately, all presently available DjVu to PDF tools seem to just dump flattened enormous TIFF images.  This is ridiculous.
Since PDF really can't do that much better on the way it stores image data, a 5-6x bloat cannot be avoided.  However, none of the 
existing tools preserve:

* The OCR'd text content
* Table of Contents or Internal links

This is kind of silly, but until Sony's Digital Paper, there was no need to move functional DjVu files to PDFs.
In order to make workable PDFs from DjVu files for use on the Digital Paper System, I have implemented in one location the following
procedures detailed here:

By automating the procedure of user zetah for extracting the text and getting it in the correct locations:
http://askubuntu.com/questions/46233/converting-djvu-to-pdf (OCR text transfer)

By implementing the procedure of user pyrocrasty for extracting the outline, and putting it into the PDF generated above:
http://superuser.com/questions/801893/converting-djvu-to-pdf-and-preserving-table-of-contents-how-is-it-possible (bookmark transfer)

## Using Docker

Build the Docker image:

```bash
docker build -t dpsprep .
```

Run the container with a volume mount to process files:

```bash
docker run --rm -u $(id -u):$(id -g) -v $(pwd):/files dpsprep input.djvu output.pdf
```

To use specific options:

```bash
docker run --rm -u $(id -u):$(id -g) -v $(pwd):/files dpsprep --pool=8 --quality=50 input.djvu output.pdf
```

### Add as alias

Put the following line into `~/.bashrc` or `~/.zshrc`:

```bash
alias dpsprep='docker run --rm -u $(id -u):$(id -g) -v $(pwd):/files dpsprep'
```

This will allow you to run the command as `dpsprep` without needing to specify the Docker command each time.
