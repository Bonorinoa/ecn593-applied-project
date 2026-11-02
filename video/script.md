# ECN 593 architecture lecture: script

Study video for Augusto. It walks the project top-down, from the policy question to the one
command that replicates it. It describes architecture and design only: **no result numbers**.
Every number spoken is a configuration constant, cited to its file and line.

- **Sources of truth:** the code (`src/poc_abm/`, `config/`, `scripts/`), `SPECIFICATION.md`,
  `docs/preregistration-v2.md` (with amendments A1 and A2), and the spine
  (`~/Hermes/Projects/ecn593/STATUS.md`). Line numbers refer to the repo at `d230748`.
- **Narration blocks** are the exact TTS input: each one is byte-identical to
  `video/narration/sNN.txt`. Symbols are spelled for the voice (see the table below), so the
  narration is phonetic on purpose; the visuals use the real symbols.
- **Sources blocks** list each factual claim of the narration, in order, with its source.
  Lines marked *framing* are analogies or signposts, not claims.
- Voice: Gradium Phonon 31m, voice **Hadley** (choice and reason in the storyboard, section 0).

| Written | Spoken in the narration |
|---|---|
| θ2, θ1 | theta two, theta one |
| Θ_hm, Θ_exp | Theta H M, Theta E X P |
| δ_spill | delta spill |
| NROY | N R O Y |
| I(c), M(c), c* | I of c, M of c, c star |
| k/N | k over N |
| F-HONEST, F-OVERCONF | F honest, F over-conf |
| OLS-HC1 | O L S, with H C one standard errors |
| `config/world.toml` | config slash world dot toml |

---

## Scene 1. The policy question, and why one calibrated point can mislead

### Narration
```text
Picture a village of eight hundred people. A campaign can seed eighty of them. If we seed the eighty best-connected people, how much does the whole village move, compared with no campaign at all? We call that number theta two. In this design, the researcher observes no data from the degree policy. So we build a model, and calibrate it to what we can see. Here is the trap. The model has five free parameters, and we match only four summary numbers. Many parameter points fit those numbers about equally well. They can disagree about theta two. And the best-fitting point need not be the true one. So one calibrated point can give a confident answer that is wrong. This project reports the range of answers the data cannot rule out. Then it asks which analysts are honest about that range. Let us go from the top down.
```

### Visual
A sand-outlined circle of 800 small ink dots (the village). 80 dots turn oxblood: the
best-connected people. Title card "θ2: seed the top 80 vs no campaign". Then five sliders
(α β γ κ σ) beside four target bars; several slider settings light up "fits", each paired with a
different θ2 tick on a number line; one is labelled "best fit", a different one "truth (c*)".

### Sources
| # | Claim | Source |
|---|---|---|
| 1.1 | 800 people | `config/world.toml:11` (`n_agents = 800`) |
| 1.2 | a campaign seeds 80 = ceil(0.10 × 800) | `config/world.toml:37`; `src/poc_abm/kernel.py:24-27` |
| 1.3 | "best-connected" = the 80 highest-degree people | `src/poc_abm/kernel.py:85-89` |
| 1.4 | theta2 = village mean under the degree arm minus under control | `src/poc_abm/estimand.py:17-21`; `SPECIFICATION.md` §1.5 |
| 1.5 | the policy is never observed / never a target | `docs/preregistration-v2.md` §1 (lines 22-23) |
| 1.6 | five free parameters, four moments; underidentified on purpose | `config/world.toml:28-33`; `src/poc_abm/moments.py:10`; `SPECIFICATION.md` §2 (line 115) |
| 1.7 | many points fit; fit does not pick the truth | `SPECIFICATION.md` §2 (line 115) and §4 ("Fit does not pick the truth") |
| 1.8 | the project reports the range (the image) and grades analysts against it | spine `STATUS.md`, "What the project is" |
| — | "Let us go from the top down" | *framing* |

---

## Scene 2. The world and the design

### Narration
```text
Everything starts in two small files. The first is config slash world dot toml. It holds the village and the policy question. Eight hundred people. A random friendship graph, with about eight friends each. Three covariates per person. Twenty time steps. The box C of allowed parameters. And the seed share: ten percent. The second file is config slash design dot toml. It holds the analyst's choices. How many Monte Carlo reps. How many waves of search. The allowances for model error, called delta. And the settings of both foils. Both files are exogenous: we choose them before any run. The code only reads them, and adds two rules: the edge probability, and the planted point c star, the center of the box. The endogenous quantities live elsewhere, in data and results, never in config.
```

