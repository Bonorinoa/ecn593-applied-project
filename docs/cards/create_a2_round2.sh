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
E4=$(mk E4 "A2 E4: addendum A2.1 variance split, macros (Codex gpt-5.6-sol)" engineer gpt-5.6-sol openai-codex 3h E4-engineer-a21.md)
echo "E4 $E4"
W4=$(mk W4 "A2 W4: paper fix pass (V4 wording, A2.1 macros) (writer, Claude Opus)" writer claude-opus-5-5 anthropic 3h W4-writer-fixpass.md t_3b8a53cd "$E4")
echo "W4 $W4"
V5=$(mk V5 "A2 V5: close the paper and A2.1, fresh-clone REPLICATED (Grok 4.7)" verifier grok-4.7 xai-oauth 4h V5-grok-close.md "$W4")
echo "V5 $V5"
