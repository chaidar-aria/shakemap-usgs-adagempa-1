# Minimal Sphinx Makefile — delegates to sphinx-build.
SPHINXOPTS  ?=
SPHINXBUILD ?= sphinx-build
SOURCEDIR   = .
BUILDDIR    = _build

.PHONY: help html clean Makefile

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

html:
	$(SPHINXBUILD) -b html "$(SOURCEDIR)" "$(BUILDDIR)/html" $(SPHINXOPTS) $(O)
	@echo "Build finished. HTML is in $(BUILDDIR)/html."

clean:
	rm -fr $(BUILDDIR)

# Catch-all: pass any other target through to sphinx-build -M
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
