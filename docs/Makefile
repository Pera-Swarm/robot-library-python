# Minimal Sphinx Makefile

SPHINXBUILD?=sphinx-build
SOURCEDIR=.
BUILDDIR=_build
PORT?= 9000

.PHONY: help clean html apidoc

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)"

clean:
	rm -rf "$(BUILDDIR)"

apidoc:
	sphinx-apidoc -o docs/api src/robot

html:
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html"

livehtml:
	sphinx-autobuild  --host 0.0.0.0 --port ${PORT} -c . "$(SOURCEDIR)" "$(BUILDDIR)/html"
