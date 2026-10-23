# ECN 593 applied project: honest images of a policy effect

A village agent-based model has five free parameters and three targets, so many parameter points fit the targets equally well. The project reports the image of a policy effect over the sampled parameter points that fit, and tests whether two one-world analysts give honest intervals.

## Why it matters

Calibrated simulators inform policy advice. Calibration usually ends in one "best" parameter point. If many points fit equally well, a one-world interval can look precise and still be wrong. The image is the honest report. It applies the partial-identification logic of Manski (2003) and Tamer (2010) to a calibrated simulator. The image is not an identified set in Tamer's sense (see "What the project does not claim").

## The headline

> Foil 1 is F-OVERCONF at both diagnostic points; no robust Foil 2 verdict is claimed at either point.

The analyst who ignores interference reports a tight interval that sits inside the image and misses the truth. The analyst who models exposure passes the predeclared average-variance gate, but its interval is wide and gets no robust verdict.

How to read it:

- **The model.** N = 800 people sit on a fixed random graph. Each person has a preventive-behavior level Y in (0, 1). A campaign seeds 10% of the people.
- **The targets.** Three targets z are planted: z = M(c*) at a known point c*. So the true effect is known, and the test can grade the analysts.
- **NROY and the image.** History matching evaluates three finite Latin-hypercube waves. NROY is the union of sampled points with I(c) at or below tau. Theta_hm is the range of theta2 over a declared uniform sample of 400 NROY points. Here theta2 is the effect of seeding the 80 highest-degree people, against no campaign.
- **Foil 1.** This analyst assumes no interference (SUTVA). The estimate is OLS on the degree arm, scaled by k/N = 0.1.
- **Foil 2.** This analyst models exposure to treated neighbors on a randomized arm. The target is the spillover delta_spill. The image of delta_spill is Theta_exp.
- **F-OVERCONF.** An interval is F-OVERCONF if it lies strictly inside its image. For Foil 1 this is a statement about interval geometry under the analyst's assumptions. It is not a coverage claim.
- **Diagnostic points.** The min-I point and the median-I point of NROY. They are chosen by I only, never by the effect.

![Images and one-world intervals at the two diagnostic points](figures/planted/overlay.png)

Rows are the min-I and median-I points. The left column shows theta2 against Theta_hm, with the Foil 1 interval. The right column shows delta_spill against Theta_exp, with the Foil 2 interval. A star marks the truth at that point. A triangle marks the truth at c*.

## The numbers behind the headline

All numbers come from `results/planted/poc_results.json` and `results/checks/foil2_coverage.json`.

| Quantity | Value |
|---|---|
| Targets z (level_imm, gradient_edu, level_internet) | 0.2638, 0.05, 0.2618 |
| Threshold tau | 7.8147 |
| Points kept per wave (of 1000 each) | 202, 416, 373 |
| NROY size | 991 |
| Image Theta_hm (400 sampled NROY points) | [0.00587, 0.07325] |
| Image Theta_exp (400 sampled NROY points) | [−0.000571, 0.026893] |
| theta2 and delta_spill at the planted point c* | 0.03826 and 0.00792 |

| | min-I point (I = 0.0017) | median-I point (I = 2.0208) |
|---|---|---|
| Truth theta2 | 0.03708 | 0.06346 |
| Foil 1 interval | [0.03259, 0.03465] | [0.05832, 0.05949] |
| Foil 1 verdict, contains truth | F-OVERCONF, no | F-OVERCONF, no |
| Truth delta_spill | 0.00613 | 0.00809 |
| Foil 2 interval | [−0.003022, 0.015410] | [0.000112, 0.016406] |
| Foil 2 verdict, contains truth | no verdict, yes | F-OVERCONF in the pilot image, yes |

The Foil 2 verdict at the median-I point is not robust. An independent recheck of the lower-end candidate of Theta_exp is 0.000201, above the lower end of the interval.

Foil 2 calibration check: the nominal 95% interval covered 93.4% of assignments (exact 95% binomial interval 92.9%–93.9%). The average estimated variance was 1.034 times the empirical design variance.

## How to replicate

One-time setup, then one command:

```bash
uv venv .venv --python 3.14
uv pip install --python .venv/bin/python -r requirements.txt -r requirements-dev.txt
.venv/bin/python scripts/replicate.py            # everything, about 13 minutes
.venv/bin/python scripts/replicate.py --quick    # everything except the Foil 2 check, about 7-8 minutes
```

`replicate.py` runs the tests, checks z, runs both pipelines and the Foil 2 check, copies the figures into `writeup/`, writes the paper's numbers (`writeup/numbers.tex`), and builds the PDF. It ends with a report that compares every result file with the committed one. The paper types no result: every number in it is a macro from `numbers.tex`. The PDF build needs TeX Live with `latexmk`; without it, upload `writeup/` to Overleaf.

The steps, one at a time:

```bash
python scripts/plant_z.py                        # check: data/planted.json reproduces byte for byte
python scripts/run_poc.py planted                # main run -> results/planted/, figures/planted/
python scripts/run_poc.py worldbank              # historical run -> results/worldbank/ (F-EMPTY)
python scripts/check_foil2_coverage.py           # Foil 2 calibration check -> results/checks/foil2_coverage.json
python scripts/draw_figures.py planted           # redraw figures from saved results (no simulation)
python scripts/sync_writeup_figures.py           # copy the figures into writeup/figures/
python scripts/write_numbers.py                  # write writeup/numbers.tex from config/ and results/
```

