# W1 (writer): the paper to v2, and to the two-analyst evaluation

**Root:** the repo at the E1 commits plus any fixes after V1 (V1's report is
`/Users/bonorinoa/Hermes/Projects/ecn593/reviews/v2-code.md`; apply its wording items to
README/SPECIFICATION too). Read `docs/preregistration-v2.md` first.

**Deliverable:** `writeup/main.tex` and `writeup/cover.tex` rewritten to v2. The PDF builds
with `latexmk -g -interaction=nonstopmode` in `writeup/` with no undefined references or
macros. Then `env -u PYTHONPATH .venv/bin/python scripts/replicate.py` runs end to end, in
background mode (about 8 min).

**Content, in this order of importance:**
1. **Remove every World Bank part.** That includes the sections, the required note, `empty.png`,
   and the "F-EMPTY run" paragraphs.
2. **The targets section.** Status quo + randomized pilot. Why the degree arm is never a target.
   The four moments with their definitions. delta and tau. The paired-rep identity
   pilot_level - sq_level = theta1(c*), stated as intended.
3. **The evaluation, as two analysts.**
   - *The field experimenter* has one panel from the real village (c_star). The test is whether the
     interval is right about its own world. This is layer (a): the estimator's identification
     conditions (SUTVA, unconfoundedness given X and a linear model for Foil 1; a correct exposure
     mapping and a known randomization for Foil 2).
   - *The calibrator* fits the model and works at one best-fitting point (min-I, median-I). The tests
     are whether it is right about the real village (covers_planted_truth) and how its interval
     sits against the image. This is layer (b): "my world is the world".
   - The image is honest only relative to its maintained assumptions (the kernel, C, delta, the
     targets). The sampled image can understate the true NROY image; the endpoint recheck
     addresses only noise-driven outward bias.
   - Report what the results show at all three points, from macros only.
4. **Model properties, one short paragraph each, with the numbers as macros (ask E1's
   `numbers.tex`; if a needed macro is missing, compute nothing yourself; list it in the handoff):**
   - the update map is a contraction in sup-norm with modulus at most (beta+gamma)/4 <= 0.35, so
     there is a unique stationary regime that forgets Y(0) (0.35^20 < 1e-9), with no tipping
     points or multiple equilibria;
   - linear-in-means peers (the average, not the sum); a sum would break the contraction;
   - an Erdos-Renyi graph that is locally tree-like (global clustering is a macro; if E1 did not
     add one, list it as missing).
5. **Relation to partial identification** (the reporting logic only; keep the existing "what the
   procedure is not" list).
   - Partial identification here comes from too few moments in a complete model with a unique
     equilibrium, not from an incomplete model with multiple equilibria (Tamer 2003).
   - The image is the set under the maintained assumptions. Adding "c = c0" collapses it, which is
     Manski's law of decreasing credibility.
   - Section 6's `nroy_param_spread` says which parameters the targets restrict.
6. **Cover page and abstract** to the v2 headline. Write the headline from the results, then flag
   it in the handoff for Augusto to adopt. Do not claim it is adopted.

**Citations:**
- Use only references already in the paper.
- New ones (Tamer 2003 Econometrica; Bramoullé, Djebbari and Fortin 2009 J. Econometrics;
  Manski 1993 Rev. Econ. Stud.; Kaido, Molinari and Stoye 2019 Econometrica; Chernozhukov, Hong and
  Tamer 2007 Econometrica; Imbens and Manski 2004 Econometrica) are allowed only if you confirm
  each on the publisher's site or DOI and put the DOI in the reference. Otherwise leave
  `[CITE?]` and list it.

**Style:** relaxed prose, as in the current paper. Every result number is a macro from
`writeup/numbers.tex`. Keep the existing structure where it still fits. Run
`python3 ~/.hermes/cache/scratch/flowpass_guard.py` if it exists, and treat its locked
paragraphs as advisory: the v2 change may legitimately rewrite them, so name each one you change.

**Artifact:**
- Commits on `main` (main.tex, cover.tex, main.pdf, and README/SPECIFICATION wording fixes from V1).
- The progress file `docs/cards/progress/W1.md`.
- A handoff listing the sha, the replicate.py final lines, the headline candidate, missing macros
  and `[CITE?]` items.

**Fence:**
- No code, results or numbers changes. If a macro is missing or wrong, report it; do not type numbers.
- Do not touch `docs/preregistration-v2.md` or the spine.
