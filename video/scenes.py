"""ECN 593 architecture lecture: one Manim scene per script scene (video/script.md).

Timing: each scene lasts its narration length (build/audio/durations.json) plus a short tail.
Beats are cued to sentences: `self.cue("phrase")` waits until the phrase is spoken, using the
narration-to-wav time map of timing.py (anchored at the pauses between sentences).
Animations never shorten a scene; `finish()` pads with `self.wait` so the audio is never cut.

Palette: Kaffeehaus cream (storyboard section 0.2). One oxblood thing at a time.
Text: Helvetica Neue only, no Tex. Font sizes 48 / 36 / 30 / 28 (floor 28).
No result numbers on screen: images, intervals and verdicts are schematic, without values.

Render one scene:  env -u PYTHONPATH uv run --project video manim -ql video/scenes.py S01Question
Render everything: env -u PYTHONPATH uv run --project video python video/render.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from timing import anchors, char_time  # noqa: E402
from manim import (BOLD, DL, DOWN, ITALIC, LEFT, NORMAL, ORIGIN, RIGHT, UL, UP, Arrow,
                   Brace, Circle, Create, DashedLine, DashedVMobject, Dot, FadeIn, FadeOut,
                   GrowFromCenter, GrowFromEdge, Indicate, LaggedStart, Line, MarkupText,
                   Rectangle, RoundedRectangle, Scene, Star, Text, Transform,
                   TransformFromCopy, Triangle, VGroup, Write, config)

HERE = Path(__file__).resolve().parent
DUR = json.loads((HERE / "build" / "audio" / "durations.json").read_text())["seconds"]
NARR = {k: (HERE / "narration" / f"{k}.txt").read_text().strip() for k in DUR}

# Kaffeehaus cream palette (storyboard 0.2)
PAPER, PAPER2, SAND = "#F5EFE3", "#ECE2CF", "#D8C5A2"
INK, INK2, MUTED = "#2B211D", "#54463E", "#67584D"
OX, WASH = "#6B1E23", "#F1E0DA"
SANS = "Helvetica Neue"
TITLE, BODY, LABEL, CAP = 48, 36, 30, 28
TAIL = 0.4  # seconds of picture after the last word, before the fade


# ---------------------------------------------------------------- text and shapes
def T(s, size=BODY, color=INK, bold=False, italic=False):
    return Text(s, font=SANS, font_size=size, color=color,
                weight=BOLD if bold else NORMAL, slant=ITALIC if italic else NORMAL)


def M(s, size=BODY, color=INK, bold=False):
    """MarkupText, for coloured spans only. Never <sub>: use sub() (Pango subscripts render
    under the 28 px floor in Manim)."""
    return MarkupText(s, font=SANS, font_size=size, color=color, weight=BOLD if bold else NORMAL)


def sub(base, s, size=BODY, color=INK):
    """Base symbol with a subscript (Pango <sub> renders far too small in Manim, so it is
    built by hand). The subscript never goes under the 28 px floor."""
    b = T(base, size, color)
    t = T(s, max(CAP, round(size * 0.78)), color)
    t.next_to(b, RIGHT, buff=0.04).align_to(b, DOWN).shift(DOWN * 0.13)
    g = VGroup(b, t)
    g.base = b
    return g


def inline(*items, buff=0.14):
    """Lay text pieces in a row, vertically centred on the first piece's base glyphs."""
    g = VGroup(*items).arrange(RIGHT, buff=buff)
    y = getattr(items[0], "base", items[0]).get_y()
    for it in items[1:]:
        it.shift(UP * (y - getattr(it, "base", it).get_y()))
    return g


def card(w, h, fill=PAPER2, stroke=SAND, sw=3):
    return RoundedRectangle(width=w, height=h, corner_radius=0.15, stroke_color=stroke,
                            stroke_width=sw, fill_color=fill, fill_opacity=1)


def labelled_card(text, w=None, h=0.9, size=LABEL, color=INK, pad=0.5, bold=False):
    t = T(text, size, color, bold=bold)
    c = card(w or t.width + pad, h)
    t.move_to(c)
    return VGroup(c, t)


def bracket(x0, x1, y, color=OX, w=6, cap=0.18):
    return VGroup(Line([x0, y, 0], [x1, y, 0]), Line([x0, y - cap, 0], [x0, y + cap, 0]),
                  Line([x1, y - cap, 0], [x1, y + cap, 0])).set_stroke(color, w)


def graph_picture(n, radius, seed, n_edges, dot_r, edge_w=1.0, edge_op=0.8, ring=True):
    """A picture of a friendship graph (not the drawn graph): dots on a disc, edges to near
    neighbours with heterogeneous activity, so a few dots are hubs. Returns (group, order)
    where group = [ring, edges, dots] and order lists dot indices by degree, highest first."""
    rng = np.random.default_rng(seed)
    r = radius * np.sqrt(rng.random(n))
    a = 2 * np.pi * rng.random(n)
    pts = np.c_[r * np.cos(a), r * np.sin(a), np.zeros(n)]
    w = rng.pareto(1.6, n) + 1.0
    d = np.linalg.norm(pts[:, None, :2] - pts[None, :, :2], axis=2)
    near = np.argsort(d, axis=1)[:, 1:13]
    deg = np.zeros(n, int)
    seen, edges = set(), []
    p = w / w.sum()
    while len(edges) < n_edges:
        i = int(rng.choice(n, p=p))
        cand = near[i]
        j = int(rng.choice(cand, p=w[cand] / w[cand].sum()))
        key = (min(i, j), max(i, j))
        if key in seen:
            continue
        seen.add(key)
        edges.append(key)
        deg[i] += 1
        deg[j] += 1
    lines = VGroup(*[Line(pts[i], pts[j], stroke_width=edge_w, color=SAND,
                          stroke_opacity=edge_op) for i, j in edges])
    dots = VGroup(*[Dot(pts[i], radius=dot_r, color=INK) for i in range(n)])
    order = list(np.argsort(-deg, kind="stable"))
    parts = [lines, dots]
    rim = Circle(radius=radius * 1.08, color=SAND, stroke_width=3) if ring else VGroup()
    return VGroup(rim, *parts), order


def mini_graph(mode, seed=11, n=40, k=6, radius=0.95):
    g, order = graph_picture(n, radius, seed, n_edges=55, dot_r=0.055, edge_w=1.5)
    if mode == "random":
        pick = np.random.default_rng(seed + 1).choice(n, k, replace=False)
    elif mode == "degree":
        pick = order[:k]
    else:
        pick = []
    for i in pick:
        g[2][i].set_color(OX).scale(1.5)
    return g


def nroy_cloud(center, n=110, rx=1.6, ry=0.9, seed=5, color=INK, r=0.045):
    rng = np.random.default_rng(seed)
    rr = np.sqrt(rng.random(n))
    a = 2 * np.pi * rng.random(n)
    x, y = rx * rr * np.cos(a), ry * rr * np.sin(a)
    rot = 0.35
    xs, ys = x * np.cos(rot) - y * np.sin(rot), x * np.sin(rot) + y * np.cos(rot)
    return VGroup(*[Dot([center[0] + xs[i], center[1] + ys[i], 0], radius=r, color=color)
                    for i in range(n)])