### Visual
Two cream index cards side by side, headed `world.toml` and `design.toml` (sans, oxblood
section mark). Each line of narration highlights the matching TOML key. An arrow from both cards
into a small box `config.py`, which emits two derived rules: `EDGE_P = edge_rate / N` and
`c* = centre of C`. A sand wall separates them from a third card `data/  results/` labelled
"endogenous".

### Sources
| # | Claim | Source |
|---|---|---|
| 2.1 | world.toml = the village and the policy question | `config/world.toml:1` |
| 2.2 | 800 people | `config/world.toml:11` |
| 2.3 | random graph, about 8 neighbours each (Bernoulli edges, expected degree ≈ 7.97) | `config/world.toml:12-16`; `src/poc_abm/kernel.py:41-43` |
| 2.4 | 3 covariates | `config/world.toml:17` |
| 2.5 | 20 time steps | `config/world.toml:20` |
| 2.6 | the box C | `config/world.toml:25-33` |
| 2.7 | seed share 10% | `config/world.toml:37` |
| 2.8 | design.toml = the analyst's choices | `config/design.toml:1` |
| 2.9 | Monte Carlo reps | `config/design.toml:7-10` |
| 2.10 | waves and points per wave | `config/design.toml:15-16` |
| 2.11 | delta, the discrepancy | `config/design.toml:22-28` |
| 2.12 | points in the image | `config/design.toml:31` |
| 2.13 | foil settings (and the Foil 2 check) | `config/design.toml:37-53` |
| 2.14 | both exogenous, chosen before any run | `config/world.toml:3-6`; `config/design.toml:3-5` |
| 2.15 | config.py only loads them and adds two derived rules (EDGE_P, c* = centre of C) | `src/poc_abm/config.py:11-13, 31, 37` |
| 2.16 | endogenous quantities live in `data/planted.json` and `results/`, never in config | `src/poc_abm/config.py:7-9` |

---

## Scene 3. The kernel and the three arms

### Narration
```text
Now the engine. The world is drawn once: one graph, one set of covariates, fixed seeds. Each person has an outcome between zero and one. Think of it as how far they have taken up the practice. At each of twenty steps, the outcome is updated. The new value is a logistic function of a sum. A baseline, alpha. Your own last outcome, weighted by beta. The average of your friends, weighted by gamma. Your covariates, with fixed weights. If you were seeded, a push, kappa. And noise, scaled by sigma. Alpha, beta, gamma, kappa and sigma are the parameters c. Now the arms. The control arm seeds no one. The random arm seeds eighty people at random. The degree arm seeds the eighty people with the most friends. In each rep, all three arms share the same starting state and the same shocks. So a difference between arms is the policy, not the noise.
```

### Visual
Zoom from the village into one person node with ~8 edges. Build the update as a row of sans
`Text` tokens: `Y(t+1) = Λ( α + β·Y(t) + γ·(friends' mean) + η·X + κ·D + σ·ε )`, each token
fading in with its sentence. The five free symbols (α β γ κ σ) turn oxblood and collect into
`c = (α, β, γ, κ, σ)`; η stays ink with the tag "fixed". Then three mini-graphs side by side:
control (no oxblood), random (80 scattered oxblood), degree (80 oxblood on the hubs). A sand
brace under all three: "same Y(0), same shocks".

### Sources
| # | Claim | Source |
|---|---|---|
| 3.1 | the world (graph + covariates) is drawn once with fixed seeds; every run shares it | `src/poc_abm/kernel.py:30-48`; `config/world.toml:40-41` |
| 3.2 | outcome in (0, 1) | `src/poc_abm/kernel.py:65-67, 104, 116` |
| — | "how far they have taken up the practice" | *framing* (analogy; the code names no construct) |
| 3.3 | 20 steps | `src/poc_abm/kernel.py:111`; `config/world.toml:20` |
| 3.4 | Y ← logistic(α + βY + γ·peer mean + X·η + κD + σε) | `src/poc_abm/kernel.py:112-116`; `SPECIFICATION.md` §1.2 |
| 3.5 | covariate weights η are fixed, not parameters | `config/world.toml:22-23`; `SPECIFICATION.md` §1.2 |
| 3.6 | the treatment push acts at every step (t* = 0) | `src/poc_abm/kernel.py:113`; `config/world.toml:21` |
| 3.7 | c = (α, β, γ, κ, σ_ε) | `config/world.toml:28-33`; `SPECIFICATION.md` §1.2 |
| 3.8 | control seeds none; random seeds 80 without replacement; degree seeds the 80 highest-degree | `src/poc_abm/kernel.py:79-89` |
| 3.9 | arms share the state stream (Y(0) and shocks) within a rep | `src/poc_abm/kernel.py:96-101`; `SPECIFICATION.md` §1.4 |