Measured runtimes on an Apple-silicon laptop, from a fresh clone:

- The full `replicate.py`, from a fresh clone at commit `c075b5a`, took 787 s (about 13 minutes): tests 27 s, World Bank run 44 s, planted run 362 s, Foil 2 check 350 s, the paper steps under 5 s.
- The planted run varies with machine load: 270-400 s in our runs.
- `replicate.py --quick` skips the Foil 2 check and takes about 7-8 minutes.
- Before commit `c075b5a` cached its exposure probabilities, the Foil 2 check took about 52 minutes. The results are identical.

A fresh clone gave the committed results. Every result field matches the earlier run except `ran_at` and `git_commit`. The files `image_points.json` and `overlay.png` are byte-identical. A rerun reproduces every number, because every random stream is seeded.

Pins: Python 3.14, numpy 2.5.4, scipy 1.18.1, matplotlib 3.11.2, pytest 9.1.1. Reproducibility is part of the claim, so a rerun must match to the last digit. The file `locks/freeze-*.txt` records the full environment of each run. It includes extra packages that the code does not import. The project does not use Mesa, pandas, or GPU libraries. The kernel is vectorized algebra.

Pin change on 2026-10-22. The committed results, figures and lock files come from the earlier pins (Python 3.11, numpy 2.4.6, scipy 1.15.3, matplotlib 3.10.3, pytest 8.4.2). macOS 27.0.1 cannot load the compiled scipy 1.15.3 extension, so the pins moved. A full `replicate.py` on the new pins matched every committed result file, with one exception. In `results/checks/foil2_coverage.json`, the upper Clopper-Pearson bound moved by 1.1e-16 (the last binary digit). The gate still passes. `writeup/numbers.tex` did not change (174 numbers). The figures show the same data. Only antialiasing and glyph pixels differ, so the PNG files are not byte-identical.

Two cautions. `run_poc.py` calls `uv` and overwrites the committed results, figures and lock file of its run. `check_foil2_coverage.py` reads `results/planted/poc_results.json`, so run the planted run first. After a rerun, use `git diff results/` to compare your numbers with the committed ones. In our clean-clone check, only `ran_at` and `git_commit` changed.

## Repository layout

- `config/`: every exogenous parameter, chosen before any run. `world.toml` is the simulated village and the policy question. `design.toml` is the analyst's choices, including the Foil 2 check. Endogenous quantities are never in config: they live in `data/planted.json` and `results/`.
- `src/poc_abm/`: the code. The kernel, the moments, history matching, the estimands, the foils, the pipeline and the figures. `config.py` only loads the two TOML files.
- `scripts/`: `replicate.py` and the steps it runs, plus `draw_figures.py` and the World Bank fetcher.
- `tests/`: 52 tests. Most of them check hand-computed examples.
- `data/`: the targets z (`planted.json`) and the stored inputs of the World Bank run.
- `results/`: the committed JSON of each run, and the Foil 2 calibration check.
- `figures/`: the figures of each run (`planted/` and `worldbank/`).
- `locks/`: the frozen package list of each run.
- `writeup/`: the paper as a self-contained Overleaf project: `main.tex`, `cover.tex`, `numbers.tex` (generated), `latexmkrc` (XeLaTeX, reproducible PDF), figure copies and the compiled `main.pdf`. Tests check that the figure copies and `numbers.tex` match the results.

`SPECIFICATION.md` describes the code in detail. If the two disagree, the code is what ran.

## What the project does not claim

- Theta_hm is not a posterior. It is not a Manski/Tamer identified set. It comes from a thresholded discrepancy. Sampling noise is folded into the variance matrix V. The kernel is taken as true. The image shares the reporting logic of a set, so do not collapse it to a point.
- The closest NROY point (I = 0.0017) does not recover c*. Fit does not pick the truth.
- F-OVERCONF for Foil 1 is about interval geometry under the analyst's assumptions. It is not a coverage claim.
- The project has one planted world, one graph, and one set of targets. It claims no external validity.

## The World Bank run

`python scripts/run_poc.py worldbank` reproduces the 2026-08 attempt with real World Bank anchors. It is a historical sensitivity run. It ends in F-EMPTY: the best I is 204 against tau = 7.8. In the 1,000 sampled wave-1 points, none passed the threshold. The closest sampled education correlation was 0.05, against a target of 0.61.

> The World Bank sensitivity run reproduces a historical F-EMPTY calculation. Its diagonal weights are legacy heuristic cross-entity dispersion terms, not design-based sampling variances or village-level measurement-error variances. The source includes overlapping regional/income aggregates, uses ddof=0 for level dispersion, and uses an asymptotic n-2 correlation convention.

## Planned extensions

1. A construct-validity layer. It scores Y through noisy or biased measures and screens the measures. It is parked until the core results are frozen. The code is at commit `ebed7ce`.
2. Image endpoints with a declared precision plan. Use more reps for every candidate before taking the extrema, or use a simultaneous procedure.
3. External targets with a stated target population and a transport model. The World Bank run shows what fails without one.
4. A design-based third foil. It needs randomization across villages.
5. A second kernel family. It shows how much of the image is due to the model choice.

## Status

Results freeze: 2026-11-20. Delivery: 2026-12-01.
