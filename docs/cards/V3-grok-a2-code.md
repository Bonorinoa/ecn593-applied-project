# V3 (verifier, Grok 4.7, read-only): amendment A2 code, statistics and results

Producer: E3 (Codex gpt-5.6-sol). You are a third model family: independent.
Read `docs/cards/common_rules.md` (below), amendment A2 in `docs/preregistration-v2.md`, the E3
card `docs/cards/E3-engineer-a2.md` and E3's handoff (`docs/cards/progress/E3.md`, `git log`).

**Write one file:** `reviews/a2-code.md`, starting with a verdict line (PASS / PASS-WITH-WORDING /
BLOCK). Append after each numbered item, so a retry resumes. Keep probe scripts and logs in
`reviews/probes/V3/`. Commit only those paths (`git commit -- reviews/a2-code.md reviews/probes/V3`).

**Check, in order:**
1. Does the code implement A2 as written (estimators, weights w from the degree vector, bins H/L,
   the undefined rule, offsets, R, Clopper-Pearson)? Any choice made after a result? file:line.
2. Re-derive the A1 and A2 point estimates independently on the one panel at `c_star` (your own
   code, from `simulate_panel`, the strata and the exact first-order probabilities). They must match
   the JSON to floating precision.
3. The variance: is the linear-contrast covariance the right generalization of the existing
   Aronow-Samii linearization? Does the identity test really pin it? Is SE/SD sensible?
4. The truth: is theta2(c) the right target for all three analysts? Is the comparison like for like
   (units, sign)?
5. Locks: the main results, the Foil 2 check and the delta menu unchanged; determinism; tests pass
   (run them).
6. The five written expectations (a)–(e): is E3's met/not-met reading right?
7. Wording a paper may use, and wording it must not use (for example "coverage" vs "containment",
   "unbiased", "identified").

Budget: about 60 tool calls; R <= 1,000 for any re-check; no command over 3 minutes (background
mode for longer). Do not edit any other file.
