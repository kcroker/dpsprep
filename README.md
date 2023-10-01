# dpsprep

This tool, initially made specifically for use with Sony's Digital Paper System (DPS), is now a general-purpose DjVu to PDF converter with a focus on small output size and the ability to preserve document outlines (e.g. TOC) and text layers (e.g. OCR).

## Usage

Full example:

    dpsprep --pool=8 --quality=50 input.djvu output.pdf

Consult the [man file](./dpsprep.1.ronn) for details.

See the next section for different ways to run the program.

## Installation

The easiest way to obtain `dpsprep` is to clone the repository.

The tool depends on several Python libraries, which can easily be installed via `poetry`. A configuration for `pyenv` is also included.

The only hard prerequisite is `djvulibre`. Optional prerequisites are `libtiff` and `libjpeg` (or `libjpeg-turbo`), which are used for good bitonal and multitotal (RGB or grayscale) compression, correspondingly. The former depends on the latter, so installing `libtiff` will likely install both. For details on how they can be installed, see the GitHub Actions [workflow](./.github/workflows/test.yml) and the [dpsprep-git](https://aur.archlinux.org/packages/dpsprep-git) package for Arch Linux.

Note that Windows support in `python-djvulibre` requires 64-bit `djvulibre`, and they only officially distribute 32-bit Windows packages. If you manage to make it work, consider opening a pull request.

Once inside the cloned repository, the environment for the program can be set up by simply running `poetry install`. After than, the following should work:

    poetry run python -m dpsprep input.djvu

The program can easily be installed as a Python module via `poetry` and `pip`:

    poetry build
    pip install [--user] dist/*.whl

If you are packaging this for some other package manager, consider using PEP-517 tools as shown in [this PKGBUILD file](https://aur.archlinux.org/cgit/aur.git/tree/PKGBUILD?h=dpsprep-git).

A convenience script that can be copied or linked to any directory in `$PATH` can be found at [`./bin/dpsprep`](./bin/dpsprep).

Previous versions of the tool itself used to depend on third-party binaries, but this is no longer the case. The test fixtures are checked in, however regenerating them (see [`./fixtures/makefile`](./fixtures/makefile)) requires `pdflatex` (texlive, among others), `gs` (Ghostscript), `pdftotext` (Poppler) and `djvudigital` (GSDjVU). Similarly, the man file is checked in, but building it from markdown depends on `ronn`.

## Note regarding compression

We use the default compression provided by [Pillow](https://github.com/python-pillow/Pillow). For bitonal images, [the PDF generation code says](https://github.com/python-pillow/Pillow/blob/a088d54509e42e4eeed37d618b42d775c0d16ef5/src/PIL/PdfImagePlugin.py#L138C16-L138C16) that, if `libtiff` is available, `group4` compression is used.

The size of the PDF files can sometimes later be additionally reduced. OCRmyPDF is an actively maintained project (as of late 2023) that also supports standalone PDF optimization, including JBIG2 compression via `jbig2enc`. Its compression level ranges from 1 to 3; details can be found [in the project's documentation](https://ocrmypdf.readthedocs.io/en/latest/optimizer.html)).

Please note that the compression method suggested [in the documentation](https://ocrmypdf.readthedocs.io/en/latest/cookbook.html#optimize-images-without-performing-ocr) (setting `--tesseract-timeout` to `0`) may ruin existing text layers. To perform only PDF optimization you can use the following undocumented tool instead:

    python -m ocrmypdf.optimize <input_file> <level> <output_file>

## Acknowledgements

* The font [`invisible1.ttf`](./dpsprep/invisible.ttf) is taken from [here](https://www.angelfire.com/pr/pgpf/if.html). See the `djvu_pages_to_text_fpdf` function in [`./dpsprep/text.py`](./dpsprep/text.py) for how it is used.

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
