# G2 (verifier, Grok 4.7): close the project

You are an independent verifier. The producers were Claude (the writer, W2) and GPT/Claude (the
engineer, E2). Report: `/Users/bonorinoa/Hermes/Projects/ecn593/reviews/v2-close.md`. The first
line is the verdict: **CLOSE** / **CLOSE-WITH-WORDING** / **BLOCK**. Append after each item. Probes
go in `reviews/probes/G2/`.

**Check:**
1. **E2, the delta menu.**
   - The code implements amendment A1 of `docs/preregistration-v2.md` exactly.
   - The delta = 0.02 entry matches the main run (re-run the assertion yourself, or recompute
     from the JSON).
   - In your own scratch code, recompute one menu entry's spread ratios from its data, if stored,
     or check the logic by reading the code with file:line.
   - The main design is unchanged (diff `config/` and `src/` against `512bf7a`; any change must
     be an optional argument whose default keeps the old behavior).
2. **G1's findings.** Every FIX item from `reviews/v2-final-grok.md` is applied or answered with
   evidence. List any unresolved item.
3. **W2's text.**
   - The disclosures (diagonal V, panel overlap, Foil 2 truth vs Hajek target) are accurate.
   - The "delta is the binding assumption" explanation is correct.
   - The menu section is labeled as post-result.
   - gamma reads "not met".
   - The three new citations resolve by DOI, with the right authors, year and journal.
4. **Integrity.**
   - pytest passes;
   - the 226+ macros regenerate identically in memory;
   - no typed result numbers;
   - the PDF builds byte-identically in scratch;
   - a fresh `git clone` into scratch with the README setup and `scripts/replicate.py` prints
     REPLICATED (background mode; about 21 min).
5. **The headline candidate** in W2's handoff and the cover: true word by word against `results/`?

**Fence:**
- Read-only in the repo.
- No foreground command over about 3 minutes.