# ---------------------------------------------------------------- base scene
class Lecture(Scene):
    key = ""
    mark = ""
    title = ""

    def setup(self):
        self.camera.background_color = PAPER
        self.D = DUR[self.key]
        self.text = NARR[self.key]
        self.anchors = anchors(self.text, self.D, HERE / "build" / "audio" / f"{self.key}.wav")
        self.cap = None

    def now(self):
        return self.renderer.time

    def cue(self, phrase, offset=0.0):
        i = self.text.find(phrase)
        assert i >= 0, f"{self.key}: cue phrase not in narration: {phrase!r}"
        dt = char_time(self.anchors, i) + offset - self.now()
        if dt > 0.02:
            self.wait(dt)

    def header(self):
        m = T(self.mark, TITLE, OX, bold=True)
        h = T(self.title, TITLE, INK, bold=True)
        g = VGroup(m, h).arrange(RIGHT, buff=0.3, aligned_edge=UP).to_corner(UL, buff=0.45)
        rule = Line(LEFT, RIGHT, color=SAND, stroke_width=3)
        rule.set_width(config.frame_width - 0.9).next_to(g, DOWN, buff=0.2)
        rule.align_to(g, LEFT)
        self.play(Write(g), Create(rule), run_time=0.6)
        self.head = VGroup(g, rule)

    def caption(self, s, size=LABEL, color=MUTED, markup=False, rt=0.5):
        new = s if not isinstance(s, str) else (M(s, max(size, 36), color) if markup else T(s, size, color))
        new.to_edge(DOWN, buff=0.4)
        if self.cap is not None:  # out, then in: two captions never overlap
            self.play(FadeOut(self.cap), run_time=0.2)
        self.play(FadeIn(new, shift=UP * 0.1), run_time=max(rt - 0.2, 0.25))
        self.cap = new

    def drop_caption(self, rt=0.4):
        if self.cap is not None:
            self.play(FadeOut(self.cap), run_time=rt)
            self.cap = None

    def push_row(self, rows, mob, anchor, visible=3, gap=0.62, rt=0.5):
        """Scrolling list: the newest row is oxblood, older rows ink; at most `visible`."""
        if len(rows) >= visible:  # scroll first, then add: rows never overlap
            self.play(FadeOut(rows.pop(0), shift=UP * 0.3),
                      *[r.animate.shift(UP * gap) for r in rows], run_time=rt * 0.6)
        mob.set_color(OX)
        mob.move_to(np.array(anchor) + DOWN * gap * len(rows), aligned_edge=LEFT)
        anims = [FadeIn(mob, shift=UP * 0.15)]
        if rows:
            anims.append(rows[-1].animate.set_color(INK))
        self.play(*anims, run_time=rt)
        rows.append(mob)

    def finish(self):
        dt = self.D + TAIL - 0.5 - self.now()
        if dt > 0:
            self.wait(dt)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5)


# ---------------------------------------------------------------- scene 1
class S01Question(Lecture):
    key, mark, title = "s01", "§1", "The policy question"

    def construct(self):
        self.header()
        village, order = graph_picture(800, 2.25, seed=7, n_edges=900, dot_r=0.028,
                                       edge_w=0.8, edge_op=0.7)
        village.move_to(DOWN * 0.45)
        self.play(FadeIn(village), run_time=1.0)
        self.caption("a village of 800 people")

        self.cue("A campaign can seed")
        dots = village[2]
        hubs = order[:80]
        self.play(LaggedStart(*[dots[i].animate.set_color(OX).scale(1.7) for i in hubs],
                              lag_ratio=0.03), run_time=1.6)
        self.caption("seed the 80 best-connected")

        self.cue("We call that number")
        self.play(village.animate.shift(LEFT * 3.0), run_time=0.7)
        q = VGroup(T("θ2: seed the top 80", BODY), T("vs no campaign", BODY, INK2))
        q.arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to([3.4, -0.2, 0])
        self.play(Write(q), FadeOut(self.cap), run_time=1.0)
        self.cap = None

        self.cue("In this design")
        self.caption("no data from the degree policy")

        self.cue("So we build a model")
        self.play(FadeOut(q), village.animate.scale(0.55).move_to([-5.0, 0.3, 0]), run_time=0.8)
        # sliders: five parameters
        sliders, knobs = VGroup(), []
        for i, g in enumerate("αβγκσ"):
            y = 1.6 - i * 0.62
            lab = T(g, LABEL).move_to([-2.2, y, 0])
            track = Line([-1.8, y, 0], [0.4, y, 0], color=SAND, stroke_width=5)
            knob = Dot([-0.7, y, 0], radius=0.11, color=OX)
            knobs.append(knob)
            sliders.add(VGroup(lab, track, knob))
        # targets: four bars with target marks
        bars, marks = VGroup(), VGroup()
        heights = [1.3, 0.8, 1.6, 1.1]
        for i, h in enumerate(heights):
            x = 2.0 + i * 0.75
            bar = Rectangle(width=0.45, height=0.3, fill_color=SAND, fill_opacity=1,
                            stroke_width=0).move_to([x, -0.9 + 0.15, 0])
            bars.add(bar)
            marks.add(Line([x - 0.32, -0.9 + h, 0], [x + 0.32, -0.9 + h, 0], color=INK,
                           stroke_width=4))
        base = Line([1.6, -0.9, 0], [4.6, -0.9, 0], color=INK2, stroke_width=2)
        self.play(FadeIn(sliders), FadeIn(bars), FadeIn(marks), Create(base), run_time=0.8)

        self.cue("The model has five")
        self.caption("5 parameters, 4 targets")

        self.cue("Many parameter points")
        axis = Line([-2.4, -2.45, 0], [5.0, -2.45, 0], color=SAND, stroke_width=4)
        ax_lab = T("θ2", LABEL).next_to(axis, RIGHT, buff=0.2)
        self.play(Create(axis), FadeIn(ax_lab), run_time=0.5)
        settings = [[-1.4, 0.1, -0.2, -1.2, 0.2], [0.2, -1.5, 0.3, -0.3, -1.0],
                    [-0.4, -0.6, -1.6, 0.3, -0.1]]
        tick_x = [-1.2, 3.8, 1.5]
        ticks = VGroup()
        for s, tx in zip(settings, tick_x):
            fit = [bar.animate.stretch_to_fit_height(h * 0.97 + 0.01).move_to(
                [bar.get_x(), -0.9 + (h * 0.97 + 0.01) / 2, 0]) for bar, h in zip(bars, heights)]
            self.play(*[k.animate.set_x(x) for k, x in zip(knobs, s)], *fit, run_time=0.8)
            tick = Line([tx, -2.75, 0], [tx, -2.15, 0], color=INK, stroke_width=5)
            ticks.add(tick)
            self.play(Create(tick), Indicate(marks, color=INK2, scale_factor=1.05), run_time=0.6)
            for bar in bars:
                bar.stretch_to_fit_height(0.3).move_to([bar.get_x(), -0.9 + 0.15, 0])
        self.caption("all fit about equally; θ2 differs")

        self.cue("And the best-fitting point")
        best = T("best fit", LABEL).next_to(ticks[0], UP, buff=0.15)
        star = Star(n=5, outer_radius=0.17, color=OX, fill_opacity=1).next_to(ticks[2], UP, buff=0.12)
        truth = T("truth (c*)", LABEL, OX).next_to(star, RIGHT, buff=0.12)
        self.play(FadeIn(best), run_time=0.5)
        self.play(GrowFromCenter(star), FadeIn(truth), run_time=0.6)

        self.cue("So one calibrated point")
        self.caption("one calibrated point: confident, and wrong")

        self.cue("This project reports")
        span = Rectangle(width=tick_x[1] - tick_x[0], height=0.3, fill_color=SAND,
                         fill_opacity=1, stroke_width=0).move_to([(tick_x[0] + tick_x[1]) / 2, -2.45, 0])
        self.play(FadeOut(best), FadeOut(truth), FadeOut(star), FadeIn(span), ticks.animate.set_color(INK2),
                  run_time=0.8)
        self.caption("report the range the data cannot rule out")

        self.cue("Then it asks")
        self.caption("then: which analysts are honest about it?")
        self.finish()


