# V6 (verifier, Grok 4.7, read-only): the adopted headline

Producer: the PM (Claude). Read `docs/cards/common_rules.md` (below) and `reviews/thesis-paper.md`.
The owner adopted a headline on 2026-11-01; the PM wrote it. It sits between `% HEADLINE` and
`% END HEADLINE` in `thesis/main.tex` (abstract) and `thesis/sections/01-introduction.tex`, and in a
short form in `README.md`.

**Append `## Round 3: the adopted headline` to `reviews/thesis-paper.md`** with a verdict line
(PASS / PASS-WITH-WORDING / BLOCK). Commit only that file.

**Check:** every clause against `results/` (one-panel flags, repeated-sampling readouts, Theta_hm
and the three truths); the "must not say" list in `reviews/a2-code.md`; that "conservative" is not
read as calibrated and "overconfident" never as "misses"; that the README short form says no more
than the paper; the build is clean (zero `^!`, undefined, `Overfull`, `Float too large`). Give an
exact replacement sentence for anything false or overstated. Budget: about 25 tool calls.
