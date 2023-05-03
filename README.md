# dpsprep

This tool, initially made specifically for use with Sony's Digital Paper System (DPS), is now a general-purpose DjVu to PDF convertor with a focus on small output size and the ability to preserve bookmarks and text layers (e.g. ones added by OCR).

## Usage

Full example (although you would most likely want the mode to be "bitonal", the default):

    dpsprep --pool=8 --mode=rgb --quality=50 input.djvu output.pdf

Consult the [man file](./dpsprep.1.ronn) for details.

To run the script via the [`poetry`](https://python-poetry.org/) virtual environment, we need:

    poetry run python -m dpsprep input.djvu

## Installation

The easiest way to obtain this package is to clone the repository. The tool depends on several Python libraries, which can easily be installed via `poetry`. There is a hard dependency on `djvulibre` (via `python-djvulibre`) and optional dependencies on `libtiff` and `libjpeg` for good bitonal and multitotal compression, correspondingly.

Once inside the repository, the environment for the program can be set up as follows:

    poetry env use <executable or version>
    poetry install

Now the following should work:

    poetry run python -m dpsprep input.djvu

The program can be installed as a Python module via:

    poetry build
    pip install [--user] dist/*.whl

A convenience script that can be copied or linked to any directory in `$PATH` can be found in `bin/dpsprep`.

See also the [dpsprep-git](https://aur.archlinux.org/packages/dpsprep-git) package for Arch.

Previous versions of the tool itself used to depend on third-party binaries, but this is no longer the case. The test fixtures are checked in, however regenerating them (see `./fixtures/makefile`) requires `pdflatex` (texlive, among others), `gs` (Ghostscript), `pdftotext` (Poppler) and `djvudigital` (GSDjVU). Similarly, the manfile is checked it, but building it from markdown depends on `ronn`.

## Acknowledgements

* The font "invisible1.ttf" is taken from [here](https://www.angelfire.com/pr/pgpf/if.html). It is part of the text layer generation, which itself is based on [hocr-pdf](https://github.com/ocropus/hocr-tools/blob/v1.3.0/hocr-pdf).

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
