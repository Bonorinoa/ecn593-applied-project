# ECN 593 architecture lecture: storyboard

Companion to `video/script.md` (same ten scenes, same order). This file tells the render card (VR)
what to build in Manim: objects, animations, colours and timing. It adds no factual claim; every
claim lives in the script with its source. **No result numbers on screen**, ever: the images,
intervals and verdict examples are drawn as schematic bars with no tick values.

## 0. Global decisions

### 0.1 Background: cream paper (A), not deep ink (B)

Both options were rendered as one still, the same sample frame on each background:
`video/palette-choice.png` (source `video/palette_still.py`, Manim 0.22.0, rendered with
`env -u PYTHONPATH uv run --no-project --exclude-newer "7 days" --with manim manim -s -qh ...`).

**Pick: A, cream paper `#F5EFE3`.** Reasons, from looking at the still:
1. Oxblood stays oxblood. On cream the accent is the true `#6B1E23`. On deep ink the dark theme
   has to lift it to a salmon `#E09A94` to stay legible, and the Kaffeehaus identity is gone.
2. Sand works as a structural colour on cream (rules, boxes, image bars are visible but quiet).
   On deep ink the dark-theme sand `#4B3E34` nearly disappears, so the box C and the image bars
   would need a second accent.
3. It matches the project's other artefacts (the paper and the memos are on cream), so a still
   from the video can sit in a slide or the thesis without re-theming.

Cost of the pick: a cream frame is brighter on a dark screen at night. If Augusto prefers B after
seeing the still, every colour below has a dark twin in the table, so the swap is one dict.

### 0.2 Palette (Kaffeehaus tokens, `strudel-kaffeehaus/design/tokens.css`)

| Role | Token | Cream (picked) | Deep ink (twin) |
|---|---|---|---|
| background | `paper` | `#F5EFE3` | `#181312` |
| card fill, zebra row | `paper-2` | `#ECE2CF` | `#221B18` |
| structure: rules, box C, image bars | `sand` | `#D8C5A2` | `#4B3E34` |
| text | `ink` | `#2B211D` | `#EDE4D3` |
| secondary text | `ink-2` | `#54463E` | `#CDBFAB` |
| captions, rejected points, greyed items | `muted` | `#67584D` | `#A3937F` |
| **the one accent**: seeded people, kept points, c*, intervals, section marks | `ox` | `#6B1E23` | `#E09A94` |
| highlight wash behind a key line | `ox-wash` | `#F1E0DA` | `#351E1E` |

Rule: **one oxblood thing at a time.** Oxblood marks what the narration is talking about now.
When the narration moves on, the old accent fades to `ink` or `muted`. No other hues (no green,
no blue); "good" vs "bad" is carried by words, not colour.

### 0.3 Type and text

- Font: `Helvetica Neue` (sans) for everything, via `Text(..., font="Helvetica Neue")`. Bold for
  titles only. File and code names in the same sans (no monospace font is needed).
- **No `Tex` / `MathTex`** (`dvisvgm` is not installed). Math is `Text` or `MarkupText` with
  Unicode: θ₂ (or θ2), Θ_hm as `Θ<sub>hm</sub>` in `MarkupText`, δ, τ, ≤, ≥, Σ, Λ, β̂, ×, ·, →, ↓, ↑.
- Sizes at 1080p: scene title `font_size=48`, body `36`, labels `30`, captions `28` (floor).
  Verify in the pilot stills that nothing renders under about 28 px.
- At most about 12 words on screen at once. Long labels are split across beats, not shrunk.
- Every scene opens with its section mark: oxblood `§N` + ink bold title, a sand rule under it
  (as in the palette still). The mark sits top-left and stays for the whole scene.

### 0.4 Timing

- Each scene's length is its narration length from `video/build/audio/durations.json`
  (key `seconds`, `s01` … `s10`; total 579.6 s for the Hadley take). Pad with `self.wait`; never
  cut audio.
- The beats below are given as a share of the scene (`@0.30` = 30% into the narration), aligned
  to the sentence that triggers them. They are approximate; adjust to the audio.
- Transitions: `FadeOut` of everything except the background over 0.5 s at the end of a scene;
  the next scene opens on its title with `Write` (0.6 s). No wipes, no zooms over 1 s.

### 0.5 Voice

Three Phonon voices read the same sentence ("History matching keeps every parameter point that the
targets cannot rule out. We call that set N R O Y, and theta two ranges over it."):
Hadley 10.08 s, Everly 9.44 s, Spencer 9.12 s (`video/build/audio/probe/`).

**Pick: Hadley.** It is the slowest of the three on dense technical text, and the most continuous
(the smallest share of silent 20 ms frames: 0.30, against 0.33 and 0.38), which suits a lecture
the listener follows while reading symbols. Its catalogue line, "settled, even-toned, kind", fits
an explainer better than Everly's "soft-edged, relaxed" (the voice already used for the Kaffeehaus
music loop, so the lecture also sounds distinct) or Spencer's "light, airy". Caveat: the pick
rests on these measurements and the catalogue, not on a listening test; the three probe files
are there for Augusto to hear.

