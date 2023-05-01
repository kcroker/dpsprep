%.pdf: %.tex
	pdflatex $*.tex
	rm $*.aux $*.log

%_01.png: %.pdf
	gs -sDEVICE=png16m -r300 -dLastPage=1 -o $*_01.png $*.pdf

%_words.djvu: %.pdf
	djvudigital --words $*.pdf
	mv $*.djvu $*_words.djvu

%_lines.djvu: %.pdf
	djvudigital --lines $*.pdf
	mv $*.djvu $*_lines.djvu