# ---------------------------------------------------------------- scene 2
class S02Config(Lecture):
    key, mark, title = "s02", "§2", "World and design"

    def construct(self):
        self.header()
        wc = card(5.8, 3.6).move_to([-3.4, -0.2, 0])
        wh = T("config/world.toml", LABEL, INK, bold=True).next_to(wc.get_top(), DOWN, buff=0.3)
        dc = card(5.8, 3.6).move_to([3.4, -0.2, 0])
        dh = T("config/design.toml", LABEL, INK, bold=True).next_to(dc.get_top(), DOWN, buff=0.3)
        self.play(FadeIn(wc), Write(wh), run_time=0.8)

        self.cue("It holds the village")
        self.caption("the village and the policy question")
        rows = []
        anchor = wc.get_left() + RIGHT * 0.5 + UP * 0.55
        for phrase, txt in [("Eight hundred people", "800 people"),
                            ("A random friendship", "random graph, ~8 friends"),
                            ("Three covariates", "3 covariates"),
                            ("Twenty time steps", "20 time steps"),
                            ("The box C", "box C of parameters"),
                            ("And the seed share", "seed share 10%")]:
            self.cue(phrase)
            self.push_row(rows, T(txt, LABEL), anchor)

        small_w = labelled_card("world.toml", w=3.2, h=0.85).move_to([-5.0, 1.5, 0])
        small_d = labelled_card("design.toml", w=3.2, h=0.85).move_to([-1.2, 1.5, 0])
        self.cue("The second file")
        self.play(*[FadeOut(r) for r in rows], Transform(VGroup(wc, wh), small_w), run_time=0.7)
        self.play(FadeIn(dc), Write(dh), run_time=0.6)
        self.caption("the analyst's choices")
        rows2 = []
        anchor2 = dc.get_left() + RIGHT * 0.5 + UP * 0.55
        for phrase, txt in [("How many Monte Carlo", "Monte Carlo reps"),
                            ("How many waves", "waves of search"),
                            ("The allowances for model", "δ: model-error allowance"),
                            ("And the settings of both", "foil settings")]:
            self.cue(phrase)
            self.push_row(rows2, T(txt, LABEL), anchor2)

        self.cue("Both files are exogenous")
        self.play(*[FadeOut(r) for r in rows2], Transform(VGroup(dc, dh), small_d), run_time=0.9)
        self.caption("exogenous: chosen before any run")

        self.cue("The code only reads them")
        cfg = card(5.0, 2.1).move_to([-3.1, -1.1, 0])
        cfg_t = T("config.py", LABEL, INK, bold=True).next_to(cfg.get_top(), DOWN, buff=0.22)
        a1 = Arrow([-5.0, 1.05, 0], [-3.9, -0.02, 0], color=SAND, stroke_width=5, buff=0.05)
        a2 = Arrow([-1.2, 1.05, 0], [-2.3, -0.02, 0], color=SAND, stroke_width=5, buff=0.05)
        self.play(FadeIn(cfg), Write(cfg_t), Create(a1), Create(a2), run_time=0.8)

        self.cue("and adds two rules")
        r1 = T("EDGE_P = edge_rate / N", LABEL).next_to(cfg_t, DOWN, buff=0.28)
        r2 = T("c* = centre of C", LABEL, OX).next_to(r1, DOWN, buff=0.2)
        self.play(Write(r1), run_time=0.7)
        self.cue("and the planted point")
        self.play(Write(r2), run_time=0.7)

        self.cue("The endogenous quantities")
        wall = Line([1.6, 2.1, 0], [1.6, -2.7, 0], color=SAND, stroke_width=8)
        endo = card(4.8, 2.3, fill=PAPER, stroke=MUTED).move_to([4.45, -0.3, 0])
        endo_t = T("data/   results/", BODY, INK, bold=True).move_to(endo).shift(UP * 0.35)
        endo_c = T("endogenous: computed", CAP, MUTED).next_to(endo_t, DOWN, buff=0.3)
        self.play(Create(wall), run_time=0.5)
        self.play(FadeIn(endo), Write(endo_t), FadeIn(endo_c), run_time=0.8)
        self.caption("never in config")
        self.finish()


# ---------------------------------------------------------------- scene 3
class S03Kernel(Lecture):
    key, mark, title = "s03", "§3", "The kernel"

    def construct(self):
        self.header()
        world, _ = graph_picture(300, 1.9, seed=3, n_edges=380, dot_r=0.035, edge_w=0.9)
        world.move_to(DOWN * 0.4)
        self.play(FadeIn(world), run_time=0.8)
        self.caption("drawn once: one graph, fixed seeds")

        self.cue("Each person has an outcome")
        person = Dot([-3.2, -0.3, 0], radius=0.16, color=INK)
        spokes, nbrs = VGroup(), VGroup()
        for i in range(8):
            ang = 2 * np.pi * i / 8 + 0.2
            p = person.get_center() + 1.5 * np.array([np.cos(ang), np.sin(ang), 0])
            spokes.add(Line(person.get_center(), p, color=SAND, stroke_width=3))
            nbrs.add(Dot(p, radius=0.09, color=INK2))
        meter = Rectangle(width=0.5, height=3.2, stroke_color=SAND, stroke_width=4).move_to([0.6, -0.3, 0])
        level = Rectangle(width=0.5, height=1.2, fill_color=OX, fill_opacity=1, stroke_width=0)
        level.align_to(meter, DOWN).align_to(meter, LEFT)
        lo = T("0", LABEL, MUTED).next_to(meter, DOWN, buff=0.15)
        hi = T("1", LABEL, MUTED).next_to(meter, UP, buff=0.15)
        self.play(FadeOut(world), run_time=0.5)
        self.play(FadeIn(spokes), FadeIn(nbrs), GrowFromCenter(person), FadeIn(meter),
                  GrowFromEdge(level, DOWN), FadeIn(lo), FadeIn(hi), run_time=0.9)
        self.caption("an outcome between 0 and 1")

        self.cue("At each of twenty steps")
        self.caption("updated at each of 20 steps")
        for h in (2.2, 0.9, 2.6, 1.8):
            self.play(level.animate.stretch_to_fit_height(h).align_to(meter, DOWN), run_time=0.45)

        self.cue("The new value is a logistic")
        self.play(*[FadeOut(m) for m in (person, spokes, nbrs, meter, level, lo, hi)],
                  run_time=0.5)
        self.drop_caption()
        l1 = ["Y(t+1) = Λ(", "α", "+ β·Y(t)", "+ γ·friends' mean"]
        l2 = ["+ η·X", "+ κ·D", "+ σ·ε", ")"]
        t1 = VGroup(*[T(s, BODY) for s in l1]).arrange(RIGHT, buff=0.22)
        t2 = VGroup(*[T(s, BODY) for s in l2]).arrange(RIGHT, buff=0.22)
        VGroup(t1, t2).arrange(DOWN, buff=0.45, aligned_edge=LEFT).move_to(UP * 0.7)
        t2.shift(RIGHT * 1.2)
        tokens = list(t1) + list(t2)
        self.play(FadeIn(tokens[0]), run_time=0.5)
        cues = [("A baseline, alpha", 1), ("Your own last outcome", 2),
                ("The average of your friends", 3), ("Your covariates", 4),
                ("If you were seeded", 5), ("And noise", 6)]
        prev = None
        for phrase, idx in cues:
            self.cue(phrase)
            anims = [FadeIn(tokens[idx].set_color(OX), shift=UP * 0.1)]
            if prev is not None:
                anims.append(tokens[prev].animate.set_color(INK))
            if idx == 6:
                anims.append(FadeIn(tokens[7]))
            self.play(*anims, run_time=0.45)
            prev = idx
            if idx == 4:
                fixed = T("fixed", CAP, MUTED, italic=True).next_to(tokens[4], DOWN, buff=0.15)
                self.play(FadeIn(fixed), run_time=0.3)

        self.cue("Alpha, beta, gamma")
        cvec = T("c = (α, β, γ, κ, σ)", BODY, OX).move_to(DOWN * 1.6)
        self.play(tokens[6].animate.set_color(INK),
                  TransformFromCopy(VGroup(tokens[1], tokens[2], tokens[3], tokens[5], tokens[6]), cvec),
                  run_time=1.0)
        self.caption("the five parameters c")

        self.cue("Now the arms")
        self.play(*[FadeOut(m) for m in tokens], FadeOut(fixed), FadeOut(cvec), run_time=0.5)
        self.drop_caption()
        arms, names = [], [("control", "none"), ("random", "random"), ("degree", "degree")]
        for i, ((name, mode), phrase) in enumerate(zip(names, ["The control arm", "The random arm",
                                                               "The degree arm"])):
            self.cue(phrase)
            g = mini_graph(mode, seed=21).move_to([-4.2 + 4.2 * i, 0.3, 0])
            lab = T(name, LABEL).next_to(g, DOWN, buff=0.25)
            self.play(FadeIn(g), FadeIn(lab), run_time=0.6)
            arms.append(VGroup(g, lab))
            what = {"none": "seeds no one", "random": "80 at random",
                    "degree": "80 with most friends"}[mode]
            self.caption(what)

        self.cue("In each rep")
        allarms = VGroup(*arms)
        brace = Brace(allarms, DOWN, color=SAND, buff=0.2)
        btxt = T("same Y(0), same shocks", LABEL, INK).next_to(brace, DOWN, buff=0.15)
        self.play(GrowFromCenter(brace), FadeIn(btxt), run_time=0.7)
        self.drop_caption()

        self.cue("So a difference between arms")
        self.caption("a difference between arms is the policy")
        self.finish()


