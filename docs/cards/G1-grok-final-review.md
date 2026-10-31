# G1 (verifier, third family: xAI Grok 4.7): adversarial final review before wrap-up

You are an independent, adversarial reviewer. The project was:
- produced by Claude (PM, writer) and GPT (engineer);
- verified by Gemini (`reviews/v2-code.md`, `reviews/v2-paper.md`).

You are the third family. Your job is to find what three earlier passes missed: errors in the
methods, the statistics, the code, or the claims. **Do not repeat the earlier checks.** Read the
two review files first, and spend your budget on what they did not test.

**Root:** the repo at `512bf7a` or later. Design: `docs/preregistration-v2.md` (frozen `c5560e9`).
Paper: `writeup/main.tex` and `writeup/cover.tex`. Results: `results/`.

**Report:** `/Users/bonorinoa/Hermes/Projects/ecn593/reviews/v2-final-grok.md`.
- The first line is the verdict: **WRAP** (only wording left), **WRAP-WITH-FIXES** (listed fixes, none
  methodological), or **BLOCK** (a methodological or computational defect).
- Append after each numbered item.
- Probes go in `reviews/probes/G1/` in the spine.

**Attack these, with file:line evidence and your own scratch code where a number is involved:**
1. **The estimand of Foil 2 against its "truth".**
   - `hajek_contrasts` (IPW with first-order exposure probabilities) targets an Aronow–Samii
     finite-population exposure contrast.
   - `evaluate_spill` / `true_spill_from_panel` define the truth as the mean of *unweighted* realized
     stratum contrasts.
   - Are these the same estimand? Derive it.
   - The PM measured the paired gap at c*, over 200 panels: Hajek − truth = 0.00011 (SE 0.00017). Check
     it independently at c* and at the median-I point.
   - Does any claim in the paper depend on the difference?
2. **Implausibility with a diagonal V while the four moments are correlated** (same panels, paired arms),
   compared with the chi2_4 quantile. Is the threshold's nominal level meaningful? Estimate the
   correlation of the four moments at c* (≤ 1,000 reps, background mode). Is the paper's wording
   honest about this? The Gemini verifier flagged it only as a premise note.
3. **delta as the binding assumption.** The PM's reading: with delta_level = 0.02, each level can
   miss by about sqrt(9.49 x 0.0004) = 0.062, more than theta1(c*) = 0.036, so the pilot cannot pin
   kappa (spread ratio 0.96). Is this right? Is it the main reason Theta_hm is as wide as in v1?
   Does the paper explain the width correctly, or does it attribute it to something else?
4. **Panel overlap.** The foils' panel is rep 0, which is also one of the 200 reps that define z.
   Does this bias any verdict or flag? Quantify it if it can matter.
5. **The two-analyst framing** (`main.tex`, section "The evaluation: two analysts, two layers").
   Is it logically sound? Is any conclusion stronger than the evidence (one panel per point, three
   points)? Check the headline in `cover.tex` and the abstract word by word against `results/`.
6. **Model-properties and partial-identification claims.** The contraction, uniqueness,
   linear-in-means and "partial identification from too few moments, not incompleteness".
   Anything wrong or overstated relative to Tamer (2003, 2010), Manski, Imbens–Manski or
   Chernozhukov–Hong–Tamer?
7. **Anything else** that a careful econometrics instructor would attack, ranked by severity.

**For each finding, give:**
- the severity: BLOCK / FIX (wording or disclosure) / NOTE;
- the exact file:line;
- the exact replacement text, or the computation that settles it.

**Fence:**
- Read-only in the repo.
- Do not run `replicate.py` or the Foil 2 check.
- No foreground command over about 3 minutes (use background mode).
- Keep probe scripts and logs in the spine probe folder.
