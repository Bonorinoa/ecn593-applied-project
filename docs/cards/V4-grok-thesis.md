# V4 (verifier, Grok 4.7, read-only): the paper

Producer: W3 (writer, Claude). You are an independent family. Read `docs/cards/common_rules.md`
(below), the W3 card `docs/cards/W3-writer-thesis.md`, its handoff (`docs/cards/progress/W3.md`)
and `reviews/a2-code.md`.

**Write one file:** `reviews/thesis-paper.md`, starting with a verdict line (PASS /
PASS-WITH-WORDING / BLOCK). Append after each numbered item. Probes in `reviews/probes/V4/`.
Commit only those paths.

**Check, in order:**
1. **Numbers:** every number in `thesis/` text is a macro, every macro resolves in
   `thesis/numbers.tex`, and `thesis/numbers.tex` is byte-identical to a fresh
   `scripts/write_numbers.py` run. List any typed result number with file:line.
2. **Claims:** every statistical claim matches `results/*.json` and V3's required wording; no
   "coverage" where only one-panel containment exists; "overconfident" never used as "misses the
   truth"; Foil 2 never compared with Theta_hm; the image never called an identified set. List each
   overclaim with an exact replacement sentence.
3. **A2:** the five written expectations are reported as met / not met correctly.
4. **The proposed headline:** true clause by clause against `results/`? Is it the strongest claim
   the evidence supports and no stronger?
5. **Citations:** sample at least 12 entries of `refs.bib` (all if fewer than 25) and verify each
   against Crossref or the publisher page; list wrong authors, years, titles or DOIs.
6. **Build and budget:** `latexmk` clean (zero `^!`, undefined, `Overfull`, `Float too large`);
   main text about 20 pages, total about 30. Render 3 pages and check the figures are legible.
7. **Disclosures:** A1 and A2 are labelled as written after earlier results; the AI-assistance
   statement is present and marked as a draft for the owner.

Budget: about 70 tool calls; no command over 3 minutes. Do not edit any other file.