# ---------------------------------------------------------------- scene 4
class S04Estimand(Lecture):
    key, mark, title = "s04", "§4", "The estimand θ2"

    def construct(self):
        self.header()
        base_y = -2.0
        spec = [("control", 1.3, -5.0), ("random", 2.0, -3.3), ("degree", 2.9, -1.6)]
        bars, labs = VGroup(), VGroup()
        for name, h, x in spec:
            b = Rectangle(width=1.1, height=h, fill_color=SAND, fill_opacity=1, stroke_width=0)
            b.move_to([x, base_y + h / 2, 0])
            bars.add(b)
            labs.add(T(name, LABEL).next_to(b, DOWN, buff=0.2))
        self.play(*[GrowFromEdge(b, DOWN) for b in bars], FadeIn(labs), run_time=1.0)
        self.caption("run each arm many times; average the village")

        self.cue("Theta two is the difference")
        top_c, top_d = base_y + 1.3, base_y + 2.9
        g1 = DashedLine([-5.55, top_c, 0], [-0.6, top_c, 0], color=INK2, stroke_width=2)
        br2 = VGroup(Line([-0.6, top_c, 0], [-0.6, top_d, 0]),
                     Line([-0.75, top_c, 0], [-0.45, top_c, 0]),
                     Line([-0.75, top_d, 0], [-0.45, top_d, 0])).set_stroke(OX, 6)
        l2 = T("θ2 = E[Ȳ | degree] − E[Ȳ | control]", LABEL, OX).next_to(br2, RIGHT, buff=0.3)
        self.play(Create(g1), Create(br2), Write(l2), run_time=1.0)

        self.cue("Theta one is the same")
        top_r = base_y + 2.0
        br1 = VGroup(Line([-2.55, top_c, 0], [-2.55, top_r, 0]),
                     Line([-2.68, top_r, 0], [-2.42, top_r, 0])).set_stroke(INK, 5)
        l1 = T("θ1: random vs control", LABEL, INK).move_to([1.6, top_r - 0.65, 0], aligned_edge=LEFT)
        l1.align_to(l2, LEFT)
        self.play(Create(br1), FadeIn(l1), l2.animate.set_color(INK), br2.animate.set_stroke(INK),
                  run_time=0.7)

        self.cue("The code uses two hundred")
        self.caption("200 paired reps per arm")

        self.cue("That pilot identifies")
        self.play(br1.animate.set_stroke(OX), l1.animate.set_color(OX), run_time=0.4)
        self.caption("a randomized pilot identifies θ1")

        self.cue("But theta two compares")
        self.play(*[FadeOut(m) for m in (bars, labs, g1, br2, l2, br1, l1)], run_time=0.6)
        self.caption("θ2: two whole assignment vectors")

        self.cue("A random pilot draws")
        rng = np.random.default_rng(4)
        grid = VGroup(*[Dot([-4.3 + c * 0.22, 2.1 - r * 0.2, 0], radius=0.05, color=MUTED)
                        for r in range(20) for c in range(40)])
        hub_idx = rng.choice(800, 80, replace=False)
        rings = VGroup(*[Circle(radius=0.085, color=INK, stroke_width=2).move_to(grid[i])
                         for i in hub_idx])
        self.play(FadeIn(grid), run_time=0.6)
        self.play(Create(rings), run_time=0.6)
        self.caption("rings: the top 80 · draws: random pilots")
        for _ in range(4):
            pick = rng.choice(800, 80, replace=False)
            self.play(*[grid[i].animate.set_color(OX).scale(1.4) for i in pick], run_time=0.2)
            self.wait(0.3)
            self.play(*[grid[i].animate.set_color(MUTED).scale(1 / 1.4) for i in pick], run_time=0.2)

        self.cue("The chance that it draws")
        prob = T("P(pilot = degree vector) = 1 / C(800, 80)", BODY, INK).move_to(DOWN * 2.45)
        self.drop_caption()
        self.play(Write(prob), run_time=1.0)

        self.cue("A randomized pilot therefore")
        self.caption("negligible probability, not zero")

        self.cue("To get from a pilot")
        self.play(FadeOut(grid), FadeOut(rings), FadeOut(prob), run_time=0.5)
        self.caption("two assumptions")
        c1 = labelled_card("exposure map", w=5.4, h=1.0, size=BODY).move_to([-3.4, 0.9, 0])
        c2 = labelled_card("transport", w=5.4, h=1.0, size=BODY).move_to([3.4, 0.9, 0])
        self.play(FadeIn(c1, shift=RIGHT), FadeIn(c2, shift=LEFT), run_time=0.7)

        self.cue("An exposure map")
        s1 = VGroup(T("outcome depends on a summary,", LABEL), T("e.g. treated friends", LABEL, INK2))
        s1.arrange(DOWN, buff=0.2).next_to(c1, DOWN, buff=0.4)
        self.play(c1[0].animate.set_stroke(OX), FadeIn(s1), run_time=0.6)
        self.drop_caption()

        self.cue("And transport")
        s2 = VGroup(T("pilot's exposure effects", LABEL), T("hold under the policy", LABEL, INK2))
        s2.arrange(DOWN, buff=0.2).next_to(c2, DOWN, buff=0.4)
        self.play(c1[0].animate.set_stroke(SAND), FadeOut(s1), c2[0].animate.set_stroke(OX),
                  FadeIn(s2), run_time=0.6)
        self.finish()


