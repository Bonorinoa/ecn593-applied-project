%% ecnthesis.cls -- paper class for the ECN 593 applied project (arXiv preprint).
%%
%% Two looks, one structure. The look is the only thing a class option changes:
%%   \documentclass{ecnthesis}             % kaffeehaus (default): Times + Helvetica,
%%                                         %   oxblood / sand / cream accents
%%   \documentclass[mono]{ecnthesis}       % mono: DejaVu Sans Mono, greys
%%                                         %   (close to writeup/main.pdf)
%% Every command, environment, counter and colour NAME below exists in both looks,
%% so a document compiles unchanged under either option.
%%
%% Engine: pdfLaTeX (arXiv's default). Bibliography: natbib + BibTeX.
%%
%% Colour names shared by both looks (use these in TikZ so diagrams port):
%%   ink      body text, strong strokes        line   secondary text, arrows
%%   rule     box outlines, rules in diagrams  wash   box / band fill
%%   accent   section numbers, labels, marks   sand   hairlines
%%   zebra    table stripes                    tablerule  booktabs rules
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{ecnthesis}[2026/11/01 v1.0 ECN 593 thesis/preprint class]

% ------------------------------------------------------------------ options
\newif\ifecn@mono \ecn@monofalse
\DeclareOption{kaffeehaus}{\ecn@monofalse}
\DeclareOption{mono}{\ecn@monotrue}
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{article}}
\ExecuteOptions{kaffeehaus}
\ProcessOptions\relax
\LoadClass[11pt,letterpaper,oneside]{article}

% ------------------------------------------------------------------ packages
\RequirePackage[T1]{fontenc}
\ifecn@mono
  \RequirePackage{lmodern}                       % text fallback only
  \RequirePackage[scaled=0.86]{DejaVuSansMono}   % same face and scale as writeup/
  \renewcommand{\familydefault}{\ttdefault}
  % A monospaced font has rigid word spaces, which breaks justified text
  % (overfull lines). Give the body face elastic spaces, as XeLaTeX's
  % \setmainfont did for writeup/: load the font definitions now, then
  % redeclare the family with stretch 1/2 and shrink 1/3 of a space.
  \input{T1DejaVuSansMono-TLF.fd}
  \DeclareFontFamily{T1}{DejaVuSansMono-TLF}{%
    \fontdimen3\font=0.5\fontdimen2\font
    \fontdimen4\font=0.33\fontdimen2\font}
  \RequirePackage{amsmath,amssymb,amsthm}
\else
  \RequirePackage{newtxtext}                     % Times body; TeX Gyre Heros as \sffamily
  \RequirePackage{amsmath,amsthm}                % amsthm before newtxmath (\openbox)
  \RequirePackage[varqu]{zi4}                    % Inconsolata for \texttt (URLs, paths)
  \RequirePackage{newtxmath}                     % loads amssymb-equivalents
\fi
\RequirePackage[table]{xcolor}
\RequirePackage{geometry}
\RequirePackage[final]{microtype}
\RequirePackage{setspace}
\RequirePackage{titlesec}
\RequirePackage{fancyhdr}
\RequirePackage{booktabs,array,tabularx}
\RequirePackage{enumitem}
\RequirePackage{graphicx}
\RequirePackage{caption}
\RequirePackage{environ}
\RequirePackage{needspace}
\RequirePackage{tikz}
\usetikzlibrary{arrows.meta,positioning,fit,calc,chains}
\RequirePackage[skins,breakable]{tcolorbox}
\RequirePackage[authoryear,round]{natbib}
\RequirePackage{xurl}
\RequirePackage{hyperref}   % keep last (the class loads nothing after it)

\graphicspath{{figures/}}

