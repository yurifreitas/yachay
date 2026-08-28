# The manuscript build. One entry point, four targets.
#
#   make          draft PDF (line numbers, todo notes, [P] marks visible)
#   make final    submission PDF (draft apparatus off)
#   make check    fail if any number in the manuscript is stale, or any
#                 reference is still unverified. Run before submitting.
#   make clean    remove build artefacts
#
# Engine: LuaLaTeX + biber, driven by latexmk. Not installed on this machine as of
# 2026-08-26 -- see README.md for the container fallback.

MAIN     := main
PYTHON   := python
ROOT     := ..
BUILDDIR := build
LATEXMK  := latexmk -lualatex -shell-escape -interaction=nonstopmode -halt-on-error \
            -outdir=$(BUILDDIR)

GENERATED := generated/numbers.tex

.PHONY: all final check numbers clean watch verify-refs

all: numbers
	$(LATEXMK) $(MAIN).tex

# Submission build: strip the draft option, then insist on the checks.
final: check
	sed 's/\\usepackage\[draft\]{sieve}/\\usepackage{sieve}/' $(MAIN).tex > $(BUILDDIR)/$(MAIN)-final.tex
	cp -r sections generated refs.bib sieve.sty figures $(BUILDDIR)/ 2>/dev/null || true
	cd $(BUILDDIR) && latexmk -lualatex -shell-escape -interaction=nonstopmode \
	    -halt-on-error $(MAIN)-final.tex

numbers:
	$(PYTHON) $(ROOT)/tools/paper_numbers.py

# Stage 8, enforced. A manuscript that fails this is not submitted.
check: verify-refs
	$(PYTHON) $(ROOT)/tools/paper_numbers.py --check

# Every reference must be metadata-checked against its source before submission.
verify-refs:
	@if grep -v '^\s*%' refs.bib | grep -q 'verified *= *{no}'; then \
	  echo "FAIL: refs.bib still has unverified entries:"; \
	  grep -v '^\s*%' refs.bib | grep -B12 'verified *= *{no}' | grep -E '^@' | sed 's/^/  /'; \
	  echo "Check year, venue, authors and DOI against the source, then mark verified."; \
	  exit 1; \
	fi
	@echo "all references verified"

watch: numbers
	$(LATEXMK) -pvc $(MAIN).tex

clean:
	latexmk -C -outdir=$(BUILDDIR) $(MAIN).tex 2>/dev/null || true
	rm -rf $(BUILDDIR)