# ---------------------------------------------------------------- scene 5
class S05Targets(Lecture):
    key, mark, title = "s05", "§5", "The targets z"

    def construct(self):
        self.header()
        icons = []
        for i, (mode, lab) in enumerate([("none", "status quo"), ("random", "one random pilot"),
                                         ("degree", "degree policy")]):
            g = mini_graph(mode, seed=31).move_to([-4.3 + 4.3 * i, 0.4, 0])
            t = T(lab, LABEL).next_to(g, DOWN, buff=0.3)
            icons.append(VGroup(g, t))
        self.play(FadeIn(icons[0]), run_time=0.6)
        self.cue("plus one randomized pilot")
        self.play(FadeIn(icons[1]), run_time=0.6)
        self.cue("Never the degree policy")
        self.play(FadeIn(icons[2]), run_time=0.5)
        self.play(icons[2].animate.set_opacity(0.35), run_time=0.5)
        self.caption("the degree policy: never observed")

        self.cue("So the targets are four")
        self.play(*[FadeOut(i) for i in icons], run_time=0.5)
        self.caption("four moments")
        tab = card(7.6, 3.4).move_to(DOWN * 0.35)
        rows = [("sq_level", "control"), ("sq_corr_x1", "control"),
                ("sq_peer_corr", "control"), ("pilot_level", "random")]
        stripes, rowm = VGroup(), []
        for i, (name, arm) in enumerate(rows):
            y = tab.get_top()[1] - 0.45 - i * 0.8
            if i % 2 == 1:
                stripes.add(Rectangle(width=7.3, height=0.72, fill_color=SAND, fill_opacity=0.45,
                                      stroke_width=0).move_to([0, y, 0]))
            rowm.append(VGroup(T(name, LABEL).move_to([-3.3, y, 0], aligned_edge=LEFT),
                               T(arm, LABEL, MUTED).move_to([3.3, y, 0], aligned_edge=RIGHT)))
        self.play(FadeIn(tab), FadeIn(stripes), run_time=0.5)
        for phrase, i in [("the mean outcome", 0), ("its correlation with the first", 1),
                          ("its correlation with the average", 2), ("The fourth", 3)]:
            self.cue(phrase)
            self.play(FadeIn(rowm[i], shift=UP * 0.1), run_time=0.4)

        self.cue("Stacked together")
        self.play(FadeOut(tab), FadeOut(stripes), *[FadeOut(r) for r in rowm], run_time=0.5)
        f1 = T("c → M(c)", BODY).move_to([-3.2, 1.1, 0])
        f1c = T("30 paired reps", LABEL, MUTED).next_to(f1, DOWN, buff=0.2)
        self.play(Write(f1), FadeIn(f1c), run_time=0.8)
        self.caption("the moments the model produces at c")

        self.cue("The targets, z")
        f2 = T("c* → z = M(c*)", BODY, OX).move_to([3.0, 1.1, 0])
        f2c = T("200 reps", LABEL, MUTED).next_to(f2, DOWN, buff=0.2)
        self.play(Write(f2), FadeIn(f2c), f1.animate.set_color(INK2), run_time=0.8)
        self.drop_caption()

        self.cue("They are stored in")
        fc = labelled_card("data/planted.json", h=0.9).move_to([3.0, -1.4, 0])
        arr = Arrow(f2c.get_bottom(), fc.get_top(), color=SAND, stroke_width=5, buff=0.1)
        self.play(Create(arr), FadeIn(fc), run_time=0.7)

        self.cue("Because we planted them")
        self.play(*[FadeOut(m) for m in (f1, f1c, f2, f2c, arr)], fc.animate.move_to([3.6, -0.3, 0]),
                  run_time=0.6)
        box = Rectangle(width=4.0, height=2.6, stroke_color=SAND, stroke_width=4).move_to([-2.6, -0.3, 0])
        bl = T("C", LABEL, MUTED).next_to(box, UL, buff=0.05).shift(DOWN * 0.45 + RIGHT * 0.45)
        star = Star(n=5, outer_radius=0.25, color=OX, fill_opacity=1).move_to(box)
        sl = T("c*", LABEL, OX).next_to(star, RIGHT, buff=0.15)
        self.play(Create(box), FadeIn(bl), GrowFromCenter(star), FadeIn(sl), run_time=0.8)
        self.caption("planted: the truth is known")

        self.cue("That is the point")
        self.caption("grade every analyst against the truth")
        self.finish()


# ---------------------------------------------------------------- scene 6
class S06HistoryMatching(Lecture):
    key, mark, title = "s06", "§6", "History matching"

    def construct(self):
        self.header()
        f_i = T("I(c) = Σ (z − M(c))² / V", BODY).move_to(UP * 1.2)
        self.play(Write(f_i), run_time=0.9)
        self.caption("implausibility: distance to the targets")

        self.cue("That variance adds")
        f_v = inline(T("V ="), sub("σ²", "z"), T("+"), sub("σ²", "MC"), T("(c)  +"),
                     T("δ²", BODY, OX)).next_to(f_i, DOWN, buff=0.5)
        self.play(Write(f_v), run_time=0.9)
        self.caption("target noise + Monte Carlo noise + δ²")

        self.cue("Delta is the discrepancy")
        self.caption("δ: an allowance for model error")

        self.cue("It is zero point zero two")
        d_row = T("δ = 0.02 levels · 0.05 correlations", LABEL, INK2).next_to(f_v, DOWN, buff=0.5)
        self.play(FadeIn(d_row), run_time=0.5)

        self.cue("A point is kept")
        self.play(FadeOut(f_i), FadeOut(f_v), FadeOut(d_row), run_time=0.4)
        keep = M('keep c if I(c) ≤ <span foreground="' + OX + '">τ</span>', BODY).move_to(UP * 1.9)
        self.play(Write(keep), run_time=0.7)
        self.caption("τ: 95% quantile of χ², 4 df")

        self.cue("Tau is a tolerance")
        self.caption("a tolerance, not a test level")

        self.cue("The search runs three")
        box = Rectangle(width=7.4, height=3.6, stroke_color=SAND, stroke_width=4).move_to(DOWN * 0.85)
        cl = T("C", LABEL, MUTED).move_to(box.get_corner(UL) + np.array([0.3, -0.3, 0]))
        self.play(Create(box), FadeIn(cl), run_time=0.6)
        self.caption("3 waves × 1000 Latin hypercube points")

        cx, cy = 0.6, -1.05

        def kept(p):
            x, y = p[0] - cx, p[1] - cy
            xr, yr = x * np.cos(-0.35) - y * np.sin(-0.35), x * np.sin(-0.35) + y * np.cos(-0.35)
            return (xr / 1.5) ** 2 + (yr / 0.7) ** 2 <= 1

        rng = np.random.default_rng(12)

        def wave(x0, x1, y0, y1, n, r=0.06):
            pts = np.c_[rng.uniform(x0, x1, n), rng.uniform(y0, y1, n), np.zeros(n)]
            dots = VGroup(*[Dot(p, radius=r, color=MUTED) for p in pts])
            keepers = [d for d, p in zip(dots, pts) if kept(p)]
            return dots, keepers

        self.cue("Wave one covers")
        bl, br = box.get_corner(DL), box.get_corner(np.array([1, 1, 0]))
        x0, y0, x1, y1 = bl[0] + 0.15, bl[1] + 0.15, br[0] - 0.15, br[1] - 0.15
        d1, k1 = wave(x0, x1, y0, y1, 70)
        self.play(LaggedStart(*[FadeIn(d) for d in d1], lag_ratio=0.02), run_time=1.0)
        self.play(*[d.animate.set_color(OX).scale(1.3) for d in k1], run_time=0.5)
        self.caption("wave 1: the whole box C")
        all_dots, all_kept = [d1], list(k1)

        self.cue("Each later wave")
        self.caption("next wave: around the kept points, +20%")
        for n, runt in ((45, 0.8), (35, 0.5)):
            kg = VGroup(*all_kept)
            bb = Rectangle(width=kg.width, height=kg.height).move_to(kg)
            bb = DashedVMobject(bb.set_stroke(INK, 3), num_dashes=40)
            self.play(Create(bb), run_time=0.5)
            self.play(bb.animate.scale(1.2), run_time=0.4)
            bx0, by0 = bb.get_corner(DL)[:2]
            bx1, by1 = bb.get_corner(np.array([1, 1, 0]))[:2]
            bx0, by0, bx1, by1 = max(bx0, x0), max(by0, y0), min(bx1, x1), min(by1, y1)
            prev = [d for g in all_dots for d in g if d not in all_kept]
            dn, kn = wave(bx0, bx1, by0, by1, n, r=0.05)
            self.play(*[d.animate.set_opacity(0.35) for d in prev], run_time=0.3)
            self.play(LaggedStart(*[FadeIn(d) for d in dn], lag_ratio=0.02), run_time=runt)
            self.play(*[d.animate.set_color(OX).scale(1.3) for d in kn], FadeOut(bb), run_time=0.4)
            all_dots.append(dn)
            all_kept += kn

        self.cue("There is no emulator")
        self.caption("no emulator: every point simulated")

        self.cue("The union of kept points")
        rejected = [d for g in all_dots for d in g if d not in all_kept]
        self.play(*[FadeOut(d) for d in rejected], run_time=0.6)
        nl = T("NROY: not ruled out yet", LABEL, OX).move_to([cx, y0 + 0.35, 0])
        nl.next_to(VGroup(*all_kept), UP, buff=0.35)
        self.play(FadeIn(nl), run_time=0.5)
        self.caption("the union of kept points, all waves")

        self.cue("If no point is kept")
        self.caption("no point kept → F-EMPTY · τ never loosened")
        self.finish()


