#!/usr/bin/env bash
# Create the A2-sprint card chain on board ecn593 (idempotent via keys).
set -euo pipefail
R=/Users/bonorinoa/Desktop/Github_Repositories/ecn593-applied-project
C=$R/docs/cards
S=/Users/bonorinoa/.hermes/cache/scratch/a2cards
mkdir -p "$S"
B=ecn593

body() { # $1 spec file -> body file path
  local out="$S/$(basename "$1")"
  { cat "$1"; printf '\n\n---\n\n'; cat "$C/common_rules.md"; } > "$out"
  echo "$out"
}

mk() { # key title assignee model provider runtime spec [parents...]
  local key=$1 title=$2 who=$3 model=$4 prov=$5 rt=$6 spec=$7; shift 7
  local pargs=()
  for p in "$@"; do pargs+=(--parent "$p"); done
  hermes kanban --board $B create "$title" --assignee "$who" \
    --body-file "$(body "$C/$spec")" --workspace "dir:$R" \
    --model "$model" --provider "$prov" --max-runtime "$rt" \
    --idempotency-key "$B-a2-$key" --json ${pargs[@]+"${pargs[@]}"} \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["id"])'
}

E3=$(mk E3 "A2 E3: three analysts for theta2, run, commit (Codex gpt-5.6-sol)" engineer gpt-5.6-sol openai-codex 4h E3-engineer-a2.md)
echo "E3 $E3"
V3=$(mk V3 "A2 V3: verify A2 code, statistics, results (Grok 4.7)" verifier grok-4.7 xai-oauth 3h V3-grok-a2-code.md "$E3")
echo "V3 $V3"
T1=$(mk T1 "A2 T1: thesis template, Kaffeehaus + mono looks (creative, Claude Opus)" creative claude-opus-5-5 anthropic 3h T1-creative-thesis-template.md)
echo "T1 $T1"
W3=$(mk W3 "A2 W3: full paper in the thesis template (writer, Claude Opus)" writer claude-opus-5-5 anthropic 4h W3-writer-thesis.md "$V3" "$T1")
echo "W3 $W3"
V4=$(mk V4 "A2 V4: verify the paper (Grok 4.7)" verifier grok-4.7 xai-oauth 3h V4-grok-thesis.md "$W3")
echo "V4 $V4"
VS=$(mk VS "A2 VS: video script, storyboard, Phonon narration (creative, Claude Opus)" creative claude-opus-5-5 anthropic 3h VS-creative-video-script.md)
echo "VS $VS"
VV=$(mk VV "A2 VV: verify the video script (Codex gpt-5.6-sol)" verifier gpt-5.6-sol openai-codex 2h VV-codex-video-script.md "$VS")
echo "VV $VV"
VR=$(mk VR "A2 VR: Manim scenes and render (creative, Claude Opus)" creative claude-opus-5-5 anthropic 4h VR-creative-video-render.md "$VV")
echo "VR $VR"