---

## Scene 4. The estimand theta two, and why a pilot almost never realizes it

### Narration
```text
The estimand is theta two. Run the degree arm and the control arm many times. Average the village outcome in each. Theta two is the difference. Theta one is the same contrast for the random arm. The code uses two hundred paired reps per arm. A real researcher can run a randomized pilot: seed eighty people at random, and watch. That pilot identifies theta one. But theta two compares two whole assignment vectors: the degree vector, and nobody. A random pilot draws eighty of eight hundred. The chance that it draws exactly the top eighty is one over eight hundred choose eighty. A randomized pilot therefore has only a vanishingly small chance of realizing the degree policy. To get from a pilot to theta two, you need two assumptions. An exposure map: your outcome depends on the assignment only through a simple summary, like your treated friends. And transport: what the pilot shows for each exposure also holds under the policy.
```

### Visual
Two stacked bars "degree arm" and "control arm"; a bracket between their tops labelled
`θ2 = E[Ȳ | degree] − E[Ȳ | control]`. A second, shorter bracket for `θ1` (random). Then a
lottery: 800 dots, 80 random picks flash oxblood repeatedly; never the hub set. Caption
`P(pilot = degree vector) = 1 / C(800, 80)`. Two cards slide in: "exposure map", "transport".

### Sources
| # | Claim | Source |
|---|---|---|
| 4.1 | θ2 = mean(degree) − mean(control); θ1 = mean(random) − mean(control) | `src/poc_abm/estimand.py:17-21, 58-62`; `SPECIFICATION.md` §1.5 |
| 4.2 | 200 paired reps per arm | `config/design.toml:8`; `src/poc_abm/estimand.py:49-61` |
| 4.3 | a randomized pilot identifies θ1 (pilot_level − sq_level = θ1(c*) with paired reps) | `docs/preregistration-v2.md` §2 (lines 41-43) |
| 4.4 | θ2 compares two whole assignment vectors, d2 and zero | `docs/preregistration-v2.md` A2, "Why theta2 needs more than a randomized pilot" (lines 149-150) |
| 4.5 | P(pilot = d2) = 1 / C(800, 80): a vanishingly small (negligible) chance, not "never" | same, lines 150-151, and the A2 erratum (lines 202-206); `reviews/video-script.md`, item 3 |
| 4.6 | needs (i) an exposure map and (ii) transport, as defined | same, lines 151-154 |

---

## Scene 5. The targets z

### Narration
```text
What does a researcher actually see? The village in the status quo, plus one randomized pilot. Never the degree policy. So the targets are four moments. Three come from the control arm: the mean outcome, its correlation with the first covariate, and its correlation with the average of each person's friends. The fourth is the mean outcome in the pilot. Stacked together, they are M of c: the moments the model produces at parameters c, averaged over thirty paired reps. The targets, z, are M at the planted point, c star, averaged over two hundred reps. They are stored in data slash planted dot json. Because we planted them, we know the true answer. That is the point of a planted design: we can grade every analyst against the truth.
```

### Visual
A four-row table (cream card, zebra rows in sand): `sq_level`, `sq_corr_x1`, `sq_peer_corr`
(arm: control) and `pilot_level` (arm: random). The degree arm appears greyed out with "never a
target". Arrow `c → M(c)` (30 reps); then `c* → z = M̂(c*)` (200 reps), landing in a file icon
`data/planted.json`. A small oxblood star marks c* at the centre of the box C.

