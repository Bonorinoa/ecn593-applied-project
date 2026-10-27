# V2 (verifier, cross-family): check the v2 paper and close the sprint

You are an independent verifier. The producer was the writer (Claude). Report:
`/Users/bonorinoa/Hermes/Projects/ecn593/reviews/v2-paper.md`. The first line is the verdict
(CLOSE / CLOSE-WITH-WORDING / BLOCK). Append after each item.

**Root:** the W1 commits (shas in W1's handoff). Design: `docs/preregistration-v2.md`. Code review:
`reviews/v2-code.md`.

**Check:**
1. **Every result statement** in `writeup/main.tex` and `cover.tex` against `results/*.json` through
   `numbers.tex`. No typed result number (list any). The macros regenerate identically
   (`write_numbers.table()` in memory; do not write).
2. **The evaluation section.** Do the two analysts and the two layers match the code's fields and
   the pre-registration? Are any claims overstated, especially "honest", "overconfident" and
   "coverage"? Is the containment of one panel kept apart from repeated-sampling coverage?
3. **Model-properties claims.**
   - Check the contraction bound by hand: the logistic slope is at most 1/4, W is row-stochastic,
     and the box gives beta + gamma <= 1.4.
   - Check numerically that two different Y(0) draws with the same shocks give Y_T within 1e-6 at
     two box corners.
   - Compute the global clustering of the world graph in your own code.
4. **Citations.** Each new reference exists with the stated authors, year and journal (DOI resolves).
   List each `[CITE?]`.
5. **World Bank is gone** from the paper and the docs. The tag `v1-worldbank-moments` is
   mentioned once as the archive.
6. **Integrity.**
   - pytest passes;
   - the PDF builds in a scratch copy and is byte-identical to the committed `writeup/main.pdf`;
   - a fresh `git clone` of the repo into scratch, plus the README setup (uv venv in scratch)
     and `scripts/replicate.py`, prints REPLICATED. Run it in background mode and poll; it
     takes about 8–13 min.
7. **Premise check.**

**Fence:**
- Read-only in the repo.
- Scratch: `reviews/probes/V2/` in the spine.
- No foreground command over about 3 minutes.
