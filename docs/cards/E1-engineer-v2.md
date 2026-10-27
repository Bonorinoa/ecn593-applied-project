# E1 (engineer): implement pre-registration v2, run it, commit code and results

**Acceptance (all must hold):**
1. Code implements `docs/preregistration-v2.md` exactly:
   - moments sections 2 and 3: names, order, arms, W, delta, tau (df from the number of
     moments), the planted file;
   - the evaluation in section 5: the `c_star` diagnostic point, and the `*_covers_truth` and
     `*_covers_planted_truth` fields at every point;
   - the readout in section 6 (`nroy_param_spread`);
   - the removal in section 8.

   Config values go in `config/design.toml` (delta per moment name). `config.py` only loads them.
2. World Bank removed everywhere:
   - files and code: `src/poc_abm/data_worldbank.py`, `scripts/fetch_anchors.py`, `data/anchors.json`;
   - the `worldbank` source in `pipeline.py` / `moments.py` / `config.py` and `[worldbank]` in `design.toml`;
   - outputs: `results/worldbank/`, `figures/worldbank/`, `locks/freeze-worldbank.txt`;
   - step 3 of `scripts/replicate.py`, renumbering the steps;
   - the World Bank part of `scripts/write_numbers.py`, `scripts/draw_figures.py`,
     `scripts/sync_writeup_figures.py`, and every test that uses it.

   `grep -rniE "worldbank|world bank|anchors|level_imm|gradient_edu|level_internet" src scripts tests config data`
   must return nothing. The legacy names are gone too.
3. Tests:
   - Hand-example tests for `sq_peer_corr` (a 3- or 4-person graph computed by hand), the moment
     order, delta length = number of moments, tau = chi2.ppf(0.95, 4), and `covers_planted_truth`.
   - Update the existing tests to v2. The suite passes; report the count.
4. `scripts/plant_z.py --write` regenerates `data/planted.json`; a second `plant_z.py` run reports
   "reproduces byte for byte".
5. `scripts/write_numbers.py` emits macros for every v2 result the paper will need: the new
   moments, the c_star point, the covers_planted_truth flags, nroy_param_spread, and two graph
   facts the paper states: the world graph's global clustering coefficient (3 x triangles /
   connected triples) and its mean degree. Drop the
   World Bank macros. Keep the existing planted macro names where the quantity is unchanged, so
   the writer's diff stays small.
6. Run the pipeline steps (tests, z check, planted run, Foil 2 check, figures, numbers) and
   commit the code, `data/planted.json`, `results/`, `figures/`, `locks/` and
   `writeup/numbers.tex` + `writeup/figures/`. Do NOT edit `writeup/main.tex` or
   `writeup/cover.tex`; the writer card does that. The PDF step of `replicate.py` is expected to
   fail until then, because main.tex still cites World Bank macros. Run the steps individually,
   or run `replicate.py` and record that step's failure.
7. Determinism: rerun `scripts/run_poc.py planted` after the commit and show that
   `git diff --stat results/` lists only `ran_at`/`git_commit` changes (`git diff results/` excerpt).
8. Update `README.md` and `SPECIFICATION.md` to the v2 code (Simple English, same style;
   describe what the code does, with file:function references). Remove World Bank text. Keep
   the README replication section accurate, including the measured runtimes.

**Artifact:** commits on `main`. Handoff summary with:
- the shas;
- the test count;
- from `results/planted/poc_results.json`: `n_nroy`, `wave_kept`, `finding_hm`, Theta_hm,
  Theta_exp, `nroy_param_spread`, and every `*_covers_*` flag and `*_vs_*` verdict at the three points;
- the Foil 2 gate line;
- the determinism evidence.

The progress file is `docs/cards/progress/E1.md`.

**Fence:**
- Write only inside the repo.
- Do not touch `writeup/main.tex`, `writeup/cover.tex`, `docs/preregistration-v2.md` or the spine.
- Never change tau, delta, C, the moments or any seed after seeing a result. If a result looks
  wrong, report it; do not tune.

**Locks:** the kernel (`kernel.py`), both foil estimators, `classify_interval` and the Foil 2
check's rules and parameters. They change only if a test proves a bug; report any such bug
before fixing it.
