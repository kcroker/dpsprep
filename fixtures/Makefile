.PHONY: all clean

all: lipsum.pdf lipsum_01.txt lipsum_01.png lipsum_lines.djvu lipsum_words.djvu lipsum_words_invalid.djvu

clean:
	rm --force *.djvu *.pdf *.png *.txt

%.pdf: %.tex
	pdflatex $*.tex
	rm $*.aux $*.log

%_01.txt: %.pdf
	pdftotext -l 1 -layout $*.pdf $*_01.txt

%_01.png: %.pdf
	gs -sDEVICE=pngmono -r600 -dLastPage=1 -o $*_01.png $*.pdf
	oxipng $*_01.png

%_words.djvu: %.pdf
	djvudigital --dpi=600 --words $*.pdf
	mv $*.djvu $*_words.djvu

%_lines.djvu: %.pdf
	djvudigital --dpi=600 --lines $*.pdf
	mv $*.djvu $*_lines.djvu

%_invalid.djvu: %.djvu
	cp $*.djvu $*_invalid.djvu
	djvused $*_invalid.djvu -e 'output-all' | \
		sed 's/Lorem/\\270/g' | \
		djvused $*_invalid.djvu -f /dev/stdin -s
