PASS-WITH-WORDING

# Verification: lecture video script

Artifact reviewed: `video/script.md` and `video/narration/s01.txt` through `s10.txt`, with the script's declared source baseline `d230748` and the live A2 working tree. I checked all 95 numbered claim rows against their cited sources and, where the claim describes implementation, against the code. The architecture is substantively faithful. Apply the exact replacements below before rendering.

## Required replacement sentences

1. **Scene 1, `video/script.md:35` — scope of the missing policy data.** “No researcher has data on that policy” is universal; the design only says that the degree policy is not observed in this study (`docs/preregistration-v2.md:22-23`).

   Replace:
   > No researcher has data on that policy.

   with:
   > In this design, the researcher observes no data from the degree policy.

2. **Scene 2, `video/script.md:63` — what lives in `data/` and `results/`.** The cited contract is about endogenous quantities, not every computed artifact: the pipeline also writes figures and a lock file (`src/poc_abm/pipeline.py:8-9, 233-234, 306-309`).

   Replace these two sentences:
   > Everything the model computes lives elsewhere, in data and results. Never in config.

   with:
   > The endogenous quantities live elsewhere, in data and results, never in config.

3. **Scene 4, `video/script.md:130` — a pilot can realize the degree vector.** The random arm samples 80 people without replacement (`src/poc_abm/kernel.py:81-84`), and the preceding sentence correctly gives the event positive probability, one over “eight hundred choose eighty.” “No pilot ever” is therefore literally false. The same overstatement appears in the frozen amendment at `docs/preregistration-v2.md:149-154`; that is a premise wording error, not a code error.

   Replace:
   > So no pilot ever realizes the policy.

   with:
   > A randomized pilot therefore has only a vanishingly small chance of realizing the degree policy.

4. **Scene 7, `video/script.md:214` — the image is a sampled range.** The code samples at most 400 NROY rows and takes the empirical minimum and maximum (`src/poc_abm/estimand.py:24-30, 431-435`; `src/poc_abm/pipeline.py:153-178`). Calling it simply “the range of answers the targets cannot rule out” can be heard as the full NROY image, which the project explicitly does not claim.

   Replace:
   > An image is the range of answers the targets cannot rule out.

   with:
   > Here, an image is the range across the declared sample of four hundred N R O Y points.

5. **Scene 8, `video/script.md:243` — SUTVA alone does not make scaled OLS equal theta two.** The estimator also needs exchangeability, positivity, a correct additive constant-effect model, and a sampling or asymptotic basis for HC1 (`src/poc_abm/diagnostic.py:66-88`; `SPECIFICATION.md` §3.4, required statement 2).

   Replace:
   > With no interference, that would be theta two.

   with:
   > Only under SUTVA, exchangeability and positivity given the covariates, a correctly specified additive constant-effect model, and the usual sampling basis for H C one can that scaled coefficient and interval be read as a report about theta two.

6. **Scene 8, `video/script.md:243` — analyst A1 uses contrasts from S0a, not bare stratum shares.** Amendment A2 defines a weighted sum of Hájek mean differences, each relative to S0a (`docs/preregistration-v2.md:159-167`); the implementation uses the same coefficient structure (`scripts/interference_tradeoff.py:44-63`).

   Replace:
   > A one weights the pilot's exposure strata by the shares the degree policy would create.

   with:
   > A one combines the pilot's Hájek exposure means, each relative to S zero a, using the exposure shares the degree policy would create.

7. **Scene 10, `video/script.md:307` — executable replication command.** The script's own usage is `.venv/bin/python scripts/replicate.py`, not an unqualified `python` (`scripts/replicate.py:3-5`). In the project/Hermes environment the required form also unsets the injected `PYTHONPATH` (`docs/cards/common_rules.md:8-10`).

   Replace:
   > One command: python scripts slash replicate dot py.

   with:
   > One command from the repo root, with Python path unset: env dash u Python path, dot venv slash bin slash python, scripts slash replicate dot py.

   The on-screen command should likewise be `env -u PYTHONPATH .venv/bin/python scripts/replicate.py`.