# ---------------------------------------------------------------- scene 7
class S07Images(Lecture):
    key, mark, title = "s07", "§7", "The images"

    def construct(self):
        self.header()
        cloud = nroy_cloud([-4.0, 0.0], n=110, seed=5)
        cl = T("NROY", LABEL, INK2).next_to(cloud, UP, buff=0.3)
        self.play(FadeIn(cloud), FadeIn(cl), run_time=0.7)
        self.caption("a set of parameter points; we want policy units")

        self.cue("So we draw four hundred")
        rng = np.random.default_rng(9)
        sample_idx = rng.choice(len(cloud), 28, replace=False)
        sample = [cloud[i] for i in sample_idx]
        self.play(*[d.animate.set_color(OX).scale(1.4) for d in sample], run_time=0.6)
        self.caption("sample 400 NROY points at random")

        self.cue("At each one")
        ax_y = 1.0
        axis = Line([-0.6, ax_y, 0], [5.6, ax_y, 0], color=SAND, stroke_width=4)
        axl = T("θ2", LABEL).next_to(axis, RIGHT, buff=0.2)
        self.play(Create(axis), FadeIn(axl), run_time=0.5)
        xs = np.sort(rng.uniform(0.6, 4.4, len(sample)))
        ticks = VGroup(*[Line([x, ax_y - 0.22, 0], [x, ax_y + 0.22, 0], color=OX, stroke_width=3)
                         for x in rng.permutation(xs)])
        self.play(LaggedStart(*[TransformFromCopy(d, t) for d, t in zip(sample, ticks)],
                              lag_ratio=0.05), run_time=1.6)
        self.caption("θ2 at each point, 200 reps")

        self.cue("The smallest and the largest")
        lo, hi = xs.min(), xs.max()
        bar = Rectangle(width=hi - lo, height=0.26, fill_color=SAND, fill_opacity=1,
                        stroke_width=0).move_to([(lo + hi) / 2, ax_y - 0.55, 0])
        bl = inline(sub("Θ", "hm"), T("= [min, max]")).next_to(bar, DOWN, buff=0.2)
        self.play(GrowFromCenter(bar), Write(bl), ticks.animate.set_color(INK2), run_time=0.9)
        self.drop_caption()

        self.cue("We do the same")
        ay2 = -1.5
        axis2 = Line([-0.6, ay2, 0], [5.2, ay2, 0], color=SAND, stroke_width=4)
        ax2l = sub("δ", "spill").next_to(axis2, RIGHT, buff=0.2)
        xs2 = np.sort(rng.uniform(1.4, 3.6, len(sample)))
        ticks2 = VGroup(*[Line([x, ay2 - 0.22, 0], [x, ay2 + 0.22, 0], color=OX, stroke_width=3)
                          for x in xs2])
        self.play(Create(axis2), FadeIn(ax2l), run_time=0.5)
        self.play(LaggedStart(*[TransformFromCopy(d, t) for d, t in zip(sample, ticks2)],
                              lag_ratio=0.04), run_time=1.2)
        self.caption("a random-arm quantity: δ spill")

        self.cue("It compares untreated")
        self.play(FadeOut(cloud), FadeOut(cl), run_time=0.4)
        insets = VGroup()
        for k, (lab, treated) in enumerate([("S0c: ≥ 1/4 treated", 1), ("S0a: none treated", 0)]):
            c = np.array([-5.3 + 3.25 * k, 0.5, 0])
            me = Circle(radius=0.17, color=INK, stroke_width=4).move_to(c)
            fr = VGroup()
            for j in range(4):
                ang = np.pi / 2 + j * np.pi / 2 + 0.4
                p = c + 0.8 * np.array([np.cos(ang), np.sin(ang), 0])
                fr.add(Line(c, p, color=SAND, stroke_width=3),
                       Dot(p, radius=0.1, color=OX if j < treated else INK2))
            t = T(lab, CAP).next_to(VGroup(me, fr), DOWN, buff=0.25)
            insets.add(VGroup(fr, me, t))
        self.play(FadeIn(insets), run_time=0.6)
        self.caption("δ spill = mean(S0c) − mean(S0a)")

        self.cue("Its range is the image")
        lo2, hi2 = xs2.min(), xs2.max()
        bar2 = Rectangle(width=hi2 - lo2, height=0.26, fill_color=SAND, fill_opacity=1,
                         stroke_width=0).move_to([(lo2 + hi2) / 2, ay2 - 0.55, 0])
        bl2 = sub("Θ", "exp").next_to(bar2, DOWN, buff=0.2)
        self.play(GrowFromCenter(bar2), Write(bl2), ticks2.animate.set_color(INK2), run_time=0.8)
        self.drop_caption()

        self.cue("Here, an image is")
        self.play(FadeOut(insets), run_time=0.4)
        self.caption("the range across the 400 sampled points")

        self.cue("It is not a posterior")
        nots = VGroup()
        for k, w in enumerate(["posterior", "identified set"]):
            t = T(w, BODY, INK2).move_to([-3.9, 0.6 - 1.0 * k, 0])
            s = Line(t.get_left() + LEFT * 0.1, t.get_right() + RIGHT * 0.1, color=OX, stroke_width=5)
            nots.add(VGroup(t, s))
        self.play(FadeIn(nots[0][0]), Create(nots[0][1]), run_time=0.5)
        self.cue("And it is not an identified")
        self.play(FadeIn(nots[1][0]), Create(nots[1][1]), run_time=0.5)
        self.drop_caption()

        self.cue("Its endpoints are extremes")
        ends = VGroup(ticks[int(np.argmin([t.get_x() for t in ticks]))],
                      ticks[int(np.argmax([t.get_x() for t in ticks]))])
        self.play(Indicate(ends, color=OX, scale_factor=1.6), run_time=0.8)
        self.caption("so each endpoint is rechecked with fresh reps")
        self.play(Indicate(ends, color=OX, scale_factor=1.6), run_time=0.8)

        self.cue("And because delta is an assumption")
        self.play(*[FadeOut(m) for m in (nots, axis2, ax2l, ticks2, bar2, bl2)], run_time=0.5)
        menu = VGroup()
        for k, d in enumerate(["δ level 0.02", "δ level 0.01", "δ level 0.005"]):
            y = -1.0 - 0.75 * k
            lab = T(d, LABEL).move_to([-1.0, y, 0], aligned_edge=RIGHT)
            slot = DashedVMobject(Rectangle(width=hi - lo, height=0.3).set_stroke(INK2, 2),
                                  num_dashes=30).move_to([(lo + hi) / 2, y, 0])
            menu.add(VGroup(lab, slot))
        self.play(LaggedStart(*[FadeIn(m) for m in menu], lag_ratio=0.3), run_time=1.0)
        self.caption("amendment A1: rerun the search for each δ")

        self.cue("It is a menu of answers")
        self.caption("a menu of answers, never a way to choose δ")
        self.finish()