### Sources
| # | Claim | Source |
|---|---|---|
| 5.1 | observable = the status quo plus one randomized pilot; the degree policy is never a target | `docs/preregistration-v2.md` §1 (lines 22-23) |
| 5.2 | four moments: three on control (mean, corr with x1, corr with peer mean), one on random (mean) | `docs/preregistration-v2.md` §2 table; `src/poc_abm/moments.py:10, 107-121` |
| 5.3 | the degree arm is not simulated for the moments | `src/poc_abm/moments.py:95-96` |
| 5.4 | M(c) averages 30 paired reps | `config/design.toml:9`; `src/poc_abm/moments.py:99, 107-109` |
| 5.5 | z = M̂(c*) over 200 reps; c* = centre of C | `src/poc_abm/moments.py:42-55`; `config/design.toml:10`; `src/poc_abm/config.py:37` |
| 5.6 | stored in `data/planted.json` | `src/poc_abm/moments.py:44, 54` |
| 5.7 | planted targets, so the truth is known | spine `STATUS.md`, "What the project is" |

---

## Scene 6. History matching: I of c, delta, tau, waves, NROY

### Narration
```text
Now the search. The implausibility, I of c, measures how far the model's moments sit from the targets. Each moment's miss is squared, and divided by a variance. That variance adds the noise in the targets, the Monte Carlo noise at c, and delta squared. Delta is the discrepancy: an allowance for model error. It is zero point zero two for the two levels, and zero point zero five for the two correlations. A point is kept if I of c is at most tau, the ninety-five percent quantile of a chi-square with four degrees of freedom. Tau is a tolerance, not a test level. The search runs three waves of one thousand Latin hypercube points. Wave one covers the box C. Each later wave searches around the points just kept, widened by twenty percent. There is no emulator: every point is simulated. The union of kept points is N R O Y, short for not ruled out yet. If no point is kept, that is a finding. Tau is never loosened.
```

### Visual
Formula as sans text: `I(c) = Σ (z − M(c))² / V`, then `V = σ²_z + σ²_MC(c) + δ²`, with δ²
in oxblood. A gauge "τ" draws a threshold line. Then the box C (sand rectangle, 2-D slice) fills
with 1000 grey dots; those with I ≤ τ turn oxblood. A dashed bounding box snaps around them,
widens, clips to C; wave 2 and wave 3 repeat. All oxblood dots, from all waves, merge into a
labelled set "NROY". A final card: "empty NROY = F-EMPTY; τ never loosened".

### Sources
| # | Claim | Source |
|---|---|---|
| 6.1 | I(c) = Σ miss² / V (diagonal V) | `src/poc_abm/moments.py:68-75` |
| 6.2 | V = sampling variance of z + MC variance at c + δ² | `src/poc_abm/moments.py:78-80`; `SPECIFICATION.md` §2.3 |
| 6.3 | δ is the discrepancy, an allowance for model error | `config/design.toml:22`; `src/poc_abm/moments.py:58-65`; spine `GLOSSARY.md` (concept "Model-error allowance", doc name "the discrepancy delta") |
| 6.4 | δ = 0.02 levels, 0.05 correlations | `config/design.toml:24-28` |
| 6.5 | keep c if I(c) ≤ τ | `src/poc_abm/history_matching.py:125` |
| 6.6 | τ = χ² quantile at 0.95, df = number of moments (4) | `src/poc_abm/history_matching.py:15-17`; `config/design.toml:19` |
| 6.7 | τ is a heuristic tolerance, not a test level | `SPECIFICATION.md` §4 (the τ bullet) |
| 6.8 | 3 waves × 1000 Latin-hypercube points | `config/design.toml:15-16`; `src/poc_abm/history_matching.py:110-111` |
| 6.9 | wave 1 searches the box C | `src/poc_abm/history_matching.py:101` |
| 6.10 | next box = bounding box of this wave's kept points, span +20% (10% a side); the code also clips it to C (not spoken) | `src/poc_abm/history_matching.py:40-62, 149-150`; `config/design.toml:17` |
| 6.11 | no emulator; every point simulated | `src/poc_abm/history_matching.py:3`; `SPECIFICATION.md` §2.4 |
| 6.12 | NROY = union of kept points across waves | `src/poc_abm/history_matching.py:90, 146` |
| 6.13 | empty NROY is F-EMPTY; τ never loosened | `src/poc_abm/history_matching.py:3-4, 152-163`; `docs/preregistration-v2.md` §7 |

---

## Scene 7. The images: Theta H M and Theta E X P