8. **Scene 10, `video/script.md:307` — macros and PDF build are overstated.** The project guarantees generated macros for result numbers, not literally every number in the paper; dates, quantiles, axis ticks and layout constants are typed (`STATUS.md:12`). PDF compilation is conditional on `latexmk` (`scripts/replicate.py:117-121`).

   Replace:
   > Then it copies the paper's figures, writes every paper number as a macro, and builds the PDF.

   with:
   > Then it copies the paper's figures, writes the paper's result numbers as macros, and builds the PDF when latexmk is available.

9. **Scene 10, `video/script.md:307` — `results/` does not hold every number.** Configuration constants live in `config/`, targets live in `data/planted.json`, and generated paper macros may also use configuration and graph facts; `results/` holds run outputs (`src/poc_abm/config.py:3-13`; `SPECIFICATION.md` §6).

   Replace:
   > Results hold every number, and the paper reads its numbers only from there.

   with:
   > Results hold the run outputs, and the paper reads its result numbers through generated macros.

## Acceptance checks

1. **Claims versus sources and code:** 95 numbered claim rows reviewed. Apart from the nine wording corrections above, the narration agrees with the cited code and frozen design. The A2 ladder matches the amendment: A0 is Foil 1; A1 transports exposure-specific Hájek means; A2 adds fixed top-80/rest bins; repeated sampling uses 200 fresh offsets and exact Clopper–Pearson intervals (`docs/preregistration-v2.md:156-183`). The live A2 implementation's targeted tests passed: `7 passed`.
2. **No result numbers:** pass. The narration contains no digit characters. Every spoken quantity is a configuration/design constant or a count defined by the design: population/seed size, graph/covariate/horizon settings, Monte Carlo repetitions, discrepancy values, threshold confidence/degrees of freedom, wave/sample counts, exposure cut, diagnostic-point count, and A2 repetition count. No endpoint, interval, bias, coverage, or other run result is spoken.
3. **Narration parity:** pass. All ten `video/narration/sNN.txt` files are byte-identical to the corresponding narration blocks in `video/script.md`.
4. **Glossary and A2 terminology:** pass after replacements 4 and 6 sharpen the sampled-image and A1 definitions. NROY is expanded once; the image is explicitly called neither a posterior nor an identified set; F-OVERCONF and F-HONEST use the glossary's verdict geometry; “containment” is reserved for one panel and “coverage” for repeated sampling. The amendment-A1/analyst-A1 name clash is explicit.

## Premise check

`docs/preregistration-v2.md:151` says “no pilot ever realizes the policy” immediately after assigning that event the strictly positive probability `1 / C(800, 80)`. The formula is correct; “ever” is not. The review does not modify the frozen pre-registration, but replacement 3 keeps the video mathematically correct.

## Verification commands

- `env -u PYTHONPATH .venv/bin/python /Users/bonorinoa/.hermes/profiles/verifier/cache/scratch/video_script_probe.py` — exit 0; 10 blocks, 10 files, every pair byte-identical, no digit characters.
- `env -u PYTHONPATH .venv/bin/python -m pytest tests/test_interference_tradeoff.py -q -p no:warnings` — exit 0; 7 passed.
- `git diff -- video/script.md video/narration && git status --short -- video/script.md video/narration reviews/video-script.md` — exit 0; reviewed video inputs were unchanged during the check.

Not verified here: audio pronunciation, audio duration, visual layout, or final rendering; those belong to VR.

Model route proved from `/Users/bonorinoa/.hermes/profiles/verifier/logs/agent.log`: `API call #1: model=gpt-5.6-sol provider=openai-codex` for session `local-df5806f9e945073d6fe9b49cbbbdaeb157091fb0e6d63dfac4b1378dfcd2f5b3`.