# ---------------------------------------------------------------- scene 8
class S08Analysts(Lecture):
    key, mark, title = "s08", "§8", "The analysts"

    def construct(self):
        self.header()
        self.caption("each sees one panel, reports one interval")

        self.cue("They work at three points")
        cloud = nroy_cloud([0.0, -0.1], n=120, rx=2.6, ry=1.1, seed=8, color=MUTED, r=0.05)
        cloud.set_opacity(0.55)
        self.play(FadeIn(cloud), run_time=0.6)

        def pin(p, txt, color):
            tri = Triangle(color=color, fill_opacity=1).scale(0.14).rotate(np.pi).move_to(p + UP * 0.2)
            lab = T(txt, LABEL, color).next_to(tri, UP, buff=0.1)
            return VGroup(tri, lab)

        self.cue("The calibrator")
        p1 = pin(np.array([-1.6, 0.25, 0]), "min-I", INK)
        p2 = pin(np.array([1.3, 0.45, 0]), "median-I", INK)
        self.play(FadeIn(p1, shift=DOWN * 0.2), FadeIn(p2, shift=DOWN * 0.2), run_time=0.6)
        self.caption("the calibrator: chosen by fit alone, never by θ")

        self.cue("The field experimenter")
        star = Star(n=5, outer_radius=0.2, color=OX, fill_opacity=1).move_to([0.1, -0.7, 0])
        sl = T("c*: the field experimenter", LABEL, OX).move_to([0.1, -2.15, 0])
        self.play(GrowFromCenter(star), FadeIn(sl), run_time=0.6)
        self.drop_caption()

        self.cue("Foil one is the SUTVA")
        self.play(*[FadeOut(m) for m in (cloud, p1, p2, star, sl)], run_time=0.5)
        hdr = T("Foil 1 · SUTVA", BODY, OX, bold=True).move_to([-4.6, 1.8, 0], aligned_edge=LEFT)
        hdr.to_edge(LEFT, buff=0.8)
        self.play(FadeIn(hdr), run_time=0.4)

        self.cue("On the degree-arm panel")
        g = mini_graph("degree", seed=41, radius=0.8).move_to([-5.0, 0.2, 0])
        s1 = T("OLS → β̂", BODY).move_to([-2.0, 0.2, 0])
        s2 = T("× k/N", BODY).move_to([0.6, 0.2, 0])
        br = bracket(2.6, 4.6, 0.2, color=OX)
        arrows = VGroup(*[Arrow(a.get_right(), b.get_left(), color=SAND, stroke_width=4, buff=0.15)
                          for a, b in ((g, s1), (s1, s2), (s2, br))])
        self.play(FadeIn(g), run_time=0.4)
        self.play(Create(arrows[0]), FadeIn(s1), run_time=0.5)
        self.caption("OLS on treatment and covariates, HC1 errors")
        self.cue("and scales the effect")
        self.play(Create(arrows[1]), FadeIn(s2), run_time=0.5)
        self.play(Create(arrows[2]), Create(br), run_time=0.5)
        self.drop_caption()

        self.cue("Only under SUTVA")
        lead = T("reads as θ2 only under:", LABEL, INK2).move_to([-5.4, -1.3, 0], aligned_edge=LEFT)
        chips = VGroup(*[labelled_card(s, h=0.7, size=CAP, pad=0.4) for s in
                         ["SUTVA", "exchangeability", "positivity"]]).arrange(RIGHT, buff=0.25)
        chips2 = VGroup(*[labelled_card(s, h=0.7, size=CAP, pad=0.4) for s in
                          ["correct additive model", "HC1 sampling basis"]]).arrange(RIGHT, buff=0.25)
        chips.next_to(lead, DOWN, buff=0.3).align_to(lead, LEFT)
        chips2.next_to(chips, DOWN, buff=0.25).align_to(lead, LEFT)
        self.play(FadeIn(lead), run_time=0.4)
        self.play(LaggedStart(*[FadeIn(c) for c in chips], lag_ratio=0.4), run_time=1.6)
        self.cue("a correctly specified")
        self.play(LaggedStart(*[FadeIn(c) for c in chips2], lag_ratio=0.5), run_time=1.2)

        self.cue("Under this model, it is not")
        self.play(FadeOut(lead), FadeOut(chips), FadeOut(chips2), run_time=0.4)
        self.caption("here there is interference: it is not θ2")

        self.cue("Foil two uses")
        self.play(*[FadeOut(m) for m in (hdr, g, s1, s2, br, arrows)], run_time=0.5)
        hdr2 = T("Foil 2", BODY, OX, bold=True).to_edge(LEFT, buff=0.8).set_y(1.8)
        g2 = mini_graph("random", seed=43, radius=0.8).move_to([-5.0, 0.2, 0])
        f2 = T("Hájek · Aronow–Samii", BODY).move_to([-1.0, 0.2, 0])
        br2 = bracket(2.4, 3.9, 0.2, color=OX)
        b2l = sub("δ", "spill", BODY, OX).next_to(br2, RIGHT, buff=0.3)
        ar2 = VGroup(Arrow(g2.get_right(), f2.get_left(), color=SAND, stroke_width=4, buff=0.15),
                     Arrow(f2.get_right(), br2.get_left(), color=SAND, stroke_width=4, buff=0.15))
        self.play(FadeIn(hdr2), FadeIn(g2), run_time=0.5)
        self.drop_caption()
        self.cue("It estimates delta spill")
        self.play(Create(ar2[0]), FadeIn(f2), run_time=0.5)
        self.play(Create(ar2[1]), Create(br2), FadeIn(b2l), run_time=0.5)
        self.cue("It never targets")
        self.caption("targets δ spill, never θ2")

        self.cue("Amendment A two adds")
        self.play(*[FadeOut(m) for m in (hdr2, g2, f2, br2, b2l, ar2)], run_time=0.5)
        rungs = VGroup()
        for k, s in enumerate(["A0 = Foil 1", "A1 · exposure transport", "A2 · degree-binned"]):
            rungs.add(labelled_card(s, w=5.6, h=0.95, size=BODY).move_to([-2.2, 1.2 - 1.3 * k, 0]))
        side = Arrow([-5.6, 1.4, 0], [-5.6, -1.6, 0], color=MUTED, stroke_width=5)
        sidel = T("fewer assumptions", CAP, MUTED).rotate(np.pi / 2).next_to(side, LEFT, buff=0.15)
        self.play(LaggedStart(*[FadeIn(r, shift=DOWN * 0.1) for r in rungs], lag_ratio=0.3),
                  Create(side), FadeIn(sidel), run_time=1.2)
        self.caption("a ladder of analysts for θ2")

        self.cue("Mind the names")
        nb = VGroup(T("amendment A1 = δ menu", LABEL), T("≠ analyst A1", LABEL))
        nb.arrange(DOWN, buff=0.15)
        nbc = card(nb.width + 0.6, nb.height + 0.5, fill=PAPER, stroke=OX).move_to(nb)
        name_box = VGroup(nbc, nb).move_to([3.9, -0.1, 0])
        self.drop_caption()
        self.play(FadeIn(name_box, scale=0.9), run_time=0.5)

        def focus(k):
            return [r[0].animate.set_fill(WASH if i == k else PAPER2).set_stroke(OX if i == k else SAND)
                    for i, r in enumerate(rungs)]

        self.cue("A zero is Foil one")
        self.play(FadeOut(name_box), *focus(0), run_time=0.5)

        self.cue("A one combines")
        self.play(*focus(1), run_time=0.5)
        self.caption("Hájek means vs S0a, weighted by policy shares")

        self.cue("A two also splits")
        self.play(*focus(2), run_time=0.5)
        self.caption("H = the top 80, L = the rest")

        self.cue("Each rung assumes less")
        self.caption("each rung assumes less")

        self.cue("The amendment wrote")
        e1 = T("|bias| ↓", BODY).move_to([3.6, 0.6, 0], aligned_edge=LEFT)
        e2 = T("width ↑", BODY).move_to([3.6, -0.6, 0], aligned_edge=LEFT)
        self.play(*[r[0].animate.set_fill(PAPER2).set_stroke(SAND) for r in rungs],
                  FadeIn(e1), FadeIn(e2), run_time=0.6)
        self.caption("pre-registered expectation, not a result")
        self.finish()