---

## Scene 1. The policy question (`s01`)

Objects
- `village`: 800 `Dot`s (radius 0.03, `ink`) on a jittered disc inside a sand `Circle`; a sparse
  set of `Line`s (sand, stroke 1) for edges. It is a picture, not the drawn graph.
- `hubs`: 80 of the dots, chosen as the highest-degree nodes of the picture graph.
- `q_card`: `MarkupText("θ<sub>2</sub>: seed the top 80 vs no campaign")`, body size.
- `sliders`: five short sand `Line`s with oxblood knobs, labels α β γ κ σ.
- `targets`: four small sand bars with ink outline, label "4 targets".
- `theta_axis`: a sand `NumberLine` with **no tick labels**, caption "θ2".

Beats
- @0.00 title `§1 The policy question`; `FadeIn(village)`.
- @0.10 `hubs` turn oxblood (`LaggedStart` of `set_color`, 1.5 s). `Write(q_card)` under the disc.
- @0.35 village shrinks to the left; `sliders` and `targets` appear right; caption "5 parameters,
  4 targets".
- @0.50 three slider settings in turn: the knobs move, the targets light up ("fits"), and each
  drops a tick on `theta_axis` at a different place.
- @0.70 one tick gets the label "best fit" (ink); another gets an oxblood star "truth (c*)". They
  do not coincide.
- @0.85 the three ticks stretch into one sand bar: caption "report the range".

## Scene 2. The world and the design (`s02`)

Objects
- `world_card`, `design_card`: `RoundedRectangle` (paper-2 fill, sand stroke), headers
  `world.toml` / `design.toml`. Rows as `Text` (label size): `n_agents = 800`,
  `edge_rate = 4.0`, `n_covariates = 3`, `horizon = 20`, `param_box C`, `seed_fraction = 0.10`;
  and `monte_carlo reps`, `waves · wave_points`, `delta`, `image theta_sample`, `foils`.
- `config_box`: small card `config.py` with two output lines `EDGE_P = edge_rate / N`,
  `c* = centre of C`.
- `endo_card`: muted-outline card `data/   results/`, caption "endogenous: computed".
- `wall`: a vertical sand `Line` between config and `endo_card`.

Beats
- @0.00 title `§2 The world and the design`; `FadeIn(world_card)`.
- @0.08–0.40 each world row gets an `ox-wash` highlight as the narration names it.
- @0.42 `FadeIn(design_card)`; rows highlighted in turn to @0.65.
- @0.68 both cards labelled "exogenous: chosen before any run".
- @0.75 arrows from both cards into `config_box`; its two rule lines `Write` in.
- @0.88 `wall` draws; `endo_card` appears behind it; caption "never in config".

## Scene 3. The kernel and the three arms (`s03`)

Objects
- `person`: one ink `Dot` (radius 0.12) with 8 neighbour dots on spokes.
- `y_meter`: a vertical sand bar 0 to 1 beside `person`, an oxblood fill level.
- `update`: a row of `Text` tokens: `Y(t+1) = Λ(`, `α`, `+ β·Y(t)`, `+ γ·friends' mean`,
  `+ η·X`, `+ κ·D`, `+ σ·ε`, `)`. Two lines if it exceeds the frame.
- `c_vec`: `Text("c = (α, β, γ, κ, σ)")`; tag `Text("η fixed")` in muted.
- `arms`: three small graph pictures labelled `control`, `random`, `degree`.
- `brace`: sand `Brace` under `arms`, label "same Y(0), same shocks".

Beats
- @0.00 title `§3 The kernel`; a small world picture appears, caption "drawn once".
- @0.12 zoom (0.8 s) into `person` and `y_meter`; meter label "between 0 and 1".
- @0.25 caption "20 steps"; the meter ticks up and down twice.
- @0.32–0.62 `update` tokens fade in one per clause; the token being named is oxblood, the rest ink.
- @0.64 α β γ κ σ fly out of `update` into `c_vec` (`TransformFromCopy`); `η` gets "fixed".
- @0.72 `arms` appear one by one with the narration: none / 80 scattered / 80 on hubs (oxblood).
- @0.90 `brace` grows under all three.

## Scene 4. The estimand θ2 and the pilot (`s04`)

Objects
- `bars`: three vertical sand bars (no values): `control`, `random`, `degree`.
- `theta2_brace`: oxblood bracket between the tops of `degree` and `control`, label
  `MarkupText("θ<sub>2</sub> = E[Ȳ | degree] − E[Ȳ | control]")`.
