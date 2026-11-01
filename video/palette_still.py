"""Palette still for the storyboard: the same sample frame on cream and on deep ink.

Render (from the repo root; ephemeral env, nothing installed into the repo):
    env -u PYTHONPATH uv run --no-project --exclude-newer "7 days" --with manim \
        manim -s -qh --format png -o palette-choice video/palette_still.py PaletteChoice
The PNG lands under video/media/ (gitignored); the storyboard's copy is video/palette-choice.png.
Colours are the Kaffeehaus tokens (strudel-kaffeehaus/design/tokens.css, light and dark themes).
"""
from manim import (DOWN, LEFT, RIGHT, UP, Dot, Line, Rectangle, Scene, Text,
                   VGroup, config)

LIGHT = dict(paper="#F5EFE3", paper2="#ECE2CF", sand="#D8C5A2", ink="#2B211D",
             ink2="#54463E", ox="#6B1E23", muted="#67584D")
DARK = dict(paper="#181312", paper2="#221B18", sand="#4B3E34", ink="#EDE4D3",
            ink2="#CDBFAB", ox="#E09A94", muted="#A3937F")
SANS = "Helvetica Neue"


def panel(p, label):
    w, h = config.frame_width / 2, config.frame_height
    bg = Rectangle(width=w, height=h, stroke_width=0, fill_color=p["paper"], fill_opacity=1)
    marker = Text("§6", font=SANS, weight="BOLD", color=p["ox"]).scale(0.55)
    title = Text("History matching", font=SANS, weight="BOLD", color=p["ink"]).scale(0.62)
    head = VGroup(marker, title).arrange(RIGHT, buff=0.25)
    rule = Line(LEFT * 3, RIGHT * 3, color=p["sand"], stroke_width=3)
    box = Rectangle(width=4.2, height=2.6, color=p["sand"], stroke_width=3,
                    fill_color=p["paper2"], fill_opacity=1)
    kept = [(-1.2, 0.5), (-0.6, 0.1), (0.1, 0.6), (0.6, -0.2), (-0.2, -0.5), (1.1, 0.3)]
    cut = [(-1.7, -0.9), (1.6, 0.9), (1.5, -1.0), (-1.6, 1.0)]
    dots = VGroup(*[Dot([x, y, 0], radius=0.08, color=p["ox"]) for x, y in kept],
                  *[Dot([x, y, 0], radius=0.06, color=p["muted"], fill_opacity=0.5) for x, y in cut])
    dots.move_to(box)
    rule_txt = Text("keep c if I(c) ≤ τ", font=SANS, color=p["ink"]).scale(0.5)
    sub = Text("δ = the discrepancy · NROY = not ruled out yet", font=SANS,
               color=p["ink2"]).scale(0.34)
    tag = Text(label, font=SANS, color=p["muted"]).scale(0.3)
    body = VGroup(head, rule, VGroup(box, dots), rule_txt, sub).arrange(DOWN, buff=0.32)
    tag.to_edge(DOWN, buff=0.3)
    content = VGroup(body, tag)
    return VGroup(bg, content)


class PaletteChoice(Scene):
    def construct(self):
        left = panel(LIGHT, "A · cream paper  #F5EFE3")
        right = panel(DARK, "B · deep ink  #181312")
        left.shift(LEFT * config.frame_width / 4)
        right.shift(RIGHT * config.frame_width / 4)
        # keep each panel's tag inside its own half
        for p in (left, right):
            p[1][1].next_to(p[0].get_bottom(), UP, buff=0.3)
        self.add(left, right)
