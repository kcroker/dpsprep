PDF files full of images cannot be compressed as efficiently as DjVu, sometimes leading to files that are hundreds of megabytes large. Fortunately, books are often [bitonal](https://en.wikipedia.org/wiki/Binary_image), which allows for efficient compression like [group4](https://en.wikipedia.org/wiki/Group_4_compression) or [jbig2](https://en.wikipedia.org/wiki/JBIG2). Unfortunately, in badly digitized books the scanned images may be saved as colorful JPEG files, which can partially be mitigated using `--mode bitonal` (possibly for only a range of pages).

We perform compression in two stages:

* The first one is the default compression provided by [Pillow](https://github.com/python-pillow/Pillow). For bitonal images, [the PDF generation code says](https://github.com/python-pillow/Pillow/blob/a088d54509e42e4eeed37d618b42d775c0d16ef5/src/PIL/PdfImagePlugin.py#L138C16-L138C16) that, if `libtiff` is available, `group4` compression is used.

* If [OCRmyPDF](https://github.com/ocrmypdf/OCRmyPDF) is installed (possibly via the `ocr` or `compress` extras), its PDF optimization can be used via the flags `-O1` to `-O3` (this involves no OCR). This allows us to use advanced techniques, including JBIG2 compression via [`jbig2enc`](https://github.com/agl/jbig2enc).

If manually running OCRmyPDF, note that the optimization command suggested [in the documentation](https://ocrmypdf.readthedocs.io/en/latest/cookbook.html#optimize-images-without-performing-ocr) (setting `--tesseract-timeout` to `0`) may ruin existing text layers. To perform only PDF optimization you can use the following undocumented tool instead:

    python -m ocrmypdf.optimize <input_file> <level> <output_file>
