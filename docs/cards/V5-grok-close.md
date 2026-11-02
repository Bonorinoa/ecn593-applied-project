# V5 (verifier, Grok 4.7, read-only): close the paper and the A2.1 readout

Producers: E4 (Codex) and W4 (Claude). Read `docs/cards/common_rules.md` (below), your earlier
`reviews/thesis-paper.md`, `reviews/a2-code.md`, the E4 and W4 handoffs.

**Append `## Round 2` to `reviews/thesis-paper.md`** with a new verdict line (CLOSE /
CLOSE-WITH-WORDING / BLOCK). Probes in `reviews/probes/V5/`. Commit only those paths.

**Check:**
1. Every round-1 item: applied, or W4's reason for not applying it holds.
2. E4's `scripts/a2_variance_split.py` implements addendum A2.1; the split sums to the reported
   variance; re-derive A1's c_star Young share independently; the A2.1 macros in
   `thesis/numbers.tex` match `results/interference/variance_split.json`.
3. No `\MISSING`, no typed result number, the A2.1 readout labelled post hoc and descriptive, the
   three-part interpretation labelled post hoc and map-dependent, no "calibrated".
4. Build clean; page budget.
5. Fresh clone of `origin/main` into scratch, set up per README, run `scripts/replicate.py` in
   background mode (about 45 min; poll, never block over 3 min). It must print REPLICATED.

Budget: about 70 tool calls.
