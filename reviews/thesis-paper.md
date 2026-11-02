PASS-WITH-WORDING

Independent check of the paper at `a3ad54f`, plus a forced `latexmk -g` of that tree in a scratch copy. Producer route was not re-derived; the parent handoff says Claude Opus. This review: `model=grok-4.7 provider=xai-oauth` (verifier agent log, session `local-83c169bca2bde27bbe984493f212e8eb94cbe1bf5591a84db3837ad9834415be`, API calls #21–#23).

No statistical overclaim. The only required fix is the six red `\MISSING` placeholders. The operator's note on this card says those are known, E4 is generating them, and they are not a block by themselves. W4 replaces the placeholders with the macros. Do not type the numerals.

Required replacements, verbatim:

1. In `thesis/sections/07-results.tex:256`, replace `\MISSING{YoungShareAOneStar}` with `\YoungShareAOneStar`.
2. In `thesis/sections/07-results.tex:257`, replace `\MISSING{YoungShareATwoStar}` with `\YoungShareATwoStar`.
3. In `thesis/sections/07-results.tex:261`, replace `\MISSING{DesignRedrawsAOneStar}` with `\DesignRedrawsAOneStar`.
4. In `thesis/sections/07-results.tex:262`, replace `\MISSING{DesignMainTermRatioAOneStar}` with `\DesignMainTermRatioAOneStar`.
5. In `thesis/sections/07-results.tex:263`, replace `\MISSING{DesignFullRatioAOneStar}` with `\DesignFullRatioAOneStar`.
6. In `thesis/sections/C-foil2-check.tex:51`, replace `\MISSING{YoungShareSpillStar}` with `\YoungShareSpillStar`.

Do this only after those names exist in `thesis/numbers.tex`. No other sentence needs to be replaced.

## 1. Numbers

`thesis/numbers.tex` is byte-identical to a fresh `table()` from the committed `scripts/write_numbers.py` (`git show HEAD:scripts/write_numbers.py`, ROOT pointed at the repo, `main()` not called). 454 macros, 19623 bytes. `writeup/numbers.tex` matches the same text. Exit 0.

The working tree's `scripts/write_numbers.py` had 53 uncommitted insertions from E4 at the end of this review. Those were not used. `thesis/numbers.tex` itself was not dirty.

Typed result numbers: none. The scanner listed every decimal and every integer ≥ 50 outside comments (`reviews/probes/V4/probe_v4.log`). The hits are citation years, TikZ lengths, figure widths, the normal quantile `$1.96$` in `07-results.tex:74`, the gate constant `$1.645$` in `C-foil2-check.tex:24`, and `95` in three Clopper–Pearson labels. `1.645` is the literal in `scripts/check_foil2_coverage.py:11,78,112`, not a result. The PDF's `0.3171` and `[0.3057, 0.3285]` are expanded macros; they are not typed in the tex.

CamelCase commands not in `numbers.tex` are `\Bigl`, `\Bigr`, `\Lambda`, `\Pr`, and `\Theta`. Those are LaTeX, not result macros.

The six `\MISSING` names are the required fix above. They print in red on the rebuilt PDF (page 18 shows the three design-ratio placeholders). They are not typed numerals.

## 2. Claims

Checked against `results/interference/tradeoff.json`, `results/planted/poc_results.json`, `results/checks/foil2_coverage.json`, and `results/sensitivity/delta_menu.json`. V3's must-not-say list holds.

- One-panel flags are labelled containment, not coverage (`07-results.tex:125`, `06-evaluation.tex:12-14`). The repeated-sampling column is headed "Containment [CP 95%]".
- "Overconfident" is defined as F-OVERCONF, not as missing the truth (`01-introduction.tex:85-95`, `06-evaluation.tex:33-39`). The charge is applied at the calibrator's points. At `c*` the paper reports the verdict and draws no charge (`07-results.tex:151-154`).
- Foil 2 is compared with `\Theta_{\expset}` only (`05-analysts.tex:89-91`, `07-results.tex:127-128`, overlay caption). At `c*` its interval starts at −0.00140, below `\Theta_{\expset}`'s lower end −0.000578, and the JSON verdict is `None`. At min-I and median-I it contains both spillover truths and is F-OVERCONF. That matches the prose.
- The image is called not an identified set (`08-partial-identification.tex:40-51`). No analyst is called an identified estimator of `\theta_2`.
- "Does not remove the bias. It shrinks it" (`07-results.tex:245-246`). Bias is negative for A1 and A2 at all three points. A1 has the smallest RMSE at all three (min-I 0.00272, median-I 0.00262, `c*` 0.00219).
- The pilot sentence is the erratum's wording: positive and negligible (`02-estimand.tex:67-69`). The paper does not say "no pilot ever realizes the policy" or "positivity fails" for the degree vector. `G-disclosures.tex:13-15` reports that the withdrawn wording had said it never does. That is a disclosure of the erratum, not a claim that the probability is zero. The "positivity" in `B-gap-decomposition.tex:14` is the usual conditional-exchangeability list, not the degree vector.

Interpretive claims that are not just macros, checked from the JSON:

- Spread ratios: `\alpha` 0.259, `\beta` 0.965, `\gamma` 0.992, `\kappa` 0.962, `\sigma_\varepsilon` 0.839. "Only `\alpha` is pinned" and "`\gamma` is below one only in the third decimal" match. The unmet pre-registration expectation is reported as unmet.
- `\sqrt{\tau\delta_1^2}` with `\tau=9.4877` and `\delta_1=0.02` is 0.0616, which exceeds `\theta_1(c^*)=0.03631`. The code's one-moment allowance is at least that large (`moments.py:68-80`). The "exceeds" sentence is true.
- `\DeltaOne=\DeltaFour=0.02` and `\DeltaTwo=\DeltaThree=0.05`, so " `\DeltaOne` for the two levels and `\DeltaTwo` for the two correlations" matches the moment order.
- `\Theta_{\hm}` fresh minus original is `7.9\times10^{-7}` at the lower end and `4.7\times10^{-6}` at the upper end. Both first differ in the sixth decimal. Fresh `\Theta_{\expset}` moves by about `10^{-3}`; the paper does not claim otherwise. Putting the fresh ends in place leaves min-I and median-I Foil 2 strictly inside, and the `c*` Foil 2 interval still starts below the lower end. No classification changes.
- Gate coverage is 0.9343 against nominal 0.95, and `gate.pass` is true. "A little under nominal" is fair. Kernel rates are 0.92, 0.925, and 0.92; the paper reports those as macros and does not call them calibrated.
- Menu: NROY 1038, 667, 432. Quarter `\kappa` spread ratio 0.606 against the main 0.962. `c*` foil verdicts stay F-OVERCONF and `None` at every entry. `consistency_check` says the Main entry equals the planted file.
- A1/A2 SE/SD runs from 2.265 (min-I, A2) to 3.107 (median-I, A1). Those are the two macros in the "between" sentence. The other four ratios sit inside that range.
- `\PilotMinusSq` and `\ThetaOneStar` are both `0.03631`.

No overclaim, so no replacement sentence under this item.

## 3. A2 expectations

From `tradeoff.json`, not from the table macros. At all three points: absolute bias falls strictly A0 > A1 > A2; SD rises strictly and mean width rises strictly; A0 coverage is 0 and A1 and A2 are both 1, so both are closest to 0.95 and both sit 0.05 above it; A1 and A2 bias are negative; every `width_over_theta_hm` is below 1 (largest 0.412). Undefined count is 0.

`07-results.tex:289-304` reports (a), (b), (d), and (e) as met at all three points, and (c) as met only as a tie. The note separates SD from width and refuses the calibration reading. That is the required wording. Section 5 quotes the amendment's expectations as written, including the word "coverage" in the expectation itself, and points to the results section for the check. That is not a claim that the one-panel flag is coverage.

## 4. Proposed headline

The marked headline in `main.tex:70-80` and `01-introduction.tex:70-80` is true clause by clause against `results/`.

- At the real village, A0's one-panel interval misses `\theta_2` (`covers_truth` false) and is narrow (width about 0.002 against an image of width 0.068). The headline says "tight" and "misses". It does not call that interval overconfident. Correct.
- At min-I and median-I, A0 misses the truth at the point and is F-OVERCONF. Correct.
- Over the repeated panels, absolute bias falls from A0 to A1 to A2 at each of the three points, SD rises, and A1/A2 SE/SD is 2.26–3.11. "At every point" is the repeated-panel exercise, which has only those three points. It is not a claim about the whole image.
- In the one panel at the calibrator's points, A1 and A2 contain `\theta_2` at her point and are F-OVERCONF. The headline does not say they contain the village truth. At median-I they do not (`covers_planted_truth` false). That omission keeps the sentence from being stronger than the evidence.

It is not stronger than the evidence. It is also not the most complete sentence the evidence would support: it leaves out the median-I miss of the village truth, and that A1 has the smallest RMSE. Those belong in the body, where they already are. I would not rewrite the headline. The owner's decision stands.

## 5. Citations

`refs.bib` has 31 entries, all with a DOI. All 31 were queried at `https://api.crossref.org/works/{doi}`. Exit 0. That is more than the required sample of 12.

Twenty-seven matched on first-author surname, year, and title with no follow-up. Four probe flags were parser or metadata gaps, not bib errors:

- `athey2018`: authors Athey, Eckles, Imbens. Title matches once the Crossref `<i>p</i>` is read as *p*. The probe's year field was 2018; a second fetch shows `issued` 2017-11-13. The bib year 2018 is the issue year the first probe matched, not a wrong year.
- `savje2021`: Crossref authors Sävje, Aronow, Hudgens; title and year 2021 match. The probe's "s a" / "s vje" mismatch was the probe stripping `{\"a}`.
- `manski2003`: Crossref has the title and year 2003 and an empty author array. The Springer page for `10.1007/b97478` lists Charles F. Manski, the same title, and © 2003.
- `molinari2020`: the chapter DOI has an empty author array, which the bib note says. The CeMMAP record the note cites, `10.1920/wp.cem.2020.1520`, returns author Molinari, the same title, and year 2020.

No wrong author, year, title, or DOI in the 31.

## 6. Build and budget

Forced rebuild, not an up-to-date no-op:

`cp -a thesis $SCRATCH/v4-thesis && cd $SCRATCH/v4-thesis && latexmk -pdf -g -interaction=nonstopmode main.tex`

Exit 0. The scratch `main.log` has 0 lines starting with `!`, 0 "undefined", 0 `Overfull`, 0 `Float too large`. Output: `main.pdf (31 pages, 610591 bytes)`.

Printed page numbers: title unnumbered, then 1–30. The conclusion runs through printed page 21 and onto printed page 22, where the References heading starts. Appendix A starts on printed page 24 (PDF page 25). Main text is about 21 pages. The whole PDF is 31 pages. Both are inside "about 20" and "about 30".

Rendered PDF pages 15, 17, and 19 (Figures 2, 3, and 4) at 130 dpi and looked at them. Axis labels, captions, and the 0% / 100% markers are readable. Figure 2's left panel states that the `\theta_2` bars are smaller than the dots, and that is what the plot shows. Figure 4's caption says the percentages are the repeated-sampling rates and should not be read as calibrated coverage, which matches `figures.py:203` (it prints `100 * coverage`). One non-blocking visual: on the `c*` panel the lower 100% label crowds the 0.04 tick. The rate is still readable. That label lives in `src/poc_abm/figures.py`, which this card does not own.

## 7. Disclosures

`G-disclosures.tex:7-15`: A1 is labelled as written after the main results; A2 as written after the main and A1 results, including the gap decomposition and the Foil 2 check, and before any A2 code or number. The same A1 sentence is in `E-delta-menu.tex:4-8`.

`G-disclosures.tex:31-43`: the AI-assistance statement is present, headed "DRAFT for the author to edit", marked `[Draft.]`, and leaves a bracket for the author to say what he reviewed. That is a draft for the owner, not a finished statement.

## Non-blocking

- `07-results.tex:240` says A0's intervals "almost never reach the truth". The rate is 0 of 200. "Never, in these 200 panels" would be exact. The table already prints 0.000. Not an overclaim, and not a required replacement.
- Figure 4 tick crowding, above. Not a paper-wording fix.
- Premise. The card says write `reviews/thesis-paper.md` and the probes, and do not edit any other file. The common-rules progress file would be another card's tree. The card fence wins; this file is the progress record. E4 had already dirtied `src/`, `scripts/`, and `config/` in this checkout. Those paths were not staged.

## What I did not verify

- A fresh `replicate.py` or a fresh R = 200 tradeoff run. Both write result files outside this fence.
- The Hájek-versus-unweighted spillover comparison. The paper says it was made offline and is not a committed result (`C-foil2-check.tex:9-12`).
- The claim that the peer-correlation moment hardly moves across the box in `\gamma`. The paper says that check is not a committed result (`07-results.tex:87-88`).
- Volume, issue, and page ranges in `refs.bib`. Authors, years, titles, and DOIs were checked.
- Whether E4's uncommitted `write_numbers.py` still reproduces `numbers.tex`. The committed script does.

## Commands

- `env -u PYTHONPATH .venv/bin/python -u reviews/probes/V4/probe_v4.py` — exit 0. Log: `reviews/probes/V4/probe_v4.log`.
- `env -u PYTHONPATH .venv/bin/python -u reviews/probes/V4/probe_v4_cite.py` — exit 0. Log: `reviews/probes/V4/probe_v4_cite.log`.
- HEAD-script byte identity, `main()` not called — exit 0, `thesis_equals_HEAD_script True`.
- `latexmk -pdf -g -interaction=nonstopmode main.tex` in the scratch copy — exit 0. Log flags as in item 6.
