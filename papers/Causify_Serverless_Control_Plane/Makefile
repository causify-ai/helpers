LATEX ?= pdflatex
BIBTEX ?= $(shell command -v bibtex >/dev/null 2>&1 && echo bibtex || echo bibtex.original)
TARGET = paper
PDF = $(TARGET).pdf
COMPAT = Causify_Serverless_Control_Plane.pdf
IEEE_DIR = submissions/ieee_cloud_computing
IEEE_COMPAT = Causify_Serverless_Control_Plane_IEEE_Cloud_Computing.pdf

all: full ieee check

full:
	rm -f $(PDF) $(COMPAT)
	$(LATEX) -interaction=nonstopmode -halt-on-error $(TARGET).tex
	$(BIBTEX) $(TARGET)
	$(LATEX) -interaction=nonstopmode -halt-on-error $(TARGET).tex
	$(LATEX) -interaction=nonstopmode -halt-on-error $(TARGET).tex
	cp $(PDF) $(COMPAT)

ieee:
	cd $(IEEE_DIR) && rm -f $(PDF) $(IEEE_COMPAT)
	cd $(IEEE_DIR) && $(LATEX) -interaction=nonstopmode -halt-on-error $(TARGET).tex
	cd $(IEEE_DIR) && $(BIBTEX) $(TARGET)
	cd $(IEEE_DIR) && $(LATEX) -interaction=nonstopmode -halt-on-error $(TARGET).tex
	cd $(IEEE_DIR) && $(LATEX) -interaction=nonstopmode -halt-on-error $(TARGET).tex
	cp $(IEEE_DIR)/$(PDF) $(IEEE_DIR)/$(IEEE_COMPAT)

check:
	@pdftotext $(PDF) - | (! grep -E "\?\?|\[\?|undefined citations|Citation.*undefined|There were undefined|LaTeX Warning" )
	@pdftotext $(IEEE_DIR)/$(PDF) - | (! grep -E "\?\?|\[\?|undefined citations|Citation.*undefined|There were undefined|LaTeX Warning" )
	@test -s $(COMPAT)
	@test -s $(IEEE_DIR)/$(IEEE_COMPAT)

clean:
	rm -f *.aux *.bbl *.blg *.log *.out *.toc *.lof *.lot *.fls *.fdb_latexmk *.synctex.gz
	rm -f $(IEEE_DIR)/*.aux $(IEEE_DIR)/*.bbl $(IEEE_DIR)/*.blg $(IEEE_DIR)/*.log $(IEEE_DIR)/*.out $(IEEE_DIR)/*.toc $(IEEE_DIR)/*.lof $(IEEE_DIR)/*.lot $(IEEE_DIR)/*.fls $(IEEE_DIR)/*.fdb_latexmk $(IEEE_DIR)/*.synctex.gz

distclean: clean
	rm -f $(PDF) $(COMPAT) $(IEEE_DIR)/$(PDF) $(IEEE_DIR)/$(IEEE_COMPAT)

.PHONY: all full ieee check clean distclean
