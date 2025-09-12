# Minimal Sphinx Makefile

SPHINXBUILD?=sphinx-build
SOURCEDIR=.
BUILDDIR=_build
ROOTDIR=..
PY?=python
PORT?= 9000

.PHONY: help clean html apidoc

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)"

clean:
	rm -rf "$(BUILDDIR)"

apidoc:
	@if command -v sphinx-apidoc >/dev/null 2>&1; then \
		sphinx-apidoc -o api $(ROOTDIR)/src/robot; \
	else \
		$(PY) -m sphinx.ext.apidoc -o api $(ROOTDIR)/src/robot; \
	fi

html:
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html"

livehtml:
	sphinx-autobuild  --host 0.0.0.0 --port ${PORT} -c . "$(SOURCEDIR)" "$(BUILDDIR)/html"