- `theta1_brace`: ink bracket for `random` vs `control`, label `θ1`.
- `lottery`: a grid of 800 small dots; the 80 hub positions outlined in oxblood.
- `prob`: `Text("P(pilot = degree vector) = 1 / C(800, 80)")`.
- `cards`: two paper-2 cards "exposure map", "transport".

Beats
- @0.00 title `§4 The estimand θ2`; `bars` grow from 0 (heights schematic).
- @0.12 `theta2_brace` and its label; caption "200 paired reps per arm".
- @0.25 `theta1_brace`; caption under it "a pilot identifies θ1".
- @0.42 bars fade; `lottery` appears; four rapid random 80-dot draws flash oxblood (0.4 s each),
  none matching the outlined hub set.
- @0.60 `Write(prob)`; caption "no pilot ever realizes the policy".
- @0.75 `cards` slide in left and right; each gets a one-line caption as the narration defines
  it: "outcome depends on a simple summary (e.g. treated friends)" and "pilot's exposure effects
  hold under the policy".

## Scene 5. The targets z (`s05`)

Objects
- `obs`: two icons: a village at rest ("status quo"), and the village with scattered oxblood
  ("one random pilot"). A third, greyed (muted, 40% opacity) with hubs: "degree policy: never
  observed".
- `table`: four rows on a paper-2 card with sand zebra: `sq_level · control`,
  `sq_corr_x1 · control`, `sq_peer_corr · control`, `pilot_level · random`.
- `flow1`: `Text("c → M(c)")`, caption "30 paired reps".
- `flow2`: `Text("c* → z = M̂(c*)")`, caption "200 reps", into a file card `data/planted.json`.
- `star`: oxblood star at the centre of a small sand box C.

Beats
- @0.00 title `§5 The targets z`; `obs` appear; the third greys out.
- @0.20 `table` rows `FadeIn` one by one with the narration.
- @0.55 `flow1` writes; @0.68 `flow2` writes; the file card appears.
- @0.80 `star` in box C; caption "planted: the truth is known".

## Scene 6. History matching (`s06`)

Objects
- `I_formula`: `Text("I(c) = Σ (z − M(c))² / V")`.
- `V_formula`: `MarkupText("V = σ²<sub>z</sub> + σ²<sub>MC</sub>(c) + δ²")`, with `δ²` in oxblood.
- `delta_row`: `Text("δ: 0.02 levels · 0.05 correlations")`.
- `tau_line`: horizontal oxblood dashed line labelled `τ`, caption "χ² 95%, 4 df · a tolerance,
  not a test".
- `box`: sand `Rectangle` (a 2-D slice of C, labelled "C (5 dims, shown as 2)").
- `wave_dots`: grey (`muted`) dots in the box; kept ones switch to oxblood.
- `bbox`: dashed ink rectangle around the kept dots.
- `nroy`: all kept dots merge into a cluster with label `NROY`.
- `empty_card`: caption card "no point kept → F-EMPTY · τ never loosened".

Beats
- @0.00 title `§6 History matching`; `Write(I_formula)`.
- @0.12 `Write(V_formula)`; the three terms highlight in turn; δ² stays oxblood.
- @0.30 `delta_row`.
- @0.40 formulas shrink to the top; `tau_line` appears beside a vertical I axis.
- @0.52 `box` appears; wave 1: 60 representative dots fade in (`LaggedStart`, 1 s); those under
  τ turn oxblood. Caption "wave 1 of 3 · 1000 points" (the dots are a picture of the 1000).
- @0.64 `bbox` snaps around the kept dots, then widens ("+20%"); wave 2 dots fill it; repeat for
  wave 3 (faster).
- @0.78 caption "no emulator: every point simulated".
- @0.84 kept dots of all waves gather into `nroy` with label "NROY: not ruled out yet".
- @0.93 `empty_card` fades in at the bottom.

## Scene 7. The images (`s07`)

Objects
- `nroy`: the cluster from scene 6 (rebuilt), 400 of its dots outlined (picture of the sample).
- `axis_hm`: sand `NumberLine`, no tick labels, caption "θ2".
- `bar_hm`: sand bar spanning the leftmost to the rightmost tick, `MarkupText("Θ<sub>hm</sub> = [min, max]")`.
- `axis_exp`, `bar_exp`: same for `δ_spill` → `Θ<sub>exp</sub>`.
- `strata`: a small inset graph: one untreated node with friends; labels `S1 seeded`,
  `S0a no treated friend`, `S0c ≥ 1/4 friends treated`.
- `not_card`: two struck-out words: "posterior", "identified set".
- `recheck`: the two end ticks flash; replaced by ticks labelled "fresh reps".
- `menu`: three stacked sand bars labelled `δ_level = 0.02`, `0.01`, `0.005` and "A1 menu".
  **Schematic widths, no endpoint values.**

