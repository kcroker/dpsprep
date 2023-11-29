.PHONY: all

all: lipsum_01.txt lipsum_01.png lipsum_lines.djvu lipsum_words.djvu

%.pdf: %.tex
	pdflatex $*.tex
	rm $*.aux $*.log

%_01.txt: %.pdf
	pdftotext -l 1 -layout $*.pdf $*_01.txt

%_01.png: %.pdf
	gs -sDEVICE=png16m -r300 -dLastPage=1 -o $*_01.png $*.pdf

%_words.djvu: %.pdf
	djvudigital --words $*.pdf
	mv $*.djvu $*_words.djvu

%_lines.djvu: %.pdf
	djvudigital --lines $*.pdf
	mv $*.djvu $*_lines.djvu

%_invalid.djvu: %.djvu
	cp $*.djvu $*_invalid.djvu
	djvused $*_invalid.djvu -e 'output-all' | \
		sed "s/Lorem/\\270/g" | \
		djvused $*_invalid.djvu -f /dev/stdin -s
