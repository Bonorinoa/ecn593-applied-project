#!/bin/sh
# build_looks.sh: build both looks of the template and render review shots.
#   main.pdf       the look named in main.tex (kaffeehaus by default)
#   main-mono.pdf  the same source with the mono option forced
# Shots: shots/<look>-p<N>.png at 80 dpi (pages 1-4 and the first appendix page).
# Usage (from thesis/): sh build_looks.sh
set -e
latexmk -interaction=nonstopmode -halt-on-error main.tex
latexmk -interaction=nonstopmode -halt-on-error -jobname=main-mono \
  -usepretex='\PassOptionsToClass{mono}{ecnthesis}' main.tex
mkdir -p shots && rm -f shots/*.png
for job in main main-mono; do
  look=kaffeehaus; [ "$job" = main-mono ] && look=mono
  # first page whose running header says "Appendix" (pdftotext, page by page)
  n=$(pdfinfo "$job.pdf" | awk '/^Pages:/{print $2}')
  app=""
  p=1
  while [ "$p" -le "$n" ]; do
    if pdftotext -f "$p" -l "$p" "$job.pdf" - | grep -q '^Appendix A'; then app=$p; break; fi
    p=$((p+1))
  done
  for q in 1 2 3 4 $app; do
    pdftoppm -r 80 -f "$q" -l "$q" -singlefile -png "$job.pdf" "shots/$look-p$q"
  done
done
for job in main main-mono; do
  printf '%s: Overfull=%s  errors=%s  undefined=%s\n' "$job" \
    "$(grep -c 'Overfull' $job.log || true)" \
    "$(grep -c '^!' $job.log || true)" \
    "$(grep -ci 'undefined' $job.log | tr -d ' ' || true)"
done