### Narration
```text
N R O Y is a set of parameter points. But we want answers in policy units. So we draw four hundred N R O Y points at random. At each one, we compute theta two with two hundred reps. The smallest and the largest value give the image, Theta H M. We do the same for a second quantity in the random arm, delta spill. It compares untreated people with at least a quarter of their friends treated against untreated people with no treated friends. Its range is the image Theta E X P. Here, an image is the range across the declared sample of four hundred N R O Y points. It is not a posterior. And it is not an identified set. Its endpoints are extremes of four hundred noisy estimates, so the code rechecks each endpoint's point with fresh reps. And because delta is an assumption, amendment A one reruns the search with smaller level deltas. It is a menu of answers, never a way to choose delta.
```

### Visual
The NROY cloud; 400 dots are sampled (outlined). Each sampled dot drops a tick onto a horizontal
θ2 axis below; the leftmost and rightmost ticks pull out a sand bar labelled `Θ_hm = [min, max]`.
A second axis does the same for `δ_spill` → `Θ_exp`. Small inset of the strata: S1 (seeded),
S0a (no treated friend), S0c (share ≥ 0.25). Then the two endpoint ticks flash and are re-drawn
from "fresh reps". Final strip: three stacked Θ_hm bars labelled "δ_level = 0.02 · 0.01 · 0.005
(A1 menu)" with **no endpoint values** shown.

### Sources
| # | Claim | Source |
|---|---|---|
| 7.1 | 400 NROY points sampled uniformly without replacement | `config/design.toml:31-32`; `src/poc_abm/pipeline.py:153-154`; `src/poc_abm/estimand.py:348-352` |
| 7.2 | θ2 at each with 200 reps | `src/poc_abm/pipeline.py:157-169` |
| 7.3 | Θ_hm = [min, max] of θ2; Θ_exp = [min, max] of δ_spill | `src/poc_abm/pipeline.py:172-177`; `src/poc_abm/estimand.py:24-30` |
| 7.4 | δ_spill is a random-arm quantity: mean of S0c − S0a | `src/poc_abm/estimand.py:103-123, 324-345` |
| 7.5 | S0c = untreated with treated share ≥ 0.25; S0a = untreated with no treated neighbour | `src/poc_abm/estimand.py:77-87`; `config/design.toml:39` |
| 7.6 | the image is not a posterior and not an identified set | `src/poc_abm/estimand.py:3-5`; `SPECIFICATION.md` §4; spine `GLOSSARY.md` ("Images") |
| 7.7 | endpoints are extremes of 400 noisy estimates; each endpoint's point is re-evaluated with fresh reps | `src/poc_abm/pipeline.py:266-293`; `config/design.toml:33-35` |
| 7.8 | amendment A1: level δ in {0.02, 0.01, 0.005}, rerun the waves; a menu, never used to pick δ | `docs/preregistration-v2.md` A1 (lines 114-129) |

---

## Scene 8. The analysts: Foil 1, Foil 2, and the A2 ladder

### Narration
```text
Now the analysts. Each one sees a single panel and reports an interval. They work at three points. The calibrator takes the N R O Y point with the lowest I, or the median I: chosen by fit alone, never by theta. The field experimenter works at c star, with one panel from the real village. Foil one is the SUTVA analyst. On the degree-arm panel, it runs O L S of the outcome on treatment and covariates, and scales the effect by k over N. Only under SUTVA, exchangeability and positivity given the covariates, a correctly specified additive constant-effect model, and the usual sampling basis for H C one can that scaled coefficient and interval be read as a report about theta two. Under this model, it is not. Foil two uses the random arm. It estimates delta spill, with Hajek weights and an Aronow-Samii variance. It never targets theta two. Amendment A two adds a ladder of analysts for theta two. Mind the names: amendment A one was the delta menu; analyst A one is a rung here. A zero is Foil one. A one combines the pilot's Hájek exposure means, each relative to S zero a, using the exposure shares the degree policy would create. A two also splits people into the top eighty and the rest. Each rung assumes less. The amendment wrote its expectations first: down the ladder, bias should fall, and width should rise.
```