Beats
- @0.00 title `§7 The images`; `nroy` with the 400 outlined.
- @0.12 each outlined dot drops a tick to `axis_hm` (`LaggedStart`, 1.5 s); caption "200 reps each".
- @0.28 `bar_hm` grows between the extreme ticks.
- @0.36 `strata` inset; @0.48 `axis_exp`, `bar_exp`.
- @0.58 `not_card`: "an image is not a posterior · not an identified set".
- @0.70 `recheck`.
- @0.82 `menu` stacks under `bar_hm`; caption "a menu, never a way to choose δ".

## Scene 8. The analysts and the A2 ladder (`s08`)

Objects
- `pins`: on the `nroy` cluster, two sand pins `min-I`, `median-I` with the caption "the
  calibrator · chosen by I only"; an oxblood star `c*` with "the field experimenter".
- `foil1`: card: mini degree-arm graph → `Text("OLS → β̂")` → `Text("× k/N")` → interval bracket.
  Footnote "HC1 interval". A side note: "= θ2 only if no interference".
- `foil2`: card: mini random-arm graph with strata colouring (ink / sand / muted, S1 oxblood) →
  `Text("Hájek · Aronow–Samii")` → bracket labelled `δ_spill`. Note "targets δ_spill, not θ2".
- `ladder`: three rungs, top to bottom: `A0 = Foil 1 · SUTVA`, `A1 · exposure transport`,
  `A2 · degree-binned (H = top 80, L = rest)`. A muted arrow on the side "fewer assumptions ↓".
- `name_box`: oxblood-outlined small card "amendment A1 = δ menu  ≠  analyst A1".
- `expect`: two arrows beside the ladder "|bias| ↓" and "width ↑", tag in muted italics
  "pre-registered expectation, not a result".

Beats
- @0.00 title `§8 The analysts`; caption "one panel → one interval".
- @0.08 `pins` appear in narration order.
- @0.25 `foil1` builds left to right; @0.38 the side note.
- @0.45 `foil2` builds; @0.55 its note.
- @0.60 foils shrink to the top; `ladder` draws rung by rung.
- @0.64 `name_box` pops in beside rung A1, holds 3 s, fades.
- @0.70–0.85 each rung highlights (ox-wash) as the narration reaches it; A2's rung shows the H/L
  split as two half-cells.
- @0.88 `expect` arrows and tag.

## Scene 9. Interval geometry and the two layers (`s09`)

Objects
- `image_bar`: wide sand bar labelled `Θ` (schematic).
- `brackets`: three oxblood interval brackets below it: one wider than the bar (`F-HONEST`), one
  strictly inside (`F-OVERCONF`), one crossing an end (`no verdict`).
- `rule_text`: `Text("F-HONEST: covers the image")`, `Text("F-OVERCONF: strictly inside")`.
- `ticks`: two vertical ticks on the axis: `θ2(c)` (ink) and `θ2(c*)` (oxblood star).
- `layers`: two labels "(a) own point: right about its own world?" and "(b) c*: right about the
  village?".
- `split`: two columns "one panel → contains / not" | "many panels → coverage", the second with
  sub-captions "Foil 2 calibration check" and "A2: 200 panels, Clopper–Pearson".

Beats
- @0.00 title `§9 Judging an interval`; `image_bar`; caption "Foil 1 vs Θ_hm · Foil 2 vs Θ_exp".
- @0.15 the three `brackets` appear one at a time with their labels.
- @0.45 brackets fade except the inside one; `ticks` appear; `layers` (a) then (b).
- @0.65 the two ticks slide together; caption "at c*, (a) = (b)".
- @0.75 `split` columns.

## Scene 10. One command, and where things live (`s10`)

Objects
- `cmd`: paper-2 strip with `Text("python scripts/replicate.py")`.
- `steps`: nine rows `1 tests`, `2 z check (byte for byte)`, `3 planted run`, `4 Foil 2 check`,
  `5 δ menu`, `6 paper figures`, `7 paper numbers`, `8 PDF`, `9 report`, each with a check mark
  that turns oxblood when named. Final word `REPLICATED` in oxblood bold.
- `a2_row`: dashed sand row "+ A2 step (per the amendment)".
- `tree`: top-down flow of cards: `config/` → `src/poc_abm/` (six module names, two columns) →
  `data/planted.json` · `results/` → `paper numbers (macros)`. Sand arrows.
- `seed_note`: caption "named, stable seeds → the same digits on every rerun".

Beats
- @0.00 title `§10 Replicate it`; `Write(cmd)`.
- @0.08–0.55 `steps` tick in order with the narration; `REPLICATED` at @0.55.
- @0.58 `a2_row`. @0.63 `seed_note`.
- @0.68 steps fade; `tree` builds top-down, one level per sentence.
- @0.95 closing line under the tree: "Start at config/. Follow the arrows down."
