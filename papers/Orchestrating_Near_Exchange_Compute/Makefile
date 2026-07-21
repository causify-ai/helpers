LATEX ?= pdflatex
BIBTEX ?= $(shell command -v bibtex >/dev/null 2>&1 && echo bibtex || echo bibtex.original)
TARGET = paper
PDF = $(TARGET).pdf
COMPAT = Orchestrating_Near_Exchange_Compute.pdf

all: full check

full:
	rm -f $(PDF) $(COMPAT)
	$(LATEX) -interaction=nonstopmode -halt-on-error $(TARGET).tex
	$(BIBTEX) $(TARGET)
	$(LATEX) -interaction=nonstopmode -halt-on-error $(TARGET).tex
	$(LATEX) -interaction=nonstopmode -halt-on-error $(TARGET).tex
	cp $(PDF) $(COMPAT)

check:
	@pdftotext $(PDF) - | (! grep -E "\?\?|\[\?|undefined citations|Citation.*undefined|There were undefined|LaTeX Warning" )
	@test -s $(COMPAT)

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot *.fls *.fdb_latexmk *.synctex.gz

distclean: clean
	rm -f $(PDF) $(COMPAT)

.PHONY: all full check clean distclean