### Visual
Three pins on the NROY cloud: "min-I", "median-I" (calibrator, sand pins) and "c*" (field
experimenter, oxblood star). Then two analyst cards. **Foil 1**: degree-arm graph → `OLS-HC1 → β̂`
→ `× k/N` → an interval bracket; a strike-through note "= θ2 only under SUTVA". **Foil 2**:
random-arm graph coloured by strata → `Hájek + Aronow–Samii` → interval for `δ_spill`. Then a
vertical ladder of three rungs, top to bottom: `A0 = Foil 1 (SUTVA)`, `A1 exposure transport`,
`A2 degree-binned transport (H = top 80, L = rest)`. An arrow beside the ladder: "fewer
assumptions ↓". A name-clash box: "amendment A1 = δ menu ≠ analyst A1". Two sloped arrows
labelled "expected: |bias| ↓, width ↑" with the tag "pre-registered expectation, not a result".

### Sources
| # | Claim | Source |
|---|---|---|
| 8.1 | each analyst sees one panel (offset 0) and reports an interval | `config/design.toml:38`; `src/poc_abm/diagnostic.py:164-176`; `docs/preregistration-v2.md` §5 (line 70) |
| 8.2 | three points: min-I and median-I (the calibrator), c* (the field experimenter) | `docs/preregistration-v2.md` §5 (lines 65-68) |
| 8.3 | min-I and median-I depend on I only, never on θ | `src/poc_abm/estimand.py:33-42` |
| 8.4 | Foil 1: OLS of Y on [1, D, X] on the degree-arm panel (HC1 interval, shown on screen), estimate and interval scaled by k/N | `src/poc_abm/diagnostic.py:66-109, 171-174` |
| 8.5 | (k/N)·β̂ equals θ2 only under no interference; not an identified estimator of θ2 here | `src/poc_abm/diagnostic.py:3-8`; `SPECIFICATION.md` §3.4, statement 1 |
| 8.6 | Foil 2: Hájek exposure contrast on the random arm with the Aronow–Samii variance | `src/poc_abm/estimand.py:268-321`; `src/poc_abm/diagnostic.py:10-11, 173-175` |
| 8.7 | Foil 2 targets δ_spill, not θ2 | `docs/preregistration-v2.md` A2 (line 143) |
| 8.8 | A2 = a ladder of analysts for θ2, decreasing assumption strength | `docs/preregistration-v2.md` A2 (line 156) |
| 8.9 | amendment A1 = the δ menu | `docs/preregistration-v2.md` A1 heading (line 106) |
| 8.10 | analyst A0 = Foil 1, unchanged | `docs/preregistration-v2.md` A2 (line 158) |
| 8.11 | analyst A1: pilot strata S1, S0a, S0b, S0c, Hájek means, weights w_s = n_s(d2)/N | `docs/preregistration-v2.md` A2 (lines 159-167) |
| 8.12 | analyst A2: each stratum split into H (the 80 people d2 seeds) and L (everyone else) | `docs/preregistration-v2.md` A2 (lines 168-173) |
| 8.13 | expectations written before any A2 number: \|bias\| falls and SD/width rise from A0 to A2 | `docs/preregistration-v2.md` A2 (lines 136-137, 189-194) |

---

## Scene 9. Interval geometry and the two layers of evaluation

### Narration
```text
How do we judge an interval? First, by geometry, against its own image. Foil one goes against Theta H M. Foil two goes against Theta E X P. If the interval covers the whole image, the verdict is F honest. If it sits strictly inside the image, the verdict is F over-conf: narrower than the range the targets leave open. Anything else gets no verdict. Second, by the truth, in two layers. Layer A asks: does the interval contain the truth at its own point? Is the estimator right about its own world? Layer B asks: does it contain the truth at c star? Is the report right about the real village? At c star, the two layers coincide. One panel gives containment, not coverage. Coverage needs repeated sampling. The Foil two calibration check provides it. So does amendment A two, with two hundred fresh panels per point, and exact Clopper-Pearson intervals.
```

### Visual
A sand image bar `Θ` with three candidate oxblood brackets beneath it: one wider than the bar
("F-HONEST"), one strictly inside ("F-OVERCONF"), one straddling an end ("no verdict"). Then
two vertical ticks on the axis: `θ2(c)` (the point's own truth, ink) and `θ2(c*)` (planted truth,
oxblood star). Labels "Layer (a): own world", "Layer (b): the village". At c* the two ticks slide
together. Closing card in two columns: "one panel → contains / does not contain" vs "R panels →
coverage".