# ---------------------------------------------------------------- scene 9
class S09Judging(Lecture):
    key, mark, title = "s09", "§9", "Judging an interval"

    def construct(self):
        self.header()
        L, U, iy = -4.0, 0.4, 1.4
        img = Rectangle(width=U - L, height=0.36, fill_color=SAND, fill_opacity=1,
                        stroke_width=0).move_to([(L + U) / 2, iy, 0])
        il = T("image Θ", LABEL).next_to(img, LEFT, buff=0.3)
        self.play(FadeIn(img), FadeIn(il), run_time=0.6)
        self.caption("first, by geometry, against its own image")

        self.cue("Foil one goes against")
        self.caption(inline(T("Foil 1 vs", LABEL, MUTED), sub("Θ", "hm", LABEL, MUTED),
                            T("·  Foil 2 vs", LABEL, MUTED), sub("Θ", "exp", LABEL, MUTED)))

        brs = [(-4.7, 1.1, 0.45, "F-HONEST: covers it", "If the interval covers"),
               (-3.2, -0.4, -0.45, "F-OVERCONF: inside", "If it sits strictly"),
               (-0.9, 1.6, -1.35, "no verdict", "Anything else")]
        objs = []
        for x0, x1, y, lab, phrase in brs:
            self.cue(phrase)
            b = bracket(x0, x1, y)
            t = T(lab, LABEL, OX).move_to([2.2, y, 0], aligned_edge=LEFT)
            anims = [Create(b), FadeIn(t)]
            for ob, ot in objs:
                anims += [ob.animate.set_stroke(INK2), ot.animate.set_color(INK)]
            if len(objs) == 0:
                self.drop_caption()
            self.play(*anims, run_time=0.6)
            objs.append((b, t))

        self.cue("Second, by the truth")
        self.play(*[FadeOut(m) for pair in objs for m in pair], run_time=0.5)
        axis = Line([-4.5, -0.6, 0], [4.5, -0.6, 0], color=SAND, stroke_width=4)
        t_own = Line([-1.2, -0.85, 0], [-1.2, -0.35, 0], color=INK, stroke_width=6)
        lo = T("θ2(c)", LABEL).next_to(t_own, UP, buff=0.15)
        star = Star(n=5, outer_radius=0.17, color=OX, fill_opacity=1).move_to([1.6, -0.6, 0])
        ls = T("θ2(c*)", LABEL, OX).next_to(star, UP, buff=0.15)
        self.play(Create(axis), Create(t_own), FadeIn(lo), run_time=0.6)
        self.caption("second, by the truth, in two layers")

        self.cue("Layer A asks")
        self.caption("(a) the truth at its own point: its own world?")

        self.cue("Layer B asks")
        self.play(GrowFromCenter(star), FadeIn(ls), run_time=0.5)
        self.caption("(b) the truth at c*: the real village?")

        self.cue("At c star, the two layers")
        self.play(VGroup(t_own, lo).animate.shift(RIGHT * 2.8), ls.animate.shift(UP * 0.5), run_time=1.0)
        self.caption("at c*, (a) = (b)")

        self.cue("One panel gives containment")
        self.play(*[FadeOut(m) for m in (img, il, axis, t_own, lo, star, ls)], run_time=0.5)
        self.drop_caption()
        left = VGroup(T("one panel", BODY, bold=True), T("→ contains, or not", LABEL))
        left.arrange(DOWN, buff=0.3).move_to([-3.4, 0.6, 0])
        right = VGroup(T("many panels", BODY, bold=True), T("→ coverage", LABEL))
        right.arrange(DOWN, buff=0.3).move_to([3.4, 0.6, 0])
        div = Line([0, 1.6, 0], [0, -2.6, 0], color=SAND, stroke_width=3)
        self.play(FadeIn(left), Create(div), run_time=0.6)
        self.play(FadeIn(right), run_time=0.6)

        self.cue("The Foil two calibration")
        r1 = T("Foil 2 calibration check", LABEL, OX).next_to(right, DOWN, buff=0.6)
        self.play(FadeIn(r1), run_time=0.5)

        self.cue("So does amendment A two")
        r2 = VGroup(T("A2: 200 fresh panels", LABEL, OX), T("exact Clopper–Pearson", LABEL, OX))
        r2.arrange(DOWN, buff=0.15).next_to(r1, DOWN, buff=0.35)
        self.play(r1.animate.set_color(INK), FadeIn(r2), run_time=0.5)
        self.finish()


# ---------------------------------------------------------------- scene 10
class S10Replicate(Lecture):
    key, mark, title = "s10", "§10", "Replicate it"

    def construct(self):
        self.header()
        self.caption("how do you check all of this yourself?")

        self.cue("One command")
        cmd_t = T("env -u PYTHONPATH .venv/bin/python scripts/replicate.py", LABEL)
        strip = card(cmd_t.width + 0.7, 0.85).move_to(UP * 1.85)
        cmd_t.move_to(strip)
        self.play(FadeIn(strip), Write(cmd_t), run_time=1.2)
        self.caption("from the repo root, with PYTHONPATH unset")

        rows = []
        anchor = np.array([-3.6, 0.7, 0])
        steps = [("It runs the tests", "✓ tests"),
                 ("It regenerates the targets", "✓ targets z, byte for byte"),
                 ("It runs the planted", "✓ planted pipeline"),
                 ("Then the Foil two", "✓ Foil 2 check"),
                 ("and the delta menu", "✓ δ menu"),
                 ("Then it copies the paper", "✓ paper figures"),
                 ("writes the paper's result", "✓ result numbers as macros"),
                 ("builds the PDF", "✓ PDF, if latexmk is there"),
                 ("Last, it compares", "✓ compare with committed results")]
        for i, (phrase, txt) in enumerate(steps):
            self.cue(phrase)
            if i == 0:
                self.drop_caption()
            self.push_row(rows, T(txt, BODY), anchor, visible=4, gap=0.7, rt=0.4)

        self.cue("and prints REPLICATED")
        rep = T("REPLICATED", TITLE, OX, bold=True).move_to(DOWN * 2.3)
        self.play(rows[-1].animate.set_color(INK), Write(rep), run_time=0.8)

        self.cue("Amendment A two adds")
        a2 = T("+ A2 step, for its analysts", BODY, INK2)
        a2b = DashedVMobject(card(a2.width + 0.6, 0.8, fill=PAPER).set_stroke(SAND, 3), num_dashes=50)
        a2g = VGroup(a2b, a2.move_to(a2b)).move_to([3.4, -2.3, 0])
        self.play(rep.animate.shift(LEFT * 3.4), FadeIn(a2g, shift=LEFT * 0.2), run_time=0.6)

        self.cue("Every random draw")
        self.caption("named, stable seeds → the same digits on a rerun")

        self.cue("Where things live")
        self.play(*[FadeOut(m) for m in rows + [rep, a2g, strip, cmd_t]], run_time=0.5)
        self.drop_caption()
        xs = -3.2

        def lvl(text, y, w=3.6, h=0.75):
            return labelled_card(text, w=w, h=h, size=BODY, bold=True).move_to([xs, y, 0])

        cfg = lvl("config/", 2.1)
        src = lvl("src/poc_abm/", 0.6)
        data = labelled_card("data/", w=2.4, h=0.75, size=BODY, bold=True).move_to([xs - 1.6, -0.75, 0])
        res = labelled_card("results/", w=2.4, h=0.75, size=BODY, bold=True).move_to([xs + 1.6, -0.75, 0])
        mac = lvl("paper macros", -2.05, w=4.0)

        def arr(a, b):
            return Arrow(a.get_bottom(), b.get_top(), color=SAND, stroke_width=5, buff=0.08,
                         max_tip_length_to_length_ratio=0.45)

        self.cue("The config folder")
        n1 = T("the choices", LABEL, MUTED).move_to([0.4, 2.1, 0], aligned_edge=LEFT)
        self.play(FadeIn(cfg), FadeIn(n1), run_time=0.5)

        self.cue("The source folder")
        a1 = arr(cfg, src)
        n2 = VGroup(T("kernel · moments · history matching", CAP, MUTED),
                    T("estimand · foils · pipeline", CAP, MUTED)).arrange(DOWN, aligned_edge=LEFT, buff=0.12)
        n2.move_to([0.4, 0.6, 0], aligned_edge=LEFT)
        self.play(Create(a1), FadeIn(src), FadeIn(n2), run_time=0.7)

        self.cue("Data holds the targets")
        a2_ = arr(src, data)
        n3 = T("data: the targets", LABEL, MUTED).move_to([0.4, -0.5, 0], aligned_edge=LEFT)
        self.play(Create(a2_), FadeIn(data), FadeIn(n3), run_time=0.6)

        self.cue("Results hold the run")
        a3 = arr(src, res)
        n4 = T("results: run outputs", LABEL, MUTED).move_to([0.4, -1.0, 0], aligned_edge=LEFT)
        self.play(Create(a3), FadeIn(res), FadeIn(n4), run_time=0.6)

        self.cue("and the paper reads")
        a4 = arr(res, mac)
        n5 = T("the paper's result numbers", LABEL, MUTED).move_to([0.4, -2.05, 0], aligned_edge=LEFT)
        self.play(Create(a4), FadeIn(mac), FadeIn(n5), run_time=0.6)

        self.cue("Start at the config")
        self.play(cfg[0].animate.set_stroke(OX, 5), cfg[1].animate.set_color(OX), run_time=0.5)
        self.caption("Start at config/. Follow the arrows down.", color=INK)
        self.finish()


SCENES = [S01Question, S02Config, S03Kernel, S04Estimand, S05Targets, S06HistoryMatching,
          S07Images, S08Analysts, S09Judging, S10Replicate]
