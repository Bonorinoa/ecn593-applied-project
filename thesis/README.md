# thesis/: the ECN 593 paper (arXiv preprint template)

A self-contained LaTeX project for the paper: about 20 pages of main text, then
references and appendix. It compiles with **pdfLaTeX**. The bibliography uses
**natbib + BibTeX** (style `aer`), because arXiv does not run Biber and accepts a
BibTeX `.bbl` without version trouble.

| File | What it is |
|---|---|
| `ecnthesis.cls` | the class: both looks, title page, boxes, theorem-like environments, zebra tables, captions, headers, appendix and references styles |
| `main.tex` | the paper. Right now it is the template sample: placeholder text that uses every element once |
| `refs.bib` | BibTeX entries (five for now, from `writeup/main.tex`) |
| `latexmkrc` | pdfLaTeX + BibTeX, fixed timestamp for byte-reproducible PDFs |
| `figures/` | figure files. E3 fills it (`.png` from the code); empty until then |
| `numbers.tex` | **generated** number macros, copied in by E3 from `scripts/write_numbers.py`. Not committed by the template card. `main.tex` loads it with `\InputIfFileExists{numbers}{}{}`, so the template builds without it |
| `build_looks.sh` | builds both looks and renders the review shots into `shots/` |
| `shots/` | 80 dpi PNGs of pages 1 to 4 and the first appendix page, both looks |

## Compile

From `thesis/`:

```sh
latexmk            # main.tex -> main.pdf (pdfLaTeX, BibTeX as needed)
latexmk -c         # remove build products (keeps the PDF)
sh build_looks.sh  # both looks + shots/; prints Overfull / error / undefined counts
```

`latexmkrc` fixes `SOURCE_DATE_EPOCH`, so `\today` is frozen too: set the date
with `\date{...}` in `main.tex`.

## Switch the look

One class option, first line of `main.tex`:

```latex
\documentclass{ecnthesis}         % kaffeehaus (default)
\documentclass[mono]{ecnthesis}   % mono, close to writeup/main.pdf
```

Nothing else changes: same commands, environments, counters and colour names.
To build the mono look without editing `main.tex` (this is what `build_looks.sh` does):

```sh
latexmk -jobname=main-mono -usepretex='\PassOptionsToClass{mono}{ecnthesis}' main.tex
```

| | kaffeehaus | mono |
|---|---|---|
| body | Times (`newtxtext`, `newtxmath`) | DejaVu Sans Mono at 0.86, Computer Modern math |
| headings, labels | Helvetica clone (TeX Gyre Heros) | the same mono, bold |
| colour | oxblood accent, sand hairlines, cream boxes, light sand stripes | greys |
| measure | 6.0 in on letter paper (1.25 in side margins) | 22 mm margins, as the writeup |
| paragraphs | first-line indent | no indent, space between paragraphs |

## Upload to Overleaf

1. Zip the contents of `thesis/` (not the folder above it) without the build
   products: `cd thesis && zip -r ../thesis.zip ecnthesis.cls main.tex refs.bib latexmkrc numbers.tex figures`.
2. Overleaf: New Project, Upload Project, pick the zip.
3. Menu, Compiler: **pdfLaTeX**. Main document: `main.tex`. Overleaf honours
   `latexmkrc` and runs BibTeX by itself.

## Submit to arXiv

arXiv compiles with pdfLaTeX but **does not run BibTeX**. Build locally first, then
upload `ecnthesis.cls`, `main.tex`, **`main.bbl`**, `numbers.tex` and `figures/`
(`refs.bib` and `latexmkrc` are not needed). The class uses only packages in
TeX Live.

## What the class provides

Title page (all set in the preamble, placed by `\maketitle`):

```latex
\title{...}  \subtitle{...}  \shorttitle{...}    % \shorttitle feeds the running header
\author{Augusto Gonz\'alez-Bonorino}  \affiliation{Arizona State University}
\course{ECN 593 \textperiodcentered\ Applied Project}  \date{...}  \email{...}
\keywords{...}  \jel{...}
\titlenote{...}      % small print at the foot of the title page
\titlestatus{...}    % optional status box on the title page
\begin{abstract} ... \end{abstract}   % in the preamble; \maketitle places it
```

The title page is unnumbered; the text starts on page 1.

Body:

- `\section`, `\subsection`, `\subsubsection`, `\paragraph` (run-in). Sections are numbered.
- `\begin{statusbox}[Label] ... \end{statusbox}`: the short status or disclosure box
  (label defaults to "Status").
- `definition`, `assumption`, `proposition`, `remark` (upright body, one counter each),
  and amsthm's `proof`.
- Zebra tables (booktabs rules, every second body row striped):
  `\begin{zebratabular}{lccc}` or `\begin{zebratabularx}{\linewidth}{Xccc}`, column
  heads with `\colhead{...}`, notes under the table with `\tablenote{...}`. Leave out
  `@{}` at the outer edges so stripes and rules end together. Captions go above
  tables and below figures.
- `\includefigure[width=...]{file.png}` includes `figures/file.png`, or draws a
  labelled placeholder (and a warning) while the file does not exist.
  `\figureplaceholder[width]{height}{text}` draws one directly.
- TikZ: the styles `ecn`, `ecn box`, `ecn mark`, `ecn arrow`, `ecn band`, `ecn label`, and the
  colour names `ink`, `line`, `rule`, `wash`, `accent`, `sand`, `zebra`, `tablerule`.
  The first four are the names `writeup/main.tex` and `writeup/cover.tex` use, so
  those diagrams port unchanged and take the active look's colours.
  In nodes with a `text width`, use `align=flush center` (the `ecn box` styles do):
  TikZ's `align=center` stretches the spaces around `=` and `\le`.
- `\bibliographystyle{aer}` + `\bibliography{refs}`: an unnumbered "References"
  section with hanging indents. `aer` does not print DOIs; for DOIs, switch to
  `plainnat` (also author-year).
- `\appendix`: starts a new page; sections become "Appendix A", ...; equations,
  tables and figures are numbered A.1, A.2, ...
- Running headers: short title on the left, current section on the right, page
  number centred at the foot.

## Rules for this folder

Every result number in the text is a macro from `numbers.tex`; never type one.
The template card (T1) commits only its own files here; `numbers.tex` and
`figures/*.png` belong to E3.