### Sources
| # | Claim | Source |
|---|---|---|
| 9.1 | each interval is classified against its own image: Foil 1 vs Θ_hm, Foil 2 vs Θ_exp | `src/poc_abm/pipeline.py:209, 217`; `SPECIFICATION.md` §3.7 |
| 9.2 | F-HONEST: lo ≤ L and hi ≥ U; F-OVERCONF: lo > L and hi < U; otherwise None | `src/poc_abm/diagnostic.py:31-46` |
| 9.3 | layer (a): truth at the point itself, "is the estimator right about its own world?" | `docs/preregistration-v2.md` §5 (lines 71-72); `src/poc_abm/diagnostic.py:55-63` |
| 9.4 | layer (b): truth at c*, "is the report right about the village?"; the two coincide at c* | `docs/preregistration-v2.md` §5 (lines 73-75) |
| 9.5 | one panel = descriptive containment, not repeated-sampling coverage | `docs/preregistration-v2.md` §5 (lines 79-81); `src/poc_abm/diagnostic.py:49-52`; spine `GLOSSARY.md` ("Truth containment") |
| 9.6 | the Foil 2 calibration check is repeated-sampling evidence | `docs/preregistration-v2.md` §5 (lines 80-81); `scripts/check_foil2_coverage.py`; `config/design.toml:44-53` |
| 9.7 | A2: R = 200 panels per point on fresh offsets; coverage with an exact Clopper–Pearson 95% interval | `docs/preregistration-v2.md` A2 (lines 179-183) |

---

## Scene 10. One-command replication, and where everything lives

### Narration
```text
How do you check all of this yourself? One command from the repo root, with Python path unset: env dash u Python path, dot venv slash bin slash python, scripts slash replicate dot py. It runs the tests. It regenerates the targets, and checks them byte for byte. It runs the planted pipeline. Then the Foil two check, and the delta menu. Then it copies the paper's figures, writes the paper's result numbers as macros, and builds the PDF when latexmk is available. Last, it compares each result file with the committed one, and prints REPLICATED if they match. Amendment A two adds one more step, for its analysts. Every random draw comes from a named, stable seed, so a rerun reproduces every digit. Where things live. The config folder holds the choices. The source folder holds the kernel, the moments, history matching, the estimands, the foils, and the pipeline. Data holds the targets. Results hold the run outputs, and the paper reads its result numbers through generated macros. Start at the config. Then follow the arrows down.
```

### Visual
A terminal line typed in sans mono-free style: `env -u PYTHONPATH .venv/bin/python scripts/replicate.py`. Nine numbered steps
tick down one by one (tests, z check, planted run, Foil 2 check, δ menu, paper figures, paper
numbers, PDF, report), ending on the word `REPLICATED`. A tenth step slides in dashed: "A2 step
(per the amendment)". Then the repo tree as a top-down flow: `config/` → `src/poc_abm/`
(`kernel.py`, `moments.py`, `history_matching.py`, `estimand.py`, `diagnostic.py`,
`pipeline.py`) → `data/planted.json` and `results/` → the paper's numbers macro file. Closing
title: "Start at config/. Follow the arrows down."

### Sources
| # | Claim | Source |
|---|---|---|
| 10.1 | one command, `scripts/replicate.py` | `scripts/replicate.py:1-5` |
| 10.2 | steps: tests, z check (byte for byte), planted run, Foil 2 check, delta menu, figures, numbers, PDF, report | `scripts/replicate.py:7-16, 100-116` |
| 10.3 | each result file compared with git HEAD; prints REPLICATED when identical | `scripts/replicate.py:72-94` |
| 10.4 | A2 adds its own step (`scripts/interference_tradeoff.py`) | `docs/preregistration-v2.md` A2 (lines 199-200). **Not yet in the code at `d230748`** (the E3 card adds it) |
| 10.5 | every stream has a stable named seed (crc32 of a label and an offset); reruns reproduce every digit | `src/poc_abm/kernel.py:14-21`; `SPECIFICATION.md` §1.4; spine `STATUS.md`, standing rule 4 |
| 10.6 | config/ = exogenous choices | `src/poc_abm/config.py:1-15` |
| 10.7 | source modules: kernel, moments, history matching, estimand, diagnostic (foils), pipeline | `src/poc_abm/` file list; `src/poc_abm/pipeline.py:1-9` |
| 10.8 | data = the targets; results = every number; the paper's numbers are macros generated from results | spine `STATUS.md`, "Where things live"; `scripts/replicate.py:14`; `SPECIFICATION.md` §6 (`write_numbers.py`) |
| — | "Start at the config. Then follow the arrows down." | *framing* |
