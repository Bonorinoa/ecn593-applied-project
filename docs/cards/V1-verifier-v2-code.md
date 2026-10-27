# V1 (verifier, cross-family): check the v2 code, statistics and results

You are an independent verifier. The producer was a different model family (GPT, via Codex).
Write your report to `/Users/bonorinoa/Hermes/Projects/ecn593/reviews/v2-code.md`. The first
line is the verdict: PASS / PASS-WITH-WORDING / BLOCK. Append after each numbered item, so a
retry resumes. Keep probe scripts and logs in `reviews/probes/V1/` inside the spine folder.

**Root:** the E1 commits (shas in E1's handoff; read them with `hermes kanban --board ecn593 show`
on the parent card, or `git log`). The design is `docs/preregistration-v2.md` (frozen).

**Check, with file:line evidence for each:**
1. **Pre-registration fidelity.** Moments: names, order, arms, W, the reps and the pairing. Also
   delta, tau (= 9.4877, df 4), the planted file and REPS_Z. The c_star point and the two
   containment fields at all three points. `nroy_param_spread` as defined. Nothing in section 4
   changed. Diff the locked files (`kernel.py`, the foil estimators in `estimand.py` and
   `diagnostic.py`, `classify_interval`, `scripts/check_foil2_coverage.py`) against `v1-worldbank-moments`.
2. **Independent recomputation.** In scratch code of your own (not the repo's functions),
   recompute the four moments at c* for reps 0..9 from `simulate_panel` output, and compare with
   the repo's `simulate_moments(world, c_star, reps=10)`. Recompute I(c) for 3 NROY points from
   their stored M and V. Recompute `nroy_param_spread` from `results/planted/image_points.json`.
   Check `pilot_level - sq_level` at c* against `theta_star.theta1` (the paired-rep identity in
   the pre-registration).
3. **Containment flags.** For each point and foil, recompute the flags from the stored intervals and truths.
4. **The tests.** Is each new hand example correct by hand? Does any test assert a result number
   that would hide a bug?
5. **World Bank removal** complete (the grep in E1's acceptance 2) and nothing broken by it.
6. **Determinism.** Run `scripts/run_poc.py planted` in background mode (about 4 min). Confirm that
   `git diff results/` changes only `ran_at`/`git_commit`, then `git checkout -- results figures locks`.
7. **The README and SPECIFICATION v2 text** against the code: list every false, stale or
   overstated sentence, with the exact replacement.
8. **Premise check:** anything in the pre-registration that is statistically wrong or misleading.

**Fence:**
- Read-only in the repo, except the probe and report files named above in the spine.
- Do not run `replicate.py` or the Foil 2 check.
- No command over about 3 minutes in the foreground.
