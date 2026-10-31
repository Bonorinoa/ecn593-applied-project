# W2 (writer): final polish of the paper and docs

**Gate first.** Read `/Users/bonorinoa/Hermes/Projects/ecn593/reviews/v2-final-grok.md` (card G1).
- If its verdict line is **BLOCK**: do not edit anything. `kanban_block` yourself with kind
  `needs_input`, quoting the blocking items.
- Otherwise apply what follows, and read E2's handoff (the delta menu) on the board.

**Root:** the repo at the latest commits from E2 and G1 (G1 writes only in the spine).

**Apply, in this order:**
1. **Every FIX item in the G1 report.** Use its exact replacement text, unless the text is wrong
   against the code or the results. In that case, say so in the handoff with file:line evidence.
   Report each NOTE item as applied or not, with a reason.
2. **Disclosures** (in "What the procedure is not" or the design section, whichever fits; use G1's
   numbers where it quantified them):
   - the diagonal V while the four moments are correlated, so tau = chi2_4(0.95) is a heuristic
     threshold, not a calibrated test level;
   - the foils' panel (rep 0) is also one of the 200 reps that define z;
   - Foil 2's truth is the mean of unweighted realized stratum contrasts, while the Hajek estimator
     targets the IPW exposure contrast. State the measured gap and that it is negligible here because
     of linear-in-means. Say a summed-peer kernel could break this.
3. **delta is the binding assumption.** In the results, explain the width of Theta_hm.
   - delta_level = 0.02 allows each level a miss of about sqrt(tau x delta^2) (a macro if E2 or E1
     made one; otherwise list it as a missing macro). That is more than theta1(c*), so the pilot
     cannot pin kappa.
   - Then a new subsection, "A menu of assumptions (amendment A1)". It gives the delta menu table
     from E2's macros, labeled clearly as decided after the v2 results. It ties the menu to Tamer
     (2010): more assumption (smaller delta) gives a smaller set and less credibility.
   - Report F-EMPTY or no-verdict outcomes exactly as found.
4. **gamma: "not met".** Replace "whether the expectation on gamma counts as met is a call for the
   author" with a plain statement: the expectation was not met; a ratio of 0.992 (macro) is no
   restriction.
5. **The three `[CITE?]` items in section 8.** Craig, Goldstein and Vernon (history matching),
   Beven (equifinality), Halloran and Hudgens (interference).
   - Find the right paper for each.
   - Confirm it exists on the publisher's site or by DOI resolution, and add the reference with its DOI.
   - If you cannot confirm one, rewrite the sentence without the claim, and say so in the handoff.
6. **The headline is NOT adopted yet** (Augusto decides after G1). Keep the cover headline as it is,
   unless a G1 FIX item changes its facts. Put the final candidate in the handoff.
7. **Checks before you finish:**
   - `README.md` and `SPECIFICATION.md` are consistent with the above;
   - the PDF builds clean;
   - `scripts/replicate.py` runs end to end in background mode and prints REPLICATED (now about 21 min).

**Artifact:**
- the commits (main.tex, cover.tex, main.pdf, README, SPECIFICATION);
- the progress file `docs/cards/progress/W2.md`;
- a handoff with: the sha, the replicate.py final lines, every G1 item and how it was handled, the
  citations with DOIs, and the headline candidate.

**Fence:**
- No code, results or numbers changes. If a macro is missing, list it; never type a number.
- Do not touch the pre-registration or the spine.
