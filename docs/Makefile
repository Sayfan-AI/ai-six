# Minimal Makefile for Sphinx documentation

SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

.PHONY: help clean html

help:
	@echo "Please use \`make <target>\` where <target> is one of"
	@echo "  html     to make standalone HTML files"

clean:
	rm -rf $(BUILDDIR)/*

html:
	$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
