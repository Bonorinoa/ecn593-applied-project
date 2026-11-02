# W4 (writer, Claude Opus): the paper's fix pass

Read `docs/cards/common_rules.md` (below), `reviews/thesis-paper.md` (V4's verdict on your W3
draft), `reviews/a2-code.md` (V3) and E4's handoff (`docs/cards/progress/E4.md`).

**Acceptance:**
1. Apply every required replacement in `reviews/thesis-paper.md` verbatim, or, where you disagree,
   leave the sentence and write the reason in the handoff (V5 will rule).
2. Every `\MISSING{...}` is gone: E4 generated the A2.1 macros into `thesis/numbers.tex`. Use them.
   Label the variance split as **descriptive and designed after the A2 results** (addendum A2.1),
   never as a pre-registered result.
3. The three-part reading of the trade-off may appear as an interpretation, clearly labelled
   post hoc: (i) bias removed; (ii) a real rise in sampling SD; (iii) extra interval width from the
   Young bound, because the design cannot identify the covariance of pairs that are never jointly
   exposed (Aronow and Samii 2017). Say that (iii) depends on the exposure map, and do not call the
   inflated intervals calibrated.
4. Rebuild: zero `^!`, undefined, `Overfull`, `Float too large`; main text about 20 pages, total
   about 30. Commit `thesis/` sources and `thesis/main.pdf` by explicit path.

**Artifact:** commit shas, a list of every V4 item with "applied" or "not applied: reason", page
counts. Progress file: `docs/cards/progress/W4.md`.

**Fence:** `thesis/` (not its generated files) and your progress file only.