% ------------------------------------------------------------------ colours
\ifecn@mono
  \definecolor{ink}{HTML}{111111}
  \definecolor{rule}{HTML}{222222}
  \definecolor{wash}{HTML}{F4F4F4}
  \definecolor{line}{HTML}{555555}
  \definecolor{accent}{HTML}{111111}
  \definecolor{sand}{HTML}{BBBBBB}
  \definecolor{zebra}{HTML}{F2F2F2}
  \definecolor{tablerule}{HTML}{222222}
\else
  \definecolor{oxblood}{HTML}{6E1F2A}
  \definecolor{sandtone}{HTML}{C8B28A}
  \definecolor{cream}{HTML}{FAF5EC}
  \definecolor{ink}{HTML}{231E1B}
  \definecolor{rule}{HTML}{4A3F38}
  \definecolor{wash}{HTML}{FAF5EC}       % = cream
  \definecolor{line}{HTML}{6B6058}       % warm grey
  \definecolor{accent}{HTML}{6E1F2A}     % = oxblood
  \definecolor{sand}{HTML}{C8B28A}
  \definecolor{zebra}{HTML}{F2EADB}      % light sand stripe
  \definecolor{tablerule}{HTML}{6E1F2A}
\fi

% ------------------------------------------------------------------ fonts used by the layout
% \ecnheadfont: headings and labels (Helvetica-like, or mono)
% \ecntitlefont: the title
\ifecn@mono
  \newcommand{\ecnheadfont}{\ttfamily}
  \newcommand{\ecntitlefont}{\ttfamily\bfseries}
  \newcommand{\ecnspaced}[1]{#1}
\else
  \newcommand{\ecnheadfont}{\sffamily}
  \newcommand{\ecntitlefont}{\rmfamily\bfseries}
  \newcommand{\ecnspaced}[1]{\textls[60]{#1}}
\fi

% ------------------------------------------------------------------ page geometry and text
\ifecn@mono
  \geometry{letterpaper,margin=22mm,headsep=8mm,footskip=11mm}
  \setstretch{1.12}
  \setlength{\parindent}{0pt}
  \setlength{\parskip}{0.55em plus 0.1em}
\else
  % generous margins: a 6.0in measure on letter paper
  \geometry{letterpaper,hmargin=1.25in,top=1.2in,bottom=1.15in,headsep=0.3in,footskip=0.45in}
  \setstretch{1.10}
  \setlength{\parindent}{1.4em}
  \setlength{\parskip}{0pt plus 0.5pt}
\fi
\color{ink}
\setlength{\emergencystretch}{2.5em}
\clubpenalty=10000
\widowpenalty=10000
\displaywidowpenalty=10000
\frenchspacing
\setlist{itemsep=0.15em,topsep=0.35em}
\setlist[itemize]{leftmargin=1.4em,label={\color{accent}\textbullet}}
\setlist[enumerate]{leftmargin=1.6em,label={\ecnheadfont\color{accent}\arabic*.}}

% ------------------------------------------------------------------ hyperref
\ifecn@mono
  \hypersetup{hidelinks}
\else
  \hypersetup{colorlinks=true,linkcolor=oxblood,citecolor=oxblood,urlcolor=oxblood}
\fi
\hypersetup{pdfcreator={ecnthesis.cls},bookmarksnumbered=true}
\urlstyle{same}

% ------------------------------------------------------------------ title data
\newcommand{\ecn@subtitle}{}
\newcommand{\subtitle}[1]{\renewcommand{\ecn@subtitle}{#1}}
\newcommand{\ecn@shorttitle}{}
\newcommand{\shorttitle}[1]{\renewcommand{\ecn@shorttitle}{#1}}
\newcommand{\ecn@affiliation}{Arizona State University}
\newcommand{\affiliation}[1]{\renewcommand{\ecn@affiliation}{#1}}
\newcommand{\ecn@course}{ECN 593 \textperiodcentered\ Applied Project}
\newcommand{\course}[1]{\renewcommand{\ecn@course}{#1}}
\newcommand{\ecn@email}{}
\newcommand{\email}[1]{\renewcommand{\ecn@email}{#1}}
\newcommand{\ecn@keywords}{}
\newcommand{\keywords}[1]{\renewcommand{\ecn@keywords}{#1}}
\newcommand{\ecn@jel}{}
\newcommand{\jel}[1]{\renewcommand{\ecn@jel}{#1}}
\newcommand{\ecn@titlenote}{}
\newcommand{\titlenote}[1]{\renewcommand{\ecn@titlenote}{#1}}
\newcommand{\ecn@titlestatus}{}
\newcommand{\titlestatus}[1]{\renewcommand{\ecn@titlestatus}{#1}}
\newcommand{\ecn@abstract}{}
% The abstract is written in the preamble (or anywhere before \maketitle)
% and \maketitle places it on the title page.
\RenewEnviron{abstract}{\global\let\ecn@abstract\BODY}

% ------------------------------------------------------------------ status / disclosure box
% \begin{statusbox}[Label] ... \end{statusbox}   (label defaults to "Status")
\newtcolorbox{statusbox}[1][Status]{%
  enhanced, breakable,
  colback=wash, colframe=accent, coltext=ink,
  boxrule=0pt, leftrule=\ifecn@mono 1.2pt\else 2.2pt\fi,
  arc=0pt, outer arc=0pt,
  left=9pt, right=9pt, top=6pt, bottom=6pt,
  before skip=0.9em, after skip=0.9em,
  fontupper=\small\setlength{\parskip}{0.35em}\setlength{\parindent}{0pt},
  before upper={{\ecnheadfont\bfseries\footnotesize\color{accent}\ecnspaced{\MakeUppercase{#1}}}\hspace{0.8em}}%
}

% ------------------------------------------------------------------ title page
\renewcommand{\maketitle}{%
  \begingroup
  \hypersetup{pageanchor=false}%
  \thispagestyle{empty}%
  \setlength{\parindent}{0pt}\setlength{\parskip}{0pt}%
  \raggedright
  % top strip
  {\ecnheadfont\footnotesize\color{line}%
    \ecnspaced{\MakeUppercase{\ecn@course}}\hfill\ecnspaced{\MakeUppercase{\ecn@affiliation}}\par}%
  \vspace{0.55em}%
  {\color{accent}\rule{\linewidth}{\ifecn@mono 1.2pt\else 1.6pt\fi}}\par
  \vspace{\ifecn@mono 2.2em\else 3.0em\fi}%
  % title and subtitle
  {\ecntitlefont\fontsize{24}{29}\selectfont\color{\ifecn@mono ink\else accent\fi}\@title\par}%
  \ifx\ecn@subtitle\@empty\else
    \vspace{0.8em}%
    {\ifecn@mono\normalsize\else\large\itshape\fi\color{line}\ecn@subtitle\par}%
  \fi
  \vspace{2.0em}%
  % author block
  {\ecnheadfont\normalsize\bfseries\color{ink}\@author\par}%
  \vspace{0.25em}%
  {\ecnheadfont\footnotesize\color{line}\ecn@affiliation
    \ifx\ecn@email\@empty\else\ \textperiodcentered\ \ecn@email\fi\par}%
  \vspace{0.15em}%
  {\ecnheadfont\footnotesize\color{line}\@date\par}%
  \vspace{2.4em}%
  % abstract
  \ifx\ecn@abstract\@empty\else
    {\ecnheadfont\footnotesize\bfseries\color{accent}\ecnspaced{ABSTRACT}\par}%
    \vspace{0.5em}%
    {\color{sand}\rule{\linewidth}{0.4pt}}\par
    \vspace{0.7em}%
    {\small\setstretch{1.12}\ifecn@mono\else\justifying@ecn\fi\ecn@abstract\par}%
    \vspace{0.7em}%
    {\color{sand}\rule{\linewidth}{0.4pt}}\par
    \vspace{0.6em}%
  \fi
  \ifx\ecn@keywords\@empty\else
    {\footnotesize\ecn@meta{Keywords}{\ecn@keywords}\par}\vspace{0.3em}%
  \fi
  \ifx\ecn@jel\@empty\else
    {\footnotesize\ecn@meta{JEL codes}{\ecn@jel}\par}%
  \fi
  \ifx\ecn@titlestatus\@empty\else
    \vspace{1.4em}%
    \begin{statusbox}\ecn@titlestatus\end{statusbox}%
  \fi
  \vfill
  \ifx\ecn@titlenote\@empty\else
    {\color{sand}\rule{\linewidth}{0.4pt}}\par\vspace{0.5em}%
    {\ecnheadfont\scriptsize\color{line}\ecn@titlenote\par}%
  \fi
  \clearpage
  \endgroup
  \setcounter{page}{1}%
  \setcounter{footnote}{0}%
  \gdef\@thanks{}%
}
\newcommand{\justifying@ecn}{\rightskip=0pt\relax\leftskip=0pt\relax\parfillskip=0pt plus 1fil\relax}
\newcommand{\ecn@meta}[2]{%
  \begin{tabularx}{\linewidth}{@{}>{\ecnheadfont\bfseries\color{accent}}p{6.6em}>{\raggedright\arraybackslash\color{ink}}X@{}}%
    \ecnspaced{\MakeUppercase{#1}} & #2
  \end{tabularx}}

% ------------------------------------------------------------------ sections
% \Needspace (capital N) checks the room left and breaks only if it is short.
% The lower-case \needspace inserts stretchable glue that, in a ragged-bottom
% page, often looks to TeX like the best break and ends pages half empty.
\setcounter{secnumdepth}{3}
\ifecn@mono
  \titleformat{\section}[block]
    {\Needspace{7\baselineskip}\normalsize\bfseries\color{ink}}
    {\thesection}{0.7em}{}
    [\vspace{-0.4em}{\color{rule}\titlerule[0.4pt]}]
  \titleformat{\subsection}[block]
    {\normalsize\bfseries\color{ink}}{\thesubsection}{0.6em}{}
  \titleformat{\subsubsection}[runin]
    {\normalsize\bfseries\color{ink}}{\thesubsubsection}{0.6em}{}[.~]
  \titleformat{\paragraph}[runin]{\normalsize\bfseries\color{ink}}{}{0pt}{}[.]
  \titlespacing*{\section}{0pt}{1.4em}{0.7em}
  \titlespacing*{\subsection}{0pt}{1.0em}{0.35em}
  \titlespacing*{\subsubsection}{0pt}{0.8em}{0.5em}
  \titlespacing*{\paragraph}{0pt}{0.6em}{1ex}
\else
  % a short oxblood bar above each section: the "section-number marker"
  \titleformat{\section}[display]
    {\Needspace{7\baselineskip}\sffamily\bfseries\color{ink}}
    {\vbox{\hbox{\color{accent}\rule{2.2em}{1.4pt}}\vskip0.55em
      \hbox{\small\color{accent}\textls[80]{\MakeUppercase{\ecn@secprefix}}\thesection}}}
    {-1.0em}{\Large}
  \titleformat{name=\section,numberless}[display]
    {\Needspace{7\baselineskip}\sffamily\bfseries\color{ink}}
    {\vbox{\hbox{\color{accent}\rule{2.2em}{1.4pt}}}}
    {-0.2em}{\Large}
  \titleformat{\subsection}[hang]
    {\sffamily\bfseries\large\color{ink}}{\color{accent}\thesubsection}{0.75em}{}
  \titleformat{\subsubsection}[hang]
    {\sffamily\bfseries\normalsize\color{ink}}{\color{accent}\thesubsubsection}{0.7em}{}
  \titleformat{\paragraph}[runin]
    {\sffamily\bfseries\small\color{ink}}{}{0pt}{}[.]
  \titlespacing*{\section}{0pt}{2.2em}{0.9em}
  \titlespacing*{\subsection}{0pt}{1.5em}{0.55em}
  \titlespacing*{\subsubsection}{0pt}{1.1em}{0.4em}
  \titlespacing*{\paragraph}{0pt}{0.8em}{0.7em}
\fi
\newcommand{\ecn@secprefix}{Section\ }

% ------------------------------------------------------------------ running headers
\newcommand{\ecn@headtitle}{\ifx\ecn@shorttitle\@empty\@title\else\ecn@shorttitle\fi}
\pagestyle{fancy}
% after \pagestyle{fancy}, which redefines both: sections only in the header
\renewcommand{\sectionmark}[1]{\markright{\thesection\quad #1}}
\renewcommand{\subsectionmark}[1]{}
\fancyhf{}
\fancyhead[L]{\ecnheadfont\footnotesize\color{line}\ecnspaced{\ecn@headtitle}}
\fancyhead[R]{\ecnheadfont\footnotesize\color{line}\nouppercase{\rightmark}}
\fancyfoot[C]{\ecnheadfont\footnotesize\color{accent}\thepage}
\renewcommand{\headrule}{{\color{sand}\hrule height 0.4pt width\headwidth}}
\renewcommand{\headrulewidth}{0.4pt}
\fancypagestyle{plain}{%
  \fancyhf{}%
  \fancyfoot[C]{\ecnheadfont\footnotesize\color{accent}\thepage}%
  \renewcommand{\headrule}{}}
\setlength{\headheight}{14pt}
\renewcommand{\footnoterule}{\kern-3pt{\color{sand}\hrule width 0.3\columnwidth height 0.4pt}\kern 2.6pt}

% ------------------------------------------------------------------ theorem-like environments
% Upright body (economics convention); head in the heading face, coloured accent.
\newtheoremstyle{ecnthm}
  {0.8em}{0.8em}
  {\normalfont}{0pt}
  {\ecnheadfont\bfseries\color{accent}}{.}
  {0.6em}
  {\thmname{#1}\thmnumber{ #2}\thmnote{\normalfont\ecnheadfont\color{line}\ (#3)}}
\theoremstyle{ecnthm}
\newtheorem{definition}{Definition}
\newtheorem{assumption}{Assumption}
\newtheorem{proposition}{Proposition}
\newtheorem{remark}{Remark}
\renewcommand{\qedsymbol}{{\color{accent}$\square$}}

% ------------------------------------------------------------------ captions
\captionsetup{
  font={small,color=ink}, labelfont={bf,color=accent},
  labelsep=period, justification=justified, singlelinecheck=true,
  skip=0.6em, margin=0pt}
\ifecn@mono\else
  \DeclareCaptionFont{ecnlabel}{\sffamily\bfseries\color{accent}}
  \captionsetup{labelfont=ecnlabel}
\fi
\captionsetup[table]{position=top,skip=0.5em}
\captionsetup[figure]{position=bottom}
\setlength{\textfloatsep}{1.6em plus 0.3em minus 0.3em}
\setlength{\intextsep}{1.2em plus 0.3em minus 0.3em}

% ------------------------------------------------------------------ zebra tables
% \begin{zebratabular}{lccc} \toprule \colhead{..} & .. \\ \midrule ... \bottomrule \end{zebratabular}
% \begin{zebratabularx}{\linewidth}{Xccc} ... \end{zebratabularx}
% The first body row is plain, the second striped, and so on.
% Do not use @{} at the outer edges: colortbl paints a stripe over the full
% column including \tabcolsep, so without @{} the stripes and the booktabs
% rules end at the same place. (\arrayrulecolor is global in colortbl, so each
% environment restores it to ink on exit.)
\newcommand{\ecn@zebrasetup}{%
  \rowcolors{3}{zebra}{}%
  \arrayrulecolor{tablerule}%
  \setlength{\aboverulesep}{0pt}\setlength{\belowrulesep}{0pt}%
  \setlength{\extrarowheight}{0pt}%
  \renewcommand{\arraystretch}{1.35}%
  \small}
\newenvironment{zebratabular}[1]
  {\ecn@zebrasetup\begin{tabular}{#1}}
  {\end{tabular}\arrayrulecolor{ink}}
\newenvironment{zebratabularx}[2]
  {\ecn@zebrasetup\tabularx{#1}{#2}}
  {\endtabularx\arrayrulecolor{ink}}
\newcommand{\colhead}[1]{{\ecnheadfont\bfseries\footnotesize #1}}
% source / note line under a table or figure
\newcommand{\tablenote}[1]{\par\vspace{0.45em}{\footnotesize\color{line}\justifying@ecn#1\par}}

% ------------------------------------------------------------------ figures
% \figureplaceholder[width]{height}{text}: a framed stand-in for a missing figure.
\newcommand{\figureplaceholder}[3][\linewidth]{%
  \begin{tikzpicture}
    \useasboundingbox (0,0) rectangle (#1,#2);
    \path[fill=wash, draw=sand, dash pattern=on 3pt off 2pt, line width=0.6pt]
      (0.3pt,0.3pt) rectangle ($(#1,#2)-(0.3pt,0.3pt)$);
    \node[font=\ecnheadfont\footnotesize, text=line, align=center, text width=0.8*#1]
      at ($(0,0)!0.5!(#1,#2)$) {#3};
  \end{tikzpicture}}
% \includefigure[graphicx options]{file.ext}: includes figures/file.ext,
% or draws a placeholder (and warns) while E3 has not produced it yet.
\newcommand{\includefigure}[2][width=\linewidth]{%
  \IfFileExists{figures/#2}%
    {\includegraphics[#1]{#2}}%
    {\ClassWarning{ecnthesis}{figures/#2 not found; drawing a placeholder}%
     \figureplaceholder{0.42\linewidth}{figures/\detokenize{#2}\\(not yet generated)}}}

% TikZ styles shared by both looks (colour names resolve per look)
\tikzset{
  ecn/.style={font=\footnotesize, >=Stealth, every node/.append style={text=ink}},
  % flush center: plain \centering. (TikZ's align=center uses finite glue, which
  % stretches the spaces around math relations in a node with a text width.)
  ecn box/.style={draw=rule, line width=0.45pt, fill=wash, inner sep=5pt, align=flush center},
  ecn mark/.style={draw=accent, line width=0.9pt, fill=wash, inner sep=5pt, align=flush center},
  ecn arrow/.style={->, line width=0.65pt, color=line},
  ecn band/.style={fill=zebra, draw=line, line width=0.3pt},
  ecn label/.style={font=\ecnheadfont\scriptsize, text=line},
}

% ------------------------------------------------------------------ references (natbib + BibTeX)
\renewcommand{\bibfont}{\small}
\setlength{\bibsep}{0.45em plus 0.1em}
\setlength{\bibhang}{1.6em}
\renewcommand{\bibsection}{%
  \section*{\refname}%
  \markright{\refname}%
  \phantomsection\addcontentsline{toc}{section}{\refname}}
\renewcommand{\refname}{References}

% ------------------------------------------------------------------ appendix
% \appendix: starts a new page; sections become "Appendix A", ...; equations,
% figures and tables are numbered A.1, A.2, ...
\newcommand{\ecn@appsectionmark}[1]{\markright{Appendix \thesection\quad #1}}
\g@addto@macro\appendix{%
  \clearpage
  \renewcommand{\ecn@secprefix}{Appendix\ }%
  \let\sectionmark\ecn@appsectionmark
  \ifecn@mono
    \titleformat{\section}[block]
      {\Needspace{7\baselineskip}\normalsize\bfseries\color{ink}}
      {Appendix \thesection}{0.7em}{}
      [\vspace{-0.4em}{\color{rule}\titlerule[0.4pt]}]
  \fi
  \counterwithin{equation}{section}%
  \counterwithin{figure}{section}%
  \counterwithin{table}{section}%
}

\endinput
