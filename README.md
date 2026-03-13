# dpsprep

[![Tests](https://github.com/kcroker/dpsprep/actions/workflows/test.yml/badge.svg)](https://github.com/kcroker/dpsprep/actions/workflows/test.yml) [![AUR Package](https://img.shields.io/aur/version/dpsprep)](https://aur.archlinux.org/packages/dpsprep)

This tool, initially made specifically for use with Sony's Digital Paper System (DPS), is now a general-purpose DjVu to PDF converter with a focus on small output size and the ability to preserve document outlines (e.g. TOC) and text layers (e.g. OCR).

## Usage

Full example (the name of the PDF is optional and inferred from the input name):

    dpsprep --pool=8 --quality=50 input.djvu output.pdf

If you have [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) installed, you can use its PDF optimizer:

    dpsprep -O3 input.djvu

You can also skip translating the text layer (it is sometimes not translated well) and redo the OCR (rather than launching the `ocrmypdf` CLI, we use the API directly and accept options in JSON format):

    dpsprep --ocr '{"language": ["rus", "eng"]}' input.djvu

Consult the man file ([online](./dpsprep.1.ronn)) for details; there are a lot of options to consider.

See the next section for different ways to run the program.

## Installation

### Automated

An easy way to install a `dpsprep` executable for the current user is via [`uv`](https://docs.astral.sh/uv/):

    uv tool install dpsprep --from git+https://github.com/kcroker/dpsprep

For better compression (see below), the `compress` extra must be specified:

    uv tool install dpsprep --from git+https://github.com/kcroker/dpsprep[compress]

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

For details on how these dependencies can be installed, see the GitHub Actions [workflow](./.github/workflows/test.yml) and the [dpsprep](https://aur.archlinux.org/packages/dpsprep) package for Arch Linux.

### Manual

Setting up the project in is again done via `uv`. Once inside the cloned repository, the environment for the program can be set up by simply running `uv sync --all-extras`. After than, the following should work:

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
> Previous versions of the tool itself used to depend on third-party binaries, but this is no longer the case. The test fixtures are checked in, however regenerating them (see [`./fixtures/Makefile`](./fixtures/Makefile)) requires `pdflatex` (texlive, among others), `gs` (Ghostscript), `oxipng` (oxipng), `pdftotext` (Poppler), `djvudigital` (GSDjVU) and `djvused` (DjVuLibre). Similarly, the man file is checked in, but building it from markdown depends on `ronn`.

## Details

### Compression

We perform compression in two stages:

* The first one is the default compression provided by [Pillow](https://github.com/python-pillow/Pillow). For bitonal images, [the PDF generation code says](https://github.com/python-pillow/Pillow/blob/a088d54509e42e4eeed37d618b42d775c0d16ef5/src/PIL/PdfImagePlugin.py#L138C16-L138C16) that, if `libtiff` is available, `group4` compression is used.

* If [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) is installed, its PDF optimization can be used via the flags `-O1` to `-O3` (this involves no OCR). This allows us to use advanced techniques, including JBIG2 compression via `jbig2enc`.

If manually running OCRmyPDF, note that the optimization command suggested [in the documentation](https://ocrmypdf.readthedocs.io/en/latest/cookbook.html#optimize-images-without-performing-ocr) (setting `--tesseract-timeout` to `0`) may ruin existing text layers. To perform only PDF optimization you can use the following undocumented tool instead:

    python -m ocrmypdf.optimize <input_file> <level> <output_file>

### Text layer

The visible contents of a DjVu file are well-compressed images (see [here](http://yann.lecun.com/ex/djvu/index.html)). But a DjVu file also contains a "text layer" stored as metadata attached to invisible rectangular blocks. PDF does not support such constructs, so we do a little hack.

We render each page as an image and put it as a background in the PDF. We then use a font, [`invisible1.ttf`](./dpsprep/invisible.ttf), taken from [here](https://www.angelfire.com/pr/pgpf/if.html), to "draw" text. Every time we draw a block of text, we rescale the font so that the width of the text matches that of the corresponding DjVu block.

The following screenshot displays the result of converting a DjVu document:

![Image](./screenshots/lipsum_with_image.png)

The following screenshot displays the same document without the background image and with the invisible font replaced by Times New Roman:

![Image](./screenshots/lipsum_with_text.png)

Since the image is actually drawn on top of the text, there is no harm in using an actual visible font, possibly rendered using a transparent "color". Still, when searching and selecting text, the scrambled letters from the second image would be highlighted. With the invisible font, there are no visible glyphs to highlight, so an illusory "block" containing the text is highlighted instead.

See [`./dpsprep/text.py`](./dpsprep/text.py) for the implementation.

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
