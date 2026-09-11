#!/usr/bin/env bash
set -e
URL="https://emersonspartz.github.io/dimir-tidebinder-wasp-guide/"
html=$(curl -sf "$URL?v=$(date +%s)")
for n in "Tidebinder and Wasp" "Rules you must know" "Top Tidebinder targets" "Hold or fire" "vs. Mono-Green Landfall" "vs. Dimir Excruciator"; do
  grep -q "$n" <<< "$html" || { echo "FAIL: missing '$n'"; exit 1; }
done
expected=$(python3 -c "import json;print(len(json.load(open('data/result.json'))['result']['entries']))")
mus=$(grep -c '<div class="mu\( open\)\?">' <<< "$html"); bodies=$(grep -c '<div class="mu-body">' <<< "$html")
[ "$mus" = "$expected" ] || { echo "FAIL: expected $expected deck sections, got $mus"; exit 1; }
[ "$mus" = "$bodies" ] || { echo "FAIL: mu/body mismatch $mus vs $bodies"; exit 1; }
if grep -q $'—\|–' <<< "$html"; then echo "FAIL: em/en dash in live page"; exit 1; fi
echo "PASS: $mus deck sections live, structure balanced, no em dashes"
